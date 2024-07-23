from fastapi import FastAPI, status, HTTPException
from models import phoneDetails
from helper import api_requests
from helper import SERVERS
from security import Security, get_api_key

app = FastAPI()


@app.get("/")
def public():
    """A welcome message"""
    return "Welcome to the server of Telegram Bot Temp Num Bot"


@app.get("/checkBal")
async def checkbal(server_name: SERVERS, api_key: str = Security(get_api_key)):
    """Check the current balance of all your servers"""
    resp = await api_requests().getBalance(serverName=server_name)
    return resp


@app.get("/getPrices")
async def getpricesfromname(servicename: str = None,
                            api_key: str = Security(get_api_key)):
    """Gives you a list of prices from different servers"""
    resp = await api_requests().getPricesFromName(serviceName=servicename)

    if isinstance(resp, str):
        raise HTTPException(

            status_code=status.HTTP_404_NOT_FOUND,
            detail=resp
        )
    return resp


@app.get("/getPhone")
async def get_phone_from_name(server: SERVERS,
                              service_name: str = None,
                              provider: str = 'Any',
                              user: str = "123456789",
                              api_key: str = Security(get_api_key)):
    """Buy you a phone number given these details, 
    if failed will return Error Statement"""

    resp = await api_requests().getPhoneFromName(server, service_name, provider, user)

    if isinstance(resp, str):
        raise HTTPException(

            status_code=status.HTTP_404_NOT_FOUND,
            detail=resp
        )
    return resp


@app.get('/updates')
async def get_updates(server: SERVERS, access_id: str,
                      phone=987654321,
                      api_key: str = Security(get_api_key)):
    """Get the otp update for a given phone number details"""

    resp = await api_requests().getStatus(serverName=server,
                                          access_id=access_id,
                                          phone=phone)

    if not isinstance(resp, phoneDetails):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resp)
    return resp


@app.get("/cancelPhone")
async def cancel_phone(server: SERVERS, access_id: str,
                       api_key: str = Security(get_api_key)):
    """Cancel the otp update for a given phone number details,

    Returns True if Sucessfully Canceled Phone Number"""

    resp = await api_requests().cancelPhone(serverName=server,
                                            access_id=access_id)
    return resp
