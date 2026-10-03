"""
config.py
---------
Loads all application configuration from environment variables.
All sensitive values must be set in a .env file (see .env.example).
"""

import os
import sys
from dotenv import load_dotenv

# Load .env file from the project root
load_dotenv()


def _require(key: str) -> str:
    """Return the value of an environment variable, exiting if it is missing."""
    value = os.getenv(key)
    if not value:
        print(f"[ERROR] Required environment variable '{key}' is not set.")
        print("        Copy .env.example to .env and fill in the values.")
        sys.exit(1)
    return value


# ── Gemini AI ──────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = _require("GEMINI_API_KEY")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# ── Flask ──────────────────────────────────────────────────────────────────
FLASK_SECRET_KEY: str = _require("FLASK_SECRET_KEY")
# NOTE: FLASK_ENV was removed in Flask 3.x. Use FLASK_DEBUG to control debug mode.
FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "True").lower() == "true"

# ── Server ─────────────────────────────────────────────────────────────────
PORT: int = int(os.getenv("PORT", "5000"))
