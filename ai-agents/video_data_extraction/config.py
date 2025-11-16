"""
Configuration module for video data extraction.
Handles environment variables and processing defaults.

Note: All language/vision modeling is now done via the OpenRouter-backed
Gemini client in `evaluation.llm_client`. This module no longer initializes
any OpenAI-specific clients.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenRouter / Gemini configuration (used indirectly by evaluation.llm_client)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "google/gemini-2.0-flash-lite")


# Processing Configuration
DEFAULT_SEGMENT_DURATION = 30.0  # seconds
DEFAULT_FRAMES_PER_SEGMENT = 20
DEFAULT_AUDIO_CHUNK_DURATION = 60.0  # seconds

