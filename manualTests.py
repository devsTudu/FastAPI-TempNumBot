from helper import (bowerSMS,tigerSMS,fastSMS,FiveSim,api_requests)
from helper import tools,show
from helper import countryInfo,serviceInfo,serviceDetails,phoneDetails
import asyncio
import time

class testFunctions:
  def __init__(self,service:serviceInfo):
    self.bower = bowerSMS()
    self.tiger = tigerSMS()
    self.fast = fastSMS()
    self.fivesim = FiveSim()
    self.service = service

  async def testServer(self,serverName:str):
    if serverName == 'bower':
      print("Bower Test Starting")
      server = self.bower
    elif serverName == 'tiger':
      print("Tiger Test Starting")
      server = self.tiger
    elif serverName == 'fast':
      print("Fast Test Starting")
      server = self.fast
    elif serverName == '5sim':
      print("5sim Test Starting")
      server = self.fivesim
    else:
      print("Invalid Server Name")
      return None
    bal = await server.getBalance()
    print("Balance: " + str(bal))
    serviceDet =await server.getServiceDetails(service=self.service)
    show(serviceDet)
    if isinstance(serviceDet,list):
      provider_list = []
      for i in serviceDet:
        provider_list.append(i.provider)
        print("%s cost: %i count:%i" % (i.provider,i.cost,i.count))
      while True:
        provider = input("Enter Provider:")
        if provider in provider_list:
          for i in serviceDet:
            if i.provider == provider:
              serviceDet = i
              break
          break
        else: print(f"Invalid {provider}")

    if not isinstance(serviceDet, serviceDetails):
      return None
    phone = await server.getPhoneNumber(serviceDet=serviceDet,user='9348692623')
    show(phone)
    if isinstance(phone,phoneDetails):
      if phone.status == 'Waiting':
        show("Waiting 10 sec before canceling")
        time.sleep(10)
        cancel = await server.cancelService(phoneDet=phone)
        print("Cancelling now the phone number, sucess:",end=" ")
        show(cancel)

def manualTest():
    name = "Facebook" #input("Enter the service name to test:")
    service = tools.getServiceInfo(name,country=countryInfo())
    show(service)
    test = testFunctions(service=service)
    print("Servers :","bower,tiger.fast,5sim")
    server = "bower" #input("Select a server to test:")
    asyncio.run(test.testServer(serverName=server))

#manualTest()
def  api_req_test():
  name = "Facebook" #input("Enter the service name to test:")
  resp = asyncio.run(api_requests().getPricesFromName(name))
  show(resp)

#api_req_test()