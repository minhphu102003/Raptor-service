import os
from typing import Optional

from dotenv import load_dotenv
import google.genai as genai

load_dotenv()


def make_client(api_key: Optional[str] = None) -> genai.Client:
    key = api_key or os.getenv("GEMINI_API_KEY")
    return genai.Client(api_key=key)
