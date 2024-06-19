from pydantic import BaseModel, EmailStr
from typing import Optional

import datetime

class ContactSchema(BaseModel):
    fullname: str
    email: EmailStr
    phone_number:str
    birthday: datetime.date
    #birthdate: str

    class Config:
        from_attributes = True

class ContactResponse(ContactSchema):
    id: int
   

    class Config:
        from_attributes = True 
        orm_mode=True
        #orm_mode = True

class UserModel(BaseModel):
    username: str
    password: str
    refresh_token: Optional[str] = None
 
    class Config:
        from_attributes = True  

class RequestEmail(BaseModel):
    email: EmailStr



# class ContactUpdate(BaseModel):
#     fullname: Optional[str]
#     email: Optional[EmailStr]
#     phone_number: Optional[str]
#     birthday: Optional[datetime.date]

#     class Config:
#         orm_mode = True