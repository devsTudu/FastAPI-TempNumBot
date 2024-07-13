import asyncio
from typing import Union
import time
from models import (serviceDetails,serviceInfo,phoneDetails,
                    Error,countryInfo,SERVERS,priceResponse,offers)
from tools import (commonTools,BASE_URL,TOKENS, show)
from pydantic import BaseModel

tools = commonTools()


class fastSMS:
  def __init__(self, countryID: int = 22) -> None:
    self.url = BASE_URL['fast']
    self.main_params = {"api_key": TOKENS["fast"], "country": countryID}

  
  async def getPhoneNumber(self,serviceDet:serviceDetails,user:str)->Union[phoneDetails,dict]:
    params = self.main_params
    params['service'] = serviceDet.serviceInfo.fastCode
    params['action'] = "getNumber"
    params['country'] = serviceDet.serviceInfo.country.code
    response = await tools.getText(self.url,params=params)
    if not tools.isError(response) and ":" in response:
       _,access,phone = response.split(":")
       return phoneDetails(serviceDetail=serviceDet,phone=phone,access_id=access,user=user,status='Waiting',)
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

  async def getMultipleStatus(self,arrOfPhoneDetails:list[phoneDetails])->list[phoneDetails]:
    arrAccessID = []
    for i in range(len(arrOfPhoneDetails)):
       arrAccessID.append(arrOfPhoneDetails[i].access_id)

    arrAccessID = list(map(str,arrAccessID)) #Converting the AccessIDs into String format
    params = self.main_params
    params['id'] = str(arrAccessID).replace("'",'"')
    params['action'] = "getStatus_2"
    response = await tools.getJson(self.url,params=params)
    show(response)
    show(params)
    if not tools.isError(response):
      for id,status in response.items():
         for phone in arrOfPhoneDetails:
            if phone.access_id == id:
               if 'WAIT' in status: phone.status = 'Waiting'
               elif 'CANCEL' in status: phone.status = 'Cancelled'
               elif 'OK' in status:
                  phone.status = 'Success'
                  phone.otp = status.split(":")[-1]
      return arrOfPhoneDetails
    

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
    response = await tools.getText(self.url,params=params)

    return response

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
      
  async def getServiceDetails(self,service:serviceInfo)->Union[serviceDetails,Error]:
      base_url = "https://api.tiger-sms.com/stubs/handler_api.php"
      serviceid = service.tigerCode
      countrycode = service.country.code
      params = self.params
      params['action'] = "getPrices"
      params['service'] = serviceid
      params['country'] = countrycode
      response = await tools.getJson(base_url, params=params)
      try:
        data = response[countrycode][serviceid]
        return serviceDetails(server='Tiger',serviceInfo=service,**data)
        #return response[countrycode][serviceid]
      except KeyError:
        return Error(message=f"{service.name} not found in TigerSMS")
      except TypeError as t:
        return Error(message=f"Service {serviceid} has {str(t)}")

  async def getPhoneNumber(self, serviceDet:serviceDetails,user:str)->Union[phoneDetails,Error]:
    params = self.params
    params['service'] = serviceDet.serviceInfo.tigerCode
    params['action'] = "getNumber"
    params['country'] = serviceDet.serviceInfo.country.code
    params['ref'] = 'Nothing'
    response = await tools.getText(self.url, params)
    if not tools.isError(response) and ":" in response:
        _, access, phone = response.split(":")
        return phoneDetails(serviceDetail=serviceDet,
                            access_id=access,
                            phone=phone,user=user)
    else:
       return Error(message=response)
    
  async def getStatus(self, phoneDet:phoneDetails)->phoneDetails:
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
    params['id'] = phoneDet.access_id
    params['action'] = "getStatus"
    response = await tools.getText(self.url, params=params)
    if not tools.isError(response):
        if "WAIT" in response:
          phoneDet.status = 'Waiting'
        elif "CANCEL" in response:
          phoneDet.status = 'Cancelled'
        elif "OK" in response:
          phoneDet.status = "Success"
          phoneDet.otp = response.split(":")[-1]
        return phoneDet
    


  async def changeStatus(self, phoneDet:phoneDetails, code: int)->phoneDetails:
    """
    Change the status of the given access ID,
    1 - inform about the readiness of the number (SMS sent to the number)
    3 - request another code (free)
    6 - complete activation *
    8 - inform that the number has been used and cancel the activation
    """
    """
    ** if there was a status 'code received' - marks it successfully and completes, if there was a 'preparation' - deletes and marks an error, if there was a status 'awaiting retry' - transfers activation to SMS pending

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
    params['id'] = phoneDet.access_id
    params['status'] = str(code)
    params['action'] = 'setStatus'

    response = await tools.getText(self.url, params=params)
    if not tools.isError(response):
       if "ACCESS_READY" in response:
          phoneDet.status = 'Waiting'
       elif "ACCESS_RETRY_GET" in response:
          phoneDet.status = 'Waiting'
       elif "ACCESS_CANCEL" in response:
          phoneDet.status = 'Expired'
       else:
          phoneDet.status = 'Invalid'
       return phoneDet

  async def cancelService(self,accessid:str=None,phoneDet:phoneDetails=None)->bool:
     """Returns True if the service has been cancelled successfully
     False if the service has not been cancelled or an error has occurred"""
     if accessid:
        phoneDet = phoneDetails(phone='987654321',access_id=accessid)
     resp = await self.changeStatus(phoneDet,8)
     return resp.status == 'Expired'

  async def test_prices(self,service='aa'):
     req = serviceInfo(name="Probo",tigerCode=service,country=countryInfo())
     resp = await self.getServiceDetails(req)
     show(resp)
     

  async def test(self,code,name):
    print("Tiger Test")
    service_info = serviceInfo(name=name,tigerCode=code,country=countryInfo())
    service = await self.getServiceDetails(service_info)
    show(service)
    resp = await self.getPhoneNumber(service,'987654321')
    if isinstance(resp,Error):
      return resp
    try:
      show(resp)
      show("Status")
      asyncio.sleep(120)
      stat = await self.getStatus(resp)
      show(stat)
      canceled = await self.cancelService(phoneDet=stat)
      show(canceled)
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

  async def getServiceDetails(self,service:serviceInfo)->Union[serviceDetails,Error]:
      params = self.params
      serviceCode = service.bowerCode
      countryCode = service.country.code
      params['action'] = "getPrices"
      params['service'] = serviceCode
      params['country'] = countryCode
      response = await tools.getJson(self.url, params=params)
      if tools.isError(response):
        return response
      try:
        data = response[countryCode][serviceCode] #cost and count
        return serviceDetails(server='Bower',serviceInfo=service,**data)
      except KeyError as k:
          return Error(message=str(k))
    
  async def getPhoneNumber(self,serviceDet:serviceDetails,user:str='')->Union[phoneDetails,Error]:
    params = self.params
    params['service'] = serviceDet.serviceInfo.bowerCode
    params['action'] = "getNumber"
    params['country'] = serviceDet.serviceInfo.country.code
    params['maxPrice'] = 100 #MAx Price for the phone number
    params['phoneException'] = 987654321 #To get a new number needs old number
    params['ref'] = 'none'
    response = await tools.getText(self.url,params=params)
    if not tools.isError(response) and ":" in response:
      _, access, phone = response.split(":")
      return phoneDetails(serviceDetail=serviceDet,
                          access_id=access,
                          phone=phone,user=user)
    else:
       return Error(message=response)

  async def getStatus(self, phoneDet:phoneDetails)->phoneDetails:
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
    params['id'] = phoneDet.access_id
    params['action'] = "getStatus"
    response = await tools.getText(self.url, params=params)

    if not tools.isError(response):
        show(response)
        if "WAIT" in response:
          phoneDet.status = 'Waiting'
        elif "CANCEL" in response:
          phoneDet.status = 'Cancelled'
        elif "OK" in response:
          phoneDet.status = "Success"
          phoneDet.otp = response.split(":")[-1]
        return phoneDet

  async def changeStatus(self,phoneDet:phoneDetails, code: int)->phoneDetails:
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
    params['id'] = phoneDet.access_id
    params['status'] = str(code)
    params['action'] = "setSatus"

    response = await tools.getText(self.url, params=params)
    if not tools.isError(response):
       show(response)
       if "ACCESS_READY" in response:
          phoneDet.status = 'Waiting'
       elif "ACCESS_RETRY_GET" in response:
          phoneDet.status = 'Waiting'
       elif "ACCESS_CANCEL" in response:
          phoneDet.status = 'Expired'
       else:
          phoneDet.status = 'Invalid'
       return phoneDet
    
  async def cancelService(self,accessid:str=None,phoneDet:phoneDetails=None)->bool:
     """Returns True if the service has been cancelled successfully
     False if the service has not been cancelled or an error has occurred"""
     if accessid:
        phoneDet = phoneDetails(phone='987654321',access_id=accessid)
     resp = await self.changeStatus(phoneDet,8)
     return resp.status == 'Expired'


  async def getPhoneV2(self, serviceCode: str, maxPrice: int = 100):
    params = self.params
    params['service'] = serviceCode
    params['action'] = "getNumberV2"
    params['country'] = '22'
    params['maxPrice'] = str(maxPrice)

    response = await tools.getJson(self.url, params=params)
    return response

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

  async def getServiceDetails(self,service:serviceInfo)->Union[list[serviceDetails],Error]:
      serviceCode = service.fiveCode
      countryCode = service.country.name
      if not serviceCode:
        return Error(message=f"Service {serviceCode}not found in 5Sim")
      params = {
        'product':serviceCode,
        'country':countryCode
      }

      response = await tools.getJson('https://5sim.net/v1/guest/prices',
                              headers=self.headers,
                              params=params)
      try:
          respond = response[countryCode][serviceCode]
          lis = []
          for key,val in respond.items():
            data = {
              'server':'5Sim',
              'serviceInfo':service,
              'provider':key,
              'count':val['count'],
              'cost':val['cost']
            }
            if data['count'] == 0: continue
            lis.append(serviceDetails(**data))
          return lis
      except :
          return Error(message=str(response)) 
  
  async def getPhoneNumber(self,serviceDet:serviceDetails,user:str="1234567")->Union[phoneDetails,Error]:
      """Returns ("Error", error Message), when Couldnot fetch phone,
      and (id, phone number) when sucessfully fetched"""
      country = serviceDet.serviceInfo.country.name
      product = serviceDet.serviceInfo.fiveCode
      operator = serviceDet.provider
      url = f"https://5sim.net/v1/user/buy/activation/{country}/{operator}/{product}"
      response = await tools.getJson(url,
                               headers=self.headers)
      try:
        phone = response['phone']
        id = str(response['id'])
        serviceDet.cost = response['price']
        return phoneDetails(access_id=id,phone=phone,serviceDetail=serviceDet,user=user)
      except KeyError:
        return Error(message=response['Error'])
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
                

  async def getStatus(self,phoneDet:phoneDetails)->phoneDetails:
      """"
      PENDING - Preparation
      RECEIVED - Waiting of receipt of SMS
      CANCELED - Is cancelled
      TIMEOUT - A timeout
      FINISHED - Is complete
      BANNED - Number banned, when number already used
      """
      
      url = 'https://5sim.net/v1/user/check/' + phoneDet.access_id
      response = await tools.getJson(url,
                              headers=self.headers)
      if tools.isError(response):
        phoneDet.status='Invalid'
      else:
        try:
          #Returning the last OTP Received
          if "PENDING" in response['status']:
            phoneDet.status='Waiting'
          elif response['status'] in ['CANCELED', 'TIMEOUT','BANNED']:
            phoneDet.status='Expired'
          elif response['status'] in ['RECEIVED','FINISHED']:
            if  response['sms']:
              phoneDet.status='Success'
              phoneDet.otp=response['sms'][-1]['code']
            else:
              phoneDet.status='Waiting'
        except ValueError as v:
          phoneDet.status='Invalid'
      return phoneDet
        
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


  async def changeStatus(self,phoneDet:phoneDetails,code:str)->bool:
    """Change the status of id, status = [finish,cancel]"""
    if code not in ['finish','cancel']:
      return "status are in value finish/cancel"

    url = f'https://5sim.net/v1/user/{code}/' + str(id)
    response =await tools.getJson(url,
                               headers=self.headers)
    try:
      return response['status']=="CANCELED/FINISHED"
    except:
      return False

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

  async def cancelService(self,phoneDet:phoneDetails)->bool:
    """Cancel the service"""
    return await self.changeStatus(phoneDet,'cancel')

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

  
  async def rebuyNumber(self,service,number):
      product = service
      url = f"https://5sim.net/v1/user/reuse/{product}/{number}"
      response = await tools.getJson(url,
                              headers=self.headers)
      return response

class api_requests:
  def __init__(self):
    self.fast = fastSMS()
    self.tiger = tigerSMS()
    self.bower = bowerSMS()
    self.five = FiveSim()
    self.server = {
      "Fast":self.fast,
      "Tiger":self.tiger,
      "Bower":self.bower,
      "5Sim":self.five
    }
  
  async def getBalance(self,serverName:SERVERS):
    if serverName == "Fast":
      server = self.fast
    elif serverName == "Tiger":
      server = self.tiger
    elif serverName == "5Sim":
      server = self.five
    elif serverName == "Bower":
      server = self.bower
    else:
      return "Server not found"
    bal = await server.getBalance()
    return {serverName:bal}
  
  async def getPrices(self, serviceinfo:serviceInfo):
    lis = []
    if serviceinfo.bowerCode:
      lis.append(await self.bower.getServiceDetails(serviceinfo))
    if serviceinfo.tigerCode:
      lis.append(await self.tiger.getServiceDetails(serviceinfo))
    if serviceinfo.fastCode:
      lis.append(await self.fast.getServiceDetails(serviceinfo))
    if serviceinfo.fiveCode:
      lis += await self.five.getServiceDetails(serviceinfo)
    offering = []
    for i in lis:
      if tools.isError(i):
        continue
      data = {
        "server":i.server,
        "provider":i.provider,
        "cost":i.cost,
        "count":i.count
      }
      offering.append(offers(**data))
    resp = priceResponse(service=serviceinfo,offers=offering)
    return resp.dict()

  async def getPricesFromName(self, serviceName:str):
    serviceinfo = tools.getServiceInfo(serviceName,country=countryInfo())
    if serviceinfo is None:
      return "Service not found"
    return await self.getPrices(serviceinfo)
  
  async def getPhoneFromName(self,server:SERVERS,
                        serviceName:str=None,
                        provider:str='Any',
                        user:str='123456789')->phoneDetails:
    serviceinfo = tools.getServiceInfo(serviceName,countryInfo())
    if serviceinfo is None:
      return "Service not found"
    service = serviceDetails(server=server,
                        provider=provider,
                        serviceInfo=serviceinfo)
    return await self.getPhone(serviceOrder=service,user=user)

  async def getPhone(self,serviceOrder:serviceDetails,user)->phoneDetails:
    server = self.server[serviceOrder.server]
    return await server.getPhoneNumber(serviceOrder,user=user)
    
  async def getStatus(self,serverName:SERVERS,
                      access_id:str,
                      phone=123456789)->phoneDetails:
    server = self.server[serverName]
    return await server.getStatus(phoneDet=phoneDetails(access_id=access_id,phone=phone))

  async def cancelPhone(self,serverName:SERVERS,access_id:str):
    server = self.server[serverName]
    return await server.cancelService(access_id)