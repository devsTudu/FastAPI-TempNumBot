from json import JSONDecodeError
import requests
from os import error, getenv
from cookHelper import hashMap,servicesMenu
import asyncio
import pytest
from pydantic import BaseModel, constr, PositiveInt
from typing import Optional, Literal



#Variable Declaration
BASE_URL = {
    "fast": "https://fastsms.su/stubs/handler_api.php",
    "bower": "https://smsbower.com/stubs/handler_api.php",
    "tiger": "https://api.tiger-sms.com/stubs/handler_api.php?",
}


TOKENS = {
  'fast':getenv('FASTSMS_API'),
  'bower':getenv('BOWER_API'),
  'tiger':getenv('TIGER_API'),
  '5Sim':getenv('FIVESIM_API')
}

SERVERS = Literal['Fast','Tiger','5Sim','Bower']

#Data Model Declaration
class phoneDetails(BaseModel):
   phone: constr(regex=r"^(?:\+91|0)?\d{10}$") # type: ignore
   access_id: str
   otp:Optional[int]=None
   user_id: str

class countryInfo(BaseModel):
   name: str = 'India'
   code: int = 22

class serviceInfo(BaseModel):
   name: str
   code: str #Hexadecimal Code for service

class serviceDetails(BaseModel):
   server: SERVERS
   country: countryInfo
   service: serviceInfo
   accessCode: str
   provider: Optional[str]  # Will be used in 5Sim
   count: PositiveInt
   cost: PositiveInt







#Common Functions for  Requesting Data from API
class commonTools:
    def __init__(self) -> None:

        pass

    async def getText(self, url, params=None, headers=None)->str:
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code == 200:
            return resp.text
        else:
            return "Error"+str(resp.status_code)

    async def getJson(self, url, params=None, headers=None,responsePrint=False)->dict:
        """
        Return Json Object if sucessful, else a {'Error':response.Text}
        """
        resp = requests.get(url, params=params, headers=headers)
        
        if resp.status_code == 200:
          if responsePrint:
            print(resp.content)
          try: 
            return resp.json()
          except JSONDecodeError as j:
            return {'Error':resp.text}
        else:
            return {"Error":resp.text}

    async def getCountryNameFromCode(self, code: str):
        if code == '22': return 'India'
        url = BASE_URL["fast"]
        param = {"api_key": TOKENS['fast'], "action": "getCountries"}
        data_country = await tools.getJson(url, params=param)
        return data_country[str(code)]

    async def getServiceNameFromCode(self, code: str):
        url = BASE_URL["fast"]
        param = {"api_key": TOKENS['fast'], "action": "getServices"}
        data = await tools.getJson(url, params=param)
        return data[str(code)]

tools = commonTools()

class fastSMS:
  def __init__(self, countryID: int = 22) -> None:
    self.url = BASE_URL['fast']
    self.main_params = {"api_key": TOKENS["fast"], "country": countryID}

  
  async def getPhoneNumber(self,serviceCode:str,countryID:int=22)->tuple[int,int] | None:
    params = self.main_params
    params['service'] = serviceCode
    params['action'] = "getNumber"
    params['country'] = countryID
    response = requests.get(self.url,params)
    if response.status_code == 200:
      try :
        _,access,phone = response.text.split(":")
        return access,phone
      except ValueError:
        return response.text
    else:
      print("Failed getting phone number")
      return None

  async def getPrice(self,serviceCode:str,countryID:str="22")->dict:
      params = self.main_params
      params['action'] = "getPrices"
      params['service']= serviceCode
      params["country"] = countryID
      response = await tools.getJson(BASE_URL['fast'], params=params)
      try:
          price = list(response[countryID][serviceCode].keys())[0]
          count = list(response[countryID][serviceCode].values())[0]
          return {
              'cost':float(price),
              'count':int(count)}
      except KeyError as k:
          return {"Error":k}

  async def getStatus(self,acceesID:str):
    params = self.main_params
    params['id'] = acceesID
    params['action'] = "getStatus"
    response = requests.get(self.url,params=params)
    if response.status_code == 200:
      return response.text
    return response.content

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

  async def changeStatus(self,accessID:str,code:int):
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
    params['id'] = accessID
    params['status'] = code
    params['action'] = 'setStatus'


    response = requests.get(self.url,params=params)
    return response.text

  async def getBalance(self):
    self.main_params['action'] = "getBalance"
    resp = await tools.getText(self.url, params=self.main_params)
    try:
      bal = float(resp.split(":")[-1])
    except ValueError as v:
      return v
    return bal
    
  
  async def test(self,code):
    print("Fast Test")
    resp = self.getPhoneNumber(code)
    try:
      access,phone = resp
      print(access,phone)
      print(self.getStatus(access))
      print(self.changeStatus(access, 8))
      print(self.getStatus(access))

    except ValueError:
      print(resp)
    
    resp = self.getMultipleStatus(["171949019199603", 171955584892590])
    print(resp)
    
class tigerSMS:

  def __init__(self) -> None:
    self.url = "https://api.tiger-sms.com/stubs/handler_api.php"
    self.params = {"api_key": TOKENS['tiger']}

  async def getBalance(self):
    params = self.params
    params['action']='getBalance'
    resp = await tools.getText(self.url, params=params)
    try:
      bal = float(resp.split(":")[-1])
      return bal
    except ValueError as v:
      return v
      
  async def getPrice(self,serviceCode,countryCode="22")->dict:
      base_url = "https://api.tiger-sms.com/stubs/handler_api.php"
      
      params = self.params
      params['action'] = "getPrices"
      params['service'] = serviceCode
      params['country'] = countryCode
      response = await tools.getJson(base_url, params=params)
      try:
        return response[countryCode][serviceCode]
      except KeyError:
        return {"Error":response}
      except TypeError as t:
        return {'Error':str(t)}

  async def getPhoneNumber(self, serviceCode: str, countryID: str = "22"):
    params = self.params
    params['service'] = serviceCode
    params['action'] = "getNumber"
    params['country'] = countryID
    params['ref'] = 'Nothing'
    response = requests.get(self.url, params)
    if response.status_code == 200:
      try:
        _, access, phone = response.text.split(":")
        return access, phone
      except ValueError:
        return response.text
    else:
      print("Failed getting phone number")
      return None

  async def getStatus(self, acceesID: str):
    """
    Possible Answers
    ANSWER:
STATUS_WAIT_CODE - Waiting for SMS

STATUS_WAIT_RESEND - waiting for next SMS

STATUS_CANCEL - activation canceled

STATUS_OK: 'activation code' - code received

POSSIBLE MISTAKES:
BAD_KEY - invalid API key

BAD_ACTION - incorrect action

NO_ACTIVATION - incorrect activation id
    """
    params = self.params
    params['id'] = acceesID
    params['action'] = "getStatus"
    response = requests.get(self.url, params=params)
    if response.status_code == 200:
      return response.text
    return response.content

  def getMultipleStatus(self, arrOfAcessID: list):
    arrOfAcessID = list(map(str, arrOfAcessID))
    params = self.params
    params['id'] = str(arrOfAcessID).replace("'", '"')
    params['action'] = "getStatus_2"
    response = requests.get(self.url, params=params)
    if response.status_code == 200:
      return response.json()
    else:
      return response.content

  async def changeStatus(self, accessID: str, code: int):
    """
    Change the status of the given access ID,
    1 - inform about the readiness of the number (SMS sent to the number)
    3 - request another code (free)
    6 - complete activation *
    8 - inform that the number has been used and cancel the activation
    """
    """
    * if there was a status 'code received' - marks it successfully and completes, if there was a 'preparation' - deletes and marks an error, if there was a status 'awaiting retry' - transfers activation to SMS pending

** It is not possible to change the activation status for which the verification method by call was selected if the number has already arrived

    ANSWER:
    ACCESS_READY - phone is ready for getting SMS
    ACCESS_RETRY_GET - waiting for a new SMS
    ACCESS_ACTIVATION - the service has been successfully activated
    ACCESS_CANCEL - activation canceled

    POSSIBLE MISTAKES:
    NO_ACTIVATION - incorrect activation id
    BAD_SERVICE - incorrect service name
    BAD_STATUS - incorrect status
    BAD_KEY - invalid API key
    BAD_ACTION - incorrect action
    """

    if code not in [1,3,6,8]:
      return "Wrong Status Code"
    params = self.params
    params['id'] = accessID
    params['status'] = str(code)
    params['action'] = 'setStatus'

    response = requests.get(self.url, params=params)
    return response.text

  def test(self,code):
    print("Tiger Test")
    resp = self.getPhoneNumber(code)
    try:
      access,phone = resp
      print(access,phone)
      print(self.getStatus(access))
      print(self.changeStatus(access, 8))
      print(self.getStatus(access))
    except ValueError:
      print(resp)
  
class bowerSMS:
  def __init__(self):
    self.url = "https://smsbower.com/stubs/handler_api.php"
    self.params = {"api_key": TOKENS['bower']}

  async def getBalance(self):
    params = self.params
    params["action"] = "getBalance"
    resp = await tools.getText(self.url, params=params)
    try:
      bal = float(resp.split(":")[-1])
      return bal
    except ValueError as v:
      return v

  async def getPrice(self,serviceCode,countryCode:str='22')->dict:
      params = self.params
      params['action'] = "getPrices"
      params['service'] = serviceCode
      params['country'] = countryCode
      response = await tools.getJson(self.url, params=params)
      try:
        return response[countryCode][serviceCode]
      except KeyError as k:
          return {"error":response}
    
  async def getPhoneNumber(self,
                     serviceCode: str,
                     countryID: int = 22,
                     maxPrice: int = 100):
    params = self.params
    params['service'] = serviceCode
    params['action'] = "getNumber"
    params['country'] = '22'
    params['maxPrice'] = maxPrice
    params['phoneException'] = 987654321
    params['ref'] = 'none'
    response = requests.get(self.url, params)
    if response.status_code == 200:
      try:
        _, access, phone = response.text.split(":")
        return access, phone
      except ValueError:
        return response.text
    else:
      print("Error Requesting")
      return None

  async def getStatus(self, acceesID: str):
    """
      Answer
      STATUS_WAIT_CODE - Waiting for SMS
      STATUS_WAIT_RESEND - Waiting for next sms
      STATUS_CANCEL - Activation canceled
      STATUS_OK: 'activation code' - code received
      Possible mistakes
      BAD_KEY - invalid API key
      BAD_ACTION - incorrect action
      NO_ACTIVATION - incorrect activation id
      """
    params = self.params
    params['id'] = acceesID
    params['action'] = "getStatus"
    response = requests.get(self.url, params=params)
    if response.status_code == 200:
      return response.text
    return response.content

  async def changeStatus(self, accessID: str, code: int):
    """Change the status of the given access ID,
      activation status code 
      1 - inform about the readiness of the number (SMS sent to the number)
      3 - request another code (free)
      6 - complete activation *
      8 - inform that the number has been used and cancel the activation

      Returns 
      ANSWER
      ACCESS_READY - phone is ready for getting SMS
      ACCESS_RETRY_GET - waiting for a new SMS
      ACCESS_ACTIVATION - the service has been successfully activated
      ACCESS_CANCEL - activation canceled
      Possible mistakes
      NO_ACTIVATION - incorrect activation id
      BAD_SERVICE - incorrect service name
      BAD_STATUS - incorrect status
      BAD_KEY - invalid API key
      BAD_ACTION - incorrect action
      EARLY_CANCEL_DENIED - It is possible to cancel the number after 2 minutes following the purchase

      """
    if code not in [1, 3, 6, 8]:
      return "Wrong Status Code"
    params = self.params
    params['id'] = accessID
    params['status'] = str(code)
    params['action'] = "setSatus"

    resp =await tools.getText(self.url, params=params)
    return resp
    
    

  async def getPhoneV2(self, serviceCode: str, maxPrice: int = 100):
    params = self.params
    params['service'] = serviceCode
    params['action'] = "getNumberV2"
    params['country'] = '22'
    params['maxPrice'] = str(maxPrice)

    response = await tools.getJson(self.url, params=params)
    return response

  def test(self, code):
    print("Bower Test")
    resp = self.getPhoneNumber(code)
    try:
      access,phone = resp
      print(access,phone)
      print(self.getStatus(access))
      print(self.changeStatus(access,8))
      print(self.getStatus(access))
    except ValueError:
      print(resp)

class FiveSim:
  def __init__(self):
      self.token = TOKENS["5Sim"]
      self.headers = {
          'Authorization': 'Bearer '+ self.token,
          'Accept': 'application/json',
      }

      self.country = 'india'

  
  async def getBalance(self):
    url = 'https://5sim.net/v1/user/profile'
    response = await tools.getJson(url,
       headers=self.headers)
    try:
      bal = float(response['balance'])
      return bal
    except ValueError as v:
      return v

  async def getPrice(self,serviceCode,countryCode:str='india')->dict:

      params = (('product', serviceCode), )

      response = requests.get('https://5sim.net/v1/guest/prices',
                              headers=self.headers,
                              params=params)
      try:
          respond = response.json()[serviceCode][countryCode]
          return respond
      except error as e:
          return {str(e):response.text}
  
  async def getPhoneNumber(self,service:str,operator:str):
      """Returns ("Error", error Message), when Couldnot fetch phone,
      and (id, phone number) when sucessfully fetched"""
      country = 'india'
      product = service
      url = f"https://5sim.net/v1/user/buy/activation/{country}/{operator}/{product}"
      response = await tools.getJson(url,
                               headers=self.headers)
      try:
        phone = response['phone']
        id = response['id']
        return id,phone
      except KeyError:
        return response
        example = {
          "id":11631253,
          "phone":"+79000381454",
          "operator":"beeline",
          "product":"vkontakte",
          "price":21,
          "status":"PENDING",
          "expires":"2018-10-13T08:28:38.809469028Z",
          "sms":null,
          "created_at":"2018-10-13T08:13:38.809469028Z",
          "forwarding":false,
          "forwarding_number":"",
          "country":"russia"
          }
                

  async def getStatus(self,id):
      url = 'https://5sim.net/v1/user/check/' + str(id)
      response = await tools.getJson(url,
                              headers=self.headers)
      try:
        #Returning the last OTP Received
        return response['status']+(
          response['sms'][-1]['code'] if response['sms'] else "")
      except ValueError as v:
        return response['status']+str(v)
      
      example = {
      "id": 11631253,
      "created_at": "2018-10-13T08:13:38.809469028Z",
      "phone": "+79000381454",
      "product": "vkontakte",
      "price": 21,
      "status": "RECEIVED",
      "expires": "2018-10-13T08:28:38.809469028Z",
      "sms": [
          {
            "created_at":"2018-10-13T08:20:38.809469028Z",
            "date":"2018-10-13T08:19:38Z",
            "sender":"VKcom",
            "text":"VK: 09363 - use this code to reclaim your suspended profile.",
            "code":"09363"
          }
      ],
      "forwarding": false,
      "forwarding_number": "",
      "country":"russia"
      }


  async def changeStatus(self,id,status:str):
    """Change the status of id, status = [finish,cancel]"""
    if status not in ['finish','cancel']:
      return "status are in value finish/cancel"

    url = f'https://5sim.net/v1/user/{status}/' + str(id)
    response =await tools.getJson(url,
                               headers=self.headers)
    try:
      return response['status']
    except ValueError as v:
      return str(v)
    except:
      return "Failed to change status"

    example = {
"id": 11631253,
"created_at": "2018-10-13T08:13:38.809469028Z",
"phone": "+79000381454",
"product": "vkontakte",
"price": 21,
"status": "CANCELED/FINISHED",
"expires": "2018-10-13T08:28:38.809469028Z",
"sms": [
  {
    "created_at":"2018-10-13T08:20:38.809469028Z",
    "date":"2018-10-13T08:19:38Z",
    "sender":"VKcom",
    "text":"VK: 09363 - use this code to reclaim your suspended profile.",
    "code":"09363"
  }
],
"forwarding": false,
"forwarding_number": "",
"country":"russia"
}



  async def getPrice2(self,service:str,provider:str='any'):
      """
      To get the Price of a specific provider, put the value, other wise when provider is 'any'-> it returns a list of dict of different available providers
      """
      headers = {
  'Accept': 'application/json',
      }
      params = (
          ('country', self.country),
          ('product', service),
      )

      response = await tools.getJson('https://5sim.net/v1/guest/prices',
                              headers=headers, params=params)
      try:
        if provider=='any':
          #This is when you want a list of prices for a product
          reply = response[self.country][service]
        else:
          #This is to get a single price for a good, to deduct after purchase
          reply = response[self.country][service][provider]['cost']
        return reply
      except ValueError as v:
        return str(v)
      except KeyError as k:
        return str(k)+str(response)
      
      examples = {
"russia":{
  "telegram":{
    "beeline":{
      "cost":8,
      "count":0,
      "rate": 99.99
    },
    "matrix":{
      "cost":8,
      "count":0,
      "rate": 99.99
    },
    "megafon":{
      "cost":8,
      "count":0,
      "rate": 99.99
    },
    "mts":{
      "cost":8,
      "count":0,
      "rate": 99.99
    },
    "rostelecom":{
      "cost":8,
      "count":0,
      "rate": 99.99
    },
    "tele2":{
      "cost":8,
      "count":0,
      "rate": 99.99
    },
    "virtual15":{
      "cost":8,
      "count":0,
      "rate": 99.99
    },
    "yota":{
      "cost":8,
      "count":0,
      "rate": 99.99
    }
  }
}
}

  
  def rebuyNumber(self,service,number):
      product = service
      url = f"https://5sim.net/v1/user/reuse/{product}/{number}"
      response = requests.get(url,
                              headers=self.headers)
      return response.json()

class getPrice:
    def __init__(self, serviceCode:str="",serviceName:str="", countryCode: str="22") -> None:
        if serviceName:
          self.serviceName = serviceName
        elif serviceCode:
          self.serviceName = hashMap.getServiceName(serviceCode)
        
        self.serverIDs = servicesMenu.getServiceCodes(self.serviceName)  
        self.countryCode = countryCode

    async def getAll(self):
        priceResponse = {}#{"ids":self.serverIDs}
        if self.serverIDs == {'Service Name Not Found':self.serviceName}:
          return self.serverIDs
        
        #Product Detail
        self.countryName = await tools.getCountryNameFromCode(self.countryCode)
        #self.serviceName = await tools.getServiceNameFromCode(self.serviceId)
        priceResponse["detail"] = {
            "Name": self.serviceName,
            "Country": self.countryName
        }
        try:
            #Tiger
            if self.serverIDs["ID Tiger"]:
                tiger_price, tiger_count = await self.tiger()
                priceResponse["tiger"] = {
                    "price": tiger_price,
                    "count": tiger_count
                }
        except:
            pass
        try:
            #FastSMS
            if self.serverIDs["ID Fast"]:
                fast_price, fast_count = await self.fast()
                priceResponse["fastSMS"] = {
                    "price": fast_price,
                    "count": fast_count
                }
        except:
            pass
        try:
            #Bower
            if self.serverIDs["ID Bower"]:
                bower_price, bower_count = await self.bower()
                priceResponse["SMSBower"] = {
                    "price": bower_price,
                    "count": bower_count
                }
        except:
            pass
        try:
            #5Sim
            fiveSim = await self.sim5()
            priceResponse["5Sim"] = fiveSim
        except KeyError as k:
            priceResponse["5Sim"] = 'Key error'+k
            pass
        finally:
            pass
        return priceResponse


    async def getAll2(self):
      """This will uses price function for server class, and replace getAll function"""
      ids:dict = self.serverIDs
      pricesData = {"server ids":ids}
      map = {
        'ID Fast':fastSMS(),
        'ID Tiger':tigerSMS(),
        'ID Bower':bowerSMS(),
        'ID 5Sim':FiveSim()
      }
      for id,fn in map.items():
        if id in ids:
          pricesData[id] = await fn.getPrice(ids[id])
      # pricesData['Fast SMS'] = await fastSMS().getPrice(ids['ID Fast'])
      # pricesData['Tiger SMS'] = await tigerSMS().getPrice(ids['ID Tiger'],
      #                                               self.countryCode)
      # pricesData['Bower SMS'] = await bowerSMS().getPrice(ids['ID Bower'],
      #                                              self.countryCode)
      # resp = await FiveSim().getPrice2(ids['ID 5Sim'])
      # pricesData['5Sim SMS'] = resp
      return pricesData
      
      pass
    async def tiger(self):
        """Returns Price, Count if Valid
        If any error returns error"""
        countryId = self.countryCode
        serviceId = self.serverIDs['ID Tiger']
        base_url = "https://api.tiger-sms.com/stubs/handler_api.php"
        params = {
            "api_key": TOKENS["tiger"],
            "action": "getPrices",
            "service": serviceId,
            "country": countryId
        }
        response = await tools.getJson(base_url, params=params)
        if isinstance(response, requests.Response):            
            params["service"] = self.serverIDs['ID Tiger']
            response = await tools.getJson(base_url, params=params)            
            if isinstance(response, requests.Response):
                return "Error"
            else:
                price = response[countryId][serviceId]["cost"]
                count = response[countryId][serviceId]["count"]
                return float(price), int(count)
        return "Error"

    async def fast(self):
        """Returns Price, Count if Valid
        If any error returns error"""
        countryId = self.countryCode
        serviceId = self.serverIDs["ID Fast"]
        params = {
            "api_key": TOKENS["fast"],
            "action": "getPrices",
            "service": serviceId,
            "country": countryId
        }
        response = await tools.getJson(BASE_URL['fast'], params=params)
        if isinstance(response, requests.Response):
            return "Error"
        price = list(response[countryId][serviceId].keys())[0]
        count = list(response[countryId][serviceId].values())[0]
        return float(price), int(count)

    async def bower(self):
        """Returns Price, Count if Valid
        If any error returns error"""

        countryId = self.countryCode
        serviceId = self.serverIDs['ID Bower']
        base_url = "https://smsbower.com/stubs/handler_api.php"
        params = {
            "api_key": TOKENS["bower"],
            "action": "getPrices",
            "service": serviceId,
            "country": countryId
        }
        response = await tools.getJson(base_url, params=params)
        if isinstance(response, requests.Response):
            return "Error"
        price = response[countryId][serviceId]["cost"]
        count = response[countryId][serviceId]["count"]
        return float(price), int(count)

    async def sim5(self):
        product = str(self.serverIDs['ID 5Sim'])
        country = str(self.countryName).lower()

        headers = {
            'Accept': 'application/json',
        }

        params = (('product', product), )

        response = requests.get('https://5sim.net/v1/guest/prices',
                                headers=headers,
                                params=params)
        try:
            respond = response.json()[product][country]
            return respond
        except:
            return response.content



class getBalances:
    def __init__(self):
        self.server = {
            "fast": self.fast,
            "bower": self.bower,
            "tiger": self.tiger,
            "5Sim": self.sim5
        }

    async def sim5(self):
        headers = {
            'Authorization': 'Bearer ' + TOKENS["5Sim"],
            'Accept': 'application/json',
        }
        response = await tools.getJson('https://5sim.net/v1/user/profile',
                                       headers=headers)
        bal = float(response['balance'])
        return bal

    async def fast(self):
        base_url = "https://fastsms.su/stubs/handler_api.php"
        param = {"api_key": TOKENS["fast"], "action": "getBalance"}
        resp = await tools.getText(base_url, params=param)
        bal = float(resp.split(":")[-1])
        return bal

    async def bower(self):
        base_url_bower = "https://smsbower.com/stubs/handler_api.php"
        params = {"api_key": TOKENS["bower"], "action": "getBalance"}
        resp = await tools.getText(base_url_bower, params=params)
        bal = float(resp.split(":")[-1])
        return bal

    async def tiger(self):
        api_key = TOKENS["tiger"]
        tiger_base_url = "https://api.tiger-sms.com/stubs/handler_api.php?"
        params = {"api_key": api_key, "action": "getBalance"}
        response = await tools.getText(tiger_base_url, params)
        bal = float(response.split(":")[1])
        return bal



tools = commonTools()

async def getAllBalances():
  response = {
    'Fast SMS':await fastSMS().getBalance(),
    'Tiger SMS':await tigerSMS().getBalance(),
    'Bower SMS':await bowerSMS().getBalance(),
    'Five Sim SMS':await FiveSim().getBalance()
  }
  return response


class Test:
  async def getAllPrice(self,ServiceName):
    resp = await getPrice(serviceName=ServiceName).getAll2()
    return resp

  async def fast(self,serviceCode):
    f = fastSMS()
    print("Fast SMS Current Bal",await f.getBalance())
    print("See Price for ",serviceCode,
          await tools.getServiceNameFromCode(serviceCode))
    print(await f.getPrice(serviceCode))
    print("Buying a number")
    
    resp = await f.getPhoneNumber(serviceCode)
    if isinstance(resp,tuple):
      accessID,Phone = resp
      print(accessID,Phone)
    else:
      return resp
    await asyncio.sleep(2)
    status = await f.getStatus(accessID)
    print(status)
    await asyncio.sleep(2)
    status = await f.changeStatus(accessID,8)
    print("Canceled the service ",status)
    status = await f.getStatus(accessID)
    print(status)
    print("Test Complete")

  async def tiger(self,serviceCode):
    f = tigerSMS()
    print("Tiger SMS Current Bal",await f.getBalance())
    print("See Price for ",serviceCode,
          await tools.getServiceNameFromCode(serviceCode))
    print(await f.getPrice(serviceCode))
    print("Buying a number")

    resp = await f.getPhoneNumber(serviceCode)
    if isinstance(resp,tuple):
      accessID,Phone = resp
      print(accessID,Phone)
    else:
      print(resp)
      return resp
    await asyncio.sleep(2)
    status = await f.getStatus(accessID)
    print(status)
    await asyncio.sleep(2)
    status = await f.changeStatus(accessID,8)
    print("Canceled the service ",status)
    status = await f.getStatus(accessID)
    print(status)
    print("Test Complete")

  async def bower(self,serviceCode):
    f = bowerSMS()
    print("Bower SMS Current Bal",await f.getBalance())
    print("See Price for ",serviceCode,
          await tools.getServiceNameFromCode(serviceCode))
    print(await f.getPrice(serviceCode))
    print("Buying a number")
  
    resp = await f.getPhoneNumber(serviceCode)
    if isinstance(resp,tuple):
      accessID,Phone = resp
      print(accessID,Phone)
    else:
      print(resp)
      return resp
    await asyncio.sleep(2)
    status = await f.getStatus(accessID)
    print(status,"Need to wait 2 mins before cancelling")
    await asyncio.sleep(130)
    status = await f.changeStatus(accessID,8)
    print("Canceled the service ",status)
    status = await f.getStatus(accessID)
    print(status)
    print("Test Complete")

  async def tempTest(self):
    b = FiveSim()
    id = "617594029"
    resp = await b.getStatus(id)
    print(resp,"Checking how to cancel the phone")
    resp = await b.changeStatus(id,"cancel")
    print(resp,"Test End")

    
  async def five(self,serviceCode):
    f = FiveSim()
    print("5Sim SMS Current Bal",await f.getBalance())
    print(await f.getPrice(serviceCode))
    print("Buying a number")
    operator = input("Select an operator")
    newPrice = await f.getPrice(serviceCode,operator)
    x = input("This is the price"+str(newPrice))
    resp = await f.getPhoneNumber(serviceCode,operator)
    if isinstance(resp,tuple):
      accessID,Phone = resp
      print(accessID,Phone)
    else:
      print("Error",resp['Error'])
      return resp
    await asyncio.sleep(2)
    status = await f.getStatus(accessID)
    print(status)
    await asyncio.sleep(2)
    status = await f.changeStatus(accessID,'cancel')
    print("Canceled the service ",status)
    status = await f.getStatus(accessID)
    print(status)
    print("Test Complete")


if __name__ == '__main__':
  
  #fastSMS().test('idg')
  #tigerSMS().test('aa')
  #bowerSMS().test('ig')
  t = Test()
  #print(asyncio.run(t.getAllPrice("Telegram")))
  #asyncio.run(t.fast('tg')) #Working very fine #Unable to cancel Phone Number
  # asyncio.run(t.tiger('ig'))  # Couldnot check for low balance stopped at buying number
  #asyncio.run(t.bower('ig'))  #Working fine verified
  asyncio.run(t.tempTest()) 
  # asyncio.run(t.five('probo')) #Working Fine
  
