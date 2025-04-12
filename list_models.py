import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
try:
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        logging.debug(f"Loaded .env file from: {dotenv_path}")
    else:
        logging.debug(".env file not found, relying on environment variables.")
except Exception as e:
     logging.warning(f"Error loading .env file: {e}")

# Configure API Key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key or api_key == "YOUR_API_KEY":
    logging.error("GOOGLE_API_KEY not found or not set in environment variables.")
    exit(1)

try:
    genai.configure(api_key=api_key)
    logging.info("google-generativeai configured successfully.")
except Exception as e:
    logging.error(f"Failed to configure google-generativeai: {e}")
    exit(1)

print("\nAvailable models supporting 'generateContent':")
print("-" * 40)
try:
    for m in genai.list_models():
      if 'generateContent' in m.supported_generation_methods:
        print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")

# Note: The list_models() output might not explicitly state which models
# support the 'generate_images' method used by Imagen 3 via the client library.
# We might need to rely on documentation or trial-and-error if 'imagen-3...' isn't listed clearly.
# However, this confirms connectivity and lists text-generation models.

print("\n" + "-" * 40)
print("Check documentation for specific Imagen model names if not listed above.")
