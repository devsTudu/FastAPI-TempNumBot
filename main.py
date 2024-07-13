from fastapi import FastAPI, status, HTTPException
from helper import api_requests
from helper import SERVERS
from security import Security,get_api_key


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
    if isinstance(resp,str):
        raise  HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resp
        )
    return resp

@app.get("/getPhone")
async def getPhoneFromName(serviceName:str=None,api_key: str = Security(get_api_key)):
    """A private endpoint that requires a valid API key to be provided."""
    return "Working"

@app.get("/")
async def root():
    return {"message": "Hello World"}

