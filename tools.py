from json import JSONDecodeError
import json
from os import getenv
from pprint import pprint
from typing import Union

from pydantic import BaseModel
from requests import get
from models import (serviceInfo,countryInfo,Error)
from dotenv import load_dotenv

load_dotenv()


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


def show(object:BaseModel):
   if isinstance(object,BaseModel):
      pprint(object.model_dump())
   elif isinstance(object,list):
    for i in object:
        show(i)
   else:
      pprint(object)
   return object



# Common Functions for Requesting Data from API
class commonTools:
    def __init__(self) -> None:
        menuPath = "menuList.json"
        with open(menuPath, 'r') as file:
            data = json.load(file)
        self.serviceMenu = data
    
    def getKeys(self,serviceName:str):
        if serviceName in self.serviceMenu:
            return self.serviceMenu[serviceName]
        else:
            return None
    
    def getServiceInfo(self,serviceName:str,country:countryInfo)->serviceInfo:
        keys = self.getKeys(serviceName)
        if keys:
            serviceinfo = serviceInfo(name=serviceName,country=country,**keys)
            return serviceinfo

    def isError(self, object) -> bool:
        if isinstance(object, str):
            return object.startswith('Error')
        elif isinstance(object,dict):
            return object.keys() == {'Error'}
        elif isinstance(object,Error):
            return True
        else:
           return False


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
                if resp.json()=={}:
                    return {"Error":"Empty JSON response"}
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
        data_country = await self.getJson(url, params=param)
        if not self.isError(data_country):
            return data_country[str(code)]
        else:
            return None

    async def getServiceNameFromCode(self, code: str) -> Union[str ,None]:
        """Returns the Service Name name from the code, or None if
        no Service name was found"""
        url = BASE_URL["fast"]
        param = {"api_key": TOKENS['fast'], "action": "getServices"}
        data = await self.getJson(url, params=param)
        if not self.isError(data):
            return data[str(code)]
        else:
            return None

