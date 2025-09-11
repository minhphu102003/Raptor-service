import os

from langfuse import Langfuse, get_client, observe

# Initialize Langfuse client
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    debug=os.getenv("LANGFUSE_DEBUG", "False").lower() == "true",
)


# Verify connection (only in development)
def verify_langfuse_connection():
    """Verify Langfuse connection - use only in development, not in production"""
    if os.getenv("ENVIRONMENT", "development") == "development":
        try:
            if langfuse.auth_check():
                print("Langfuse client is authenticated and ready!")
            else:
                print("Authentication failed. Please check your credentials and host.")
        except Exception as e:
            print(f"Error verifying Langfuse connection: {e}")
