from helper import (bowerSMS,tigerSMS,fastSMS,FiveSim)
from helper import tools,show
from helper import countryInfo,serviceInfo,serviceDetails,phoneDetails
import asyncio
import time
import pytest






# Tests Functions Declared
def test_countryFromID():
    x = asyncio.run(tools.getCountryNameFromCode('22'))
    assert x == 'india'

def test_serviceFromID():
    x = asyncio.run(tools.getServiceNameFromCode('tg'))
    assert x == 'Telegram'

test_data = [
    (fastSMS,'Instagram'),
    (tigerSMS,'1688'),
    (bowerSMS,'1688'),
    (FiveSim,'99app'),
    (tigerSMS,'99acres'),
    (bowerSMS,'99acres'),
    (FiveSim,'99acres'),
]

@pytest.mark.parametrize("server_arg, serviceName", test_data)
def test_server(server_arg:classmethod, serviceName):
    server = server_arg()
    bal = asyncio.run(server.getBalance())
    assert isinstance(bal,float)
    service = tools.getServiceInfo(serviceName=serviceName,country=countryInfo())
    serviceDet =asyncio.run(server.getServiceDetails(service=service))
    assert isinstance(serviceDet,serviceDetails)
    phone = asyncio.run(server.getPhoneNumber(serviceDet=serviceDet,user='9348692623'))
    assert isinstance(phone,phoneDetails)
    assert phone.status == "Waiting"
    time.sleep(10)
    assert asyncio.run(server.cancelService(phoneDet=phone)) == True



if __name__ == "__main__":
    #manualTest()
    test_server(bowerSMS,'99acres')