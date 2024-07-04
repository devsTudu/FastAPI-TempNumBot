import asyncio
from typing import Union
import time
from models import (serviceDetails,serviceInfo,phoneDetails,Error,countryInfo)
from tools import (commonTools,BASE_URL,TOKENS, show)

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
    if not tools.isError(response) and ":" in response:
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
    

  async def test_getNo(self):
     service = serviceInfo(name='Probo',fastCode='aa',country=countryInfo(),)
     serviceDet = await self.getServiceDetails(service)
     phone = await self.getPhonenumber(service= serviceDet,user='1234567')
     show(phone)
     return phone
  async def test_serviceDetails(self):
     req = serviceInfo(name='Probo',fastCode='aa',country=countryInfo())
     service =await self.getServiceDetails(req)
     show(service)
  async def test_getStatus(self):
     x = await self.getStatus(phoneDetails(phone='7798564311',access_id="171991856255350",user=''))
     show(x)
  async def test_cancel_phone(self):
     x = await self.cancelService("171992269389667")
     show(x)
  async def test_Multiple(self):
     phone1 = phoneDetails(phone='123456789',access_id="172001563298249")
     phone2 = phoneDetails(phone='9876543217',access_id="172000539116086",user='9556130490')
     phone3 = phoneDetails(phone='654321987',access_id="172001380934482",user='9938242526')
     arr = [phone3,phone2,phone1]
     arr = await self.getMultipleStatus(arr)
     for a in arr:
        show(a)
 
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
      
  async def getServiceDetails(self,service:serviceInfo)->Union[serviceDetails,dict]:
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
        return {"Error":response}
      except TypeError as t:
        return {'Error':str(t)}

  async def getPhoneNumber(self, service:serviceDetails,user:str)->Union[phoneDetails,Error]:
    params = self.params
    params['service'] = service.serviceInfo.tigerCode
    params['action'] = "getNumber"
    params['country'] = service.serviceInfo.country.code
    params['ref'] = 'Nothing'
    response = await tools.getText(self.url, params)
    if not tools.isError(response) and ":" in response:
        _, access, phone = response.split(":")
        return phoneDetails(serviceDetail=service,
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
       return Error(response)

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

  async def test(self, code,name):
    print("Bower Test")
    try:
      req = serviceInfo(bowerCode=code,name=name,country=countryInfo())
      service = await self.getServiceDetails(req)
      show(service)
      x = 1 #input("Buy (y/n):")
      if x == 1:
        phone = await self.getPhoneNumber(serviceDet=service,user='9348692623')
        print(1)
        show(phone)
        if isinstance(phone,phoneDetails):  
          if phone.status == 'Waiting':
            show("Waiting 10 sec before canceling")
            time.sleep(10)
            cancel = await self.cancelService(phoneDet=phone)
            show(cancel)
        else:
          show(await self.getStatus(service,'12345678'))
    except Exception as e:
      print(e)
        


if __name__ == '__main__':
    tiger = tiger()
    a = asyncio.run(tiger.test('ig','Instagram'))
    print(a)
    
    bower = bowerSMS()
    a = asyncio.run(bower.test('ig','Instagram'))
    print(a)

# Tests Functions Declared
def test_countryFromID():
    x = asyncio.run(tools.getCountryNameFromCode('22'))
    assert x == 'india'

def test_serviceFromID():
    x = asyncio.run(tools.getServiceNameFromCode('tg'))
    assert x == 'Telegram'
