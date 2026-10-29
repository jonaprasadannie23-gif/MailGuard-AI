"""
Vercel Serverless Function entry point for ProbMail.
Delegates incoming HTTP requests to the unified Flask application instance.
"""
import os
import sys
from pathlib import Path

# Add project root and backend directory to Python sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"

for path_to_add in (str(backend_dir), str(root_dir)):
    if path_to_add not in sys.path:
        sys.path.insert(0, path_to_add)

os.environ.setdefault("FLASK_ENV", "production")

from backend.app import app

# Standard Vercel Serverless Function WSGI export
handler = app

