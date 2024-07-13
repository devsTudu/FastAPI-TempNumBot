import re
from typing import Literal, Optional, Union
from pydantic import BaseModel, Field, PositiveFloat, PositiveInt


SERVERS = Literal['Fast', 'Tiger', '5Sim', 'Bower']

# Data Model Declaration
class countryInfo(BaseModel):
    name: str = 'india'
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
    count: PositiveInt=1
    cost: PositiveFloat=1.0

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

class Error(BaseModel):
   message: Union[dict,str]

class offers(BaseModel):
    """The modified model to show inside the bot"""
    server:SERVERS
    provider:Optional[str]='Any'
    count:PositiveInt
    cost:PositiveFloat

class priceResponse(BaseModel):
    service:serviceInfo
    offers:list[offers]