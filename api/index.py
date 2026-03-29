"""
Vercel Serverless Function Entry Point

This module serves as the entry point for Vercel's Python serverless functions.
It imports the FastAPI application from main.py and exposes it as a handler.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path so that local imports work
# Vercel runs this file from the api/ directory, so we need to go one level up
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set VERCEL env var if not already set (for database path detection)
if not os.environ.get("VERCEL"):
    os.environ["VERCEL"] = "1"

# Import the FastAPI app
from main import app

# Vercel expects an `app` variable for ASGI frameworks (FastAPI/Starlette)
# The variable name "app" is the default handler for @vercel/python
