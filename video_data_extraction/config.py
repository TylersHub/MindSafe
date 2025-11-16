"""
Configuration module for video data extraction.
Handles environment variables and API client initialization.
"""

import os
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")
TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. Set it as an environment variable "
        "or add it to the .env file."
    )

# Initialize OpenAI client (compatible with both old and new API versions)
try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    OPENAI_V1 = True
except ImportError:
    # Old API (openai < 1.0.0)
    openai.api_key = OPENAI_API_KEY
    client = None
    OPENAI_V1 = False


# Processing Configuration
DEFAULT_SEGMENT_DURATION = 30.0  # seconds
DEFAULT_FRAMES_PER_SEGMENT = 20
DEFAULT_AUDIO_CHUNK_DURATION = 60.0  # seconds

