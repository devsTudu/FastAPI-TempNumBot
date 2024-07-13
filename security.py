from os import getenv
from dotenv import load_dotenv
from fastapi import status, Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

load_dotenv()

API_KEYS = [
  getenv('TEMPNUM_BOT_TOKEN')
]

api_key_header = APIKeyHeader(name="x-api-key", auto_error=True)

def get_api_key(
    api_key_header: str = Security(api_key_header),
) -> str:
    """Retrieve and validate an API key from the HTTP header.

    Args:
        api_key_header: The API key passed in the HTTP header.

    Returns:
        The validated API key.

    Raises:
        HTTPException: If the API key is invalid or missing.
    """
    if api_key_header in API_KEYS:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )