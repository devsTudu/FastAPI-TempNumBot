from fastapi import FastAPI, status, Security, HTTPException
from fastapi.security.api_key import APIKeyQuery, APIKeyHeader
from os import getenv
from helper import api_requests
from helper import SERVERS
from dotenv import load_dotenv

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

app = FastAPI()

@app.get("/public")
def public():
    """A public endpoint that does not require any authentication."""
    return "This is a simple public request"

@app.get("/checkBal")
async def checkBal(serverName:SERVERS,api_key: str = Security(get_api_key)):
    """A private endpoint that requires a valid API key to be provided."""
    resp = await api_requests().getBalance(serverName=serverName)
    return resp

@app.get("/getPrices")
async def getPricesFromName(serviceName:str=None,api_key: str = Security(get_api_key)):
    """A private endpoint that requires a valid API key to be provided."""
    resp = await api_requests().getPricesFromName(serviceName=serviceName)
    return resp


