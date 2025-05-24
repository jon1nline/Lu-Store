from pydantic import BaseModel, EmailStr

class UserBase(BaseModel): #checa 
    email: EmailStr
    name: str
    phone: str


class User(UserBase):
    id: int
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
     
  
class TokenData(BaseModel):
    email: str | None = None

 

class NewUser(BaseModel):
   email: str
   password: str
   name: str
   phone: str    