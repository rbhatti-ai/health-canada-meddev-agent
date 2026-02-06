"""
Vercel serverless function entry point.
Exports the FastAPI app for Vercel's Python runtime.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the FastAPI app
from src.api.main import app

# Vercel expects the app to be named 'app' or 'handler'
# FastAPI apps work directly with Vercel's Python runtime
