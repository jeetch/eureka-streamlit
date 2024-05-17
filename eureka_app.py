import streamlit as st
import replicate
from dotenv import load_dotenv
import os
import json
import toml

# Load environment variables from .env file
load_dotenv()

# Get the Replicate API token from environment variables
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

if not REPLICATE_API_TOKEN:
    st.error("REPLICATE_API_TOKEN is not set in the environment variables.")
else:
    # Set the Replicate API token in the environment
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

    # Streamlit input field for user's prompt
    user_prompt = st.text_area("Enter your prompt", key="user_prompt")

    # Add buttons
    col1, col2 = st.columns(2)
    with col1:
        generate_button = st.button("Generate Response")
    with col2:
        lucky_button = st.button("I'm Feeling Lucky")

    # Check which button was pressed
    if generate_button:
        prompt_to_use = user_prompt
    elif lucky_button:
        prompt_to_use = "random AI app idea"
        st.text_area("Lucky Prompt", value=prompt_to_use, key="lucky_prompt", disabled=True)
    else:
        prompt_to_use = None

    if prompt_to_use:
        # Display the prompt to be used
        st.write(f'Prompt: {prompt_to_use}')

        # Prepare the prompt template for JSON output
        prompt_template = f"""system
You're a helpful assistant. I will give you an idea, and I want you to generate the name of the app, emojis, subtitle, description, color palette, and a basic business plan around it.
The output should be in JSON format:
    "Name": "<App Name with emoji>",
    "Tagline": "<Tagline>",
    "Description": "<description>",
    "Primary_Color": "<Primary color>"
user
{prompt_to_use}
assistant
"""

        # Stream the output from the replicate model
        with st.spinner('Generating response...'):
            response_text = ""
            event_texts = []
            for event in replicate.stream(
                "snowflake/snowflake-arctic-instruct",
                input={
                    "top_p": 0.9,
                    "prompt": prompt_to_use,
                    "temperature": 0.2,
                    "max_new_tokens": 512,
                    "min_new_tokens": 0,
                    "prompt_template": prompt_template,
                    "presence_penalty": 1.15,
                    "frequency_penalty": 0.2
                },
            ):
                event_texts.append(str(event))
            
            # Join the event texts into a single response text
            response_text = ''.join(event_texts)

            try:
                # Parse the response text to extract JSON data
                json_data = json.loads(response_text)

                # Extract the primary color
                primary_color = json_data.get("Primary_Color", "#FFFFFF")  # Default to white if not found

                # Update the config.toml file
                config_path = ".streamlit/config.toml"
                with open(config_path, "r") as config_file:
                    config_data = toml.load(config_file)
                
                config_data["theme"]["primaryColor"] = primary_color
                config_data["theme"]["backgroundColor"] = primary_color

                with open(config_path, "w") as config_file:
                    toml.dump(config_data, config_file)

                st.success(f'Primary color updated to: {primary_color}')

                # Display the JSON output
                st.write(json_data) 

            except json.JSONDecodeError:
                st.error("Failed to parse the JSON response. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
