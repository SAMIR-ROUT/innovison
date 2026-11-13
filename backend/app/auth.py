import os
import secrets
from pathlib import Path
from dotenv import load_dotenv
from fastapi import Header, HTTPException, status

# Load .env file from the backend directory
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """Dependency that checks for a valid X-API-Key header on write endpoints."""
    expected_api_key = os.getenv("API_KEY")
    if not expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server authentication configuration error: API_KEY is missing from environment",
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, expected_api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
    return x_api_key
