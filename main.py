"""
Entry-point shim so that the command
    uvicorn main:app --reload
works whether you are inside the backend package or at the repository root.
"""

from backend.main import app   # re-export the FastAPI instance
