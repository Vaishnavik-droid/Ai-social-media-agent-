"""
Vercel Serverless Function Entry Point for OmniPulse FastAPI Backend.
Exposes the FastAPI ASGI application instance as `app` for Vercel's Python runtime.
"""
import os
import sys

# Ensure backend and current directory are on the Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.join(PARENT_DIR, "backend")

for directory in [BACKEND_DIR, PARENT_DIR, CURRENT_DIR]:
    if os.path.exists(directory) and directory not in sys.path:
        sys.path.insert(0, directory)

# Import the FastAPI ASGI app instance
try:
    from app.main import app
except ImportError:
    from backend.app.main import app

# Entrypoint exported for Vercel
__all__ = ["app"]
