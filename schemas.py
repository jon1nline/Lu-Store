from pydantic import BaseModel, EmailStr, validator 
from typing import Optional
import re

class UserBase(BaseModel): #checa 
    email: EmailStr
    name: str
    phone: str


class User(UserBase):
    id: int
    token: str
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
  
class TokenData(BaseModel):
    email: str | None = None

class TokenRefresh(BaseModel):
    refresh_token: str    

class NewUser(BaseModel):
   email: str
   password: str
   name: str
   phone: str    

## aqui finaliza cadastro e login de funcionários
# iniciando clientes.

class ClientBase(BaseModel):
    name: str
    email: EmailStr
    cpf: str
    phone: str
    address: str | None = None
    company: str

class ClientCreate(ClientBase):
    cpf: str
    
    @validator('cpf')
    def validate_cpf(cls, v):
        # Remove caracteres não numéricos
        cpf = re.sub(r'[^0-9]', '', v)
        
        if len(cpf) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        
        # Formata o CPF
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'

class Client(ClientBase):
    id: int
    email: EmailStr
    cpf: str
    is_active: bool
    
    class Config:
        from_attributes = True   