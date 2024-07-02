import asyncio
from os import getenv
import pprint
import re
from requests import JSONDecodeError, get
from pydantic import BaseModel, Field, PositiveFloat, PositiveInt
from typing import  Optional, Literal, Union


# Variable Declaration
BASE_URL = {
    "fast": "https://fastsms.su/stubs/handler_api.php",
    "bower": "https://smsbower.com/stubs/handler_api.php",
    "tiger": "https://api.tiger-sms.com/stubs/handler_api.php?",
}


TOKENS = {
    'fast': getenv('FASTSMS_API'),
    'bower': getenv('BOWER_API'),
  'tiger': getenv('TIGER_API'),
  '5Sim': getenv('FIVESIM_API')
}

SERVERS = Literal['Fast', 'Tiger', '5Sim', 'Bower']

# Data Model Declaration

class countryInfo(BaseModel):
    name: str = 'India'
    code: str = "22"


class serviceInfo(BaseModel):
    name: str
    fastCode: str  = None
    tigerCode: str  = None
    bowerCode: str  = None
    fiveCode: str  = None
    country: countryInfo


class serviceDetails(BaseModel):
    server: SERVERS
    serviceInfo: serviceInfo
    provider: Optional[str]='Any'  # Will be used in 5Sim
    count: PositiveInt
    cost: PositiveFloat

class phoneDetails(BaseModel):
    serviceDetail: Optional[serviceDetails] = None
    phone: str = Field(..., pattern=r'^\+?1?\d{9,15}$')
    access_id: str
    otp: Optional[str] = None
    status: Literal['Invalid','Waiting','Expired','Success'] = 'Waiting'
    user: str = '123456789'

    @classmethod
    def validate_phone(cls, v):
        if not re.match(r'^\+?1?\d{9,15}$', v):
            raise ValueError('Invalid phone number format')
        return v

def show(object:BaseModel):
   if isinstance(object,BaseModel):
      pprint.pprint(object.model_dump())
   else:
      pprint.pprint(object)

# Common Functions for Requesting Data from API
class commonTools:
    def __init__(self) -> None:

        pass

    def isError(self, object:Union[str,dict]) -> bool:
        if isinstance(object, str):
            return object.startswith('Error')
        elif isinstance(object,dict):
            return object.keys() == {'Error'}
        else:
           return True


    async def getText(self, url, params=None, headers=None) -> str:
        """
        Returns the text of the response from the request if successfull,
        Otherwise Error(code)(response)
        """
        resp = get(url, params=params, headers=headers)
        if resp.status_code == 200:
            return resp.text
        else:
            return "Error"+str(resp.status_code)+resp.text

    async def getJson(self, url, params=None, headers=None, responsePrint=False) -> dict:
        """
        Return Json Object if sucessful, else a {'Error':response.Text}
        """
        resp = get(url, params=params, headers=headers)

        if resp.status_code == 200:
            if responsePrint:
                print(resp.content)
            try:
                return resp.json()
            except JSONDecodeError as j:
                return {'Error': resp.text}
        else:
            return {"Error": resp.text}

    async def getCountryNameFromCode(self, code: str) -> Union[str ,None]:
        """Returns the country name from the code, or None if
        no country name was found"""
        if code == '22':
            return 'india'
        url = BASE_URL["fast"]
        param = {"api_key": TOKENS['fast'], "action": "getCountries"}
        data_country = await tools.getJson(url, params=param)
        if not self.isError(data_country):
            return data_country[str(code)]
        else:
            return None

    async def getServiceNameFromCode(self, code: str) -> Union[str ,None]:
        """Returns the Service Name name from the code, or None if
        no Service name was found"""
        url = BASE_URL["fast"]
        param = {"api_key": TOKENS['fast'], "action": "getServices"}
        data = await tools.getJson(url, params=param)
        if not self.isError(data):
            return data[str(code)]
        else:
            return None


tools = commonTools()


class fastSMS:
  def __init__(self, countryID: int = 22) -> None:
    self.url = BASE_URL['fast']
    self.main_params = {"api_key": TOKENS["fast"], "country": countryID}

  
  async def getPhonenumber(self,service:serviceDetails,user:str)->Union[phoneDetails,dict]:
    params = self.main_params
    params['service'] = service.serviceInfo.fastCode
    params['action'] = "getNumber"
    params['country'] = service.serviceInfo.country.code
    response = await tools.getText(self.url,params=params)
    if not tools.isError(response):
       _,access,phone = response.split(":")
       return phoneDetails(serviceDetail=service,phone=phone,access_id=access,user=user,status='Waiting',)
    else:
       return response
  
  async def getServiceDetails(self,service:serviceInfo)->Union[serviceDetails,dict]:
      countryCode = service.country.code
      serviceCode = service.fastCode

      params = self.main_params
      params['action'] = "getPrices"
      params['service']= serviceCode
      params["country"] = countryCode
      response = await tools.getJson(BASE_URL['fast'], params=params)
      try:
          
          price = list(response[countryCode][serviceCode].keys())[0]
          count = list(response[countryCode][serviceCode].values())[0]
          return serviceDetails(server='Fast',serviceInfo=service,count=count,cost=price)
      except KeyError as k:
          return {"Error":k}

  async def getStatus(self,phoneDet:phoneDetails)->phoneDetails:
    """STATUS_WAIT_CODE - Waiting for SMS
STATUS_CANCEL - Activation canceled
STATUS_OK:CODE - Code received (where CODE - activation code)"""
    params = self.main_params
    params['id'] = phoneDet.access_id
    params['action'] = "getStatus"
    response =await tools.getText(self.url,params=params)
    if not tools.isError(response):
        if "WAIT" in response:
          phoneDet.status = 'Waiting'
        elif "CANCEL" in response:
          phoneDet.status = 'Cancelled'
        elif "OK" in response:
          phoneDet.status = "Success"
          phoneDet.otp = response.split(":")[-1]
        return phoneDet

  async def getMultipleStatus(self,arrOfAcessID:list):
    arrOfAcessID = list(map(str,arrOfAcessID))
    params = self.main_params
    params['id'] = str(arrOfAcessID).replace("'",'"')
    params['action'] = "getStatus_2"
    response = requests.get(self.url,params=params)
    if response.status_code == 200:
      return response.json()
    else:
      return response.content

  async def changeStatus(self,phoneDet:phoneDetails,code:int=8):
    """Change the status of the given access ID,
    activation status code (8 - cancel activation, 3 - Request another SMS)

    Returns 
      ACCESS_CANCEL_ALREADY
      TIMED OUT
      ACCESS_CANCEL

    """
    if code not in [3,8]:
      return "Wrong Status Code"
    params = self.main_params
    params['id'] = phoneDet.access_id
    params['status'] = code
    params['action'] = 'setStatus'


    return await tools.getText(self.url,params=params)

  async def cancelService(self,access_id:str=None,phoneDet:phoneDetails=None)->bool:
     """Returns True if sucessfully canceled and money refunded,
                False Failed to canceled, either Timeout, Expired or invalid"""
     if access_id is not None:
        phone = phoneDetails(access_id=access_id,phone='123456789')
     else:
        phone = phoneDet
     resp = await self.changeStatus(phoneDet=phone,code=8)
     return resp == 'ACCESS_CANCEL'

  async def getBalance(self):
    self.main_params['action'] = "getBalance"
    resp = await tools.getText(self.url, params=self.main_params)
    try:
      bal = float(resp.split(":")[-1])
    except ValueError as v:
      return v
    return bal
    

  async def test_getNo(self):
     service = serviceInfo(name='Probo',fastCode='aa',country=countryInfo(),)
     serviceDet = await self.getServiceDetails(service)
     phone = await self.getPhonenumber(service= serviceDet,user='1234567')
     show(phone)
     return phone
  async def test_serviceDetails(self):
     req = serviceInfo(name='Probo',fastCode='aa',country=countryInfo())
     service =await self.getServiceDetails(req)
     show(phone)
  async def test_getStatus(self):
     x = await self.getStatus(phoneDetails(phone='7798564311',access_id="171991856255350",user=''))
     show(x)
  async def test_cancel_phone(self):
     return await self.cancelService("171992269389667")




if __name__ == '__main__':
    fs = fastSMS()
    y = asyncio.run(fs.test_cancel_phone())
    show(y)



# Tests Functions Declared
def test_countryFromID():
    x = asyncio.run(tools.getCountryNameFromCode('22'))
    assert x == 'india'

def test_serviceFromID():
    x = asyncio.run(tools.getServiceNameFromCode('tg'))
    assert x == 'Telegram'
