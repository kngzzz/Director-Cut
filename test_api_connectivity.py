import os
import dotenv
from google.cloud import aiplatform
from google.api_core import exceptions

# Load environment variables from .env file
dotenv.load_dotenv()

# Get Vertex AI configuration
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("GOOGLE_CLOUD_LOCATION")

if not project_id or not location:
    print("Error: GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION must be set in the .env file.")
    exit(1)

print(f"Using Project ID: {project_id}")
print(f"Using Location: {location}")

# Initialize Vertex AI client (uses Application Default Credentials)
try:
    aiplatform.init(project=project_id, location=location)
    print("Vertex AI client initialized successfully.")
except Exception as e:
    print(f"Error initializing Vertex AI client: {e}")
    exit(1)

# --- List Available Vertex AI Models in Region ---
print(f"\n--- Listing Available Vertex AI Models in {location} ---")
model_count = 0
try:
    # Attempt to list models available in the region for this project
    models = aiplatform.Model.list()
    print(f"Found the following models available in {location} for project {project_id}:")
    print("-" * 60)
    for model in models:
        print(f"Display Name: {model.display_name}")
        print(f"Resource Name: {model.name}")
        print("-" * 60)
        model_count += 1

    if model_count == 0:
        print("No models found. This might indicate no custom models are deployed")
        print("and potentially limited access to publisher models in this region.")
    else:
        print(f"Total models listed: {model_count}")
    print("\nCheck the list for Imagen or Veo related models.")
    print("Note: Publisher models might have specific naming conventions (e.g., projects/google/...).")

except exceptions.PermissionDenied as e:
    print(f"Permission Denied listing models in {location}: {e}")
    print("Check your account permissions and ensure the Vertex AI API is enabled for this project.")
except exceptions.ClientError as e:
    # Catch potential errors related to region support for the list operation itself
    if "unsupported region" in str(e).lower():
        print(f"Error: The list models operation is not supported in the configured region '{location}'.")
    else:
        print(f"A client error occurred listing models in {location}: {e}")
except Exception as e:
    print(f"An unexpected error occurred listing models in {location}: {e}")

print("\nModel listing finished.")
