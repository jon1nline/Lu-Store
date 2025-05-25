from pydantic import BaseModel, EmailStr, validator, Field, field_validator
from typing import Optional, Union, Annotated
import re
from datetime import datetime

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
    last_update: datetime

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

class ProductBase(BaseModel):
    name:str = Field(..., max_length=100)
    desc: str = Field(..., max_length=200)
    category: str = Field(..., max_length=50)
    barcode: Annotated[str, Field(min_length=8, max_length=13, pattern=r'^\d+$')]
    sales_price: int
    stock: int 
    expiry_date: Optional[Union[datetime, str]] = None
    image_URL: Optional[str] = None  

    @field_validator('expiry_date', mode='before')
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v 
    
    @field_validator('barcode')
    def validate_barcode(cls, v):
        if not v.isdigit():
            raise ValueError('O código de barras deve conter apenas números')
        if len(v) not in (8, 12, 13, 14):  # Padrões comuns EAN-8, UPC-A, EAN-13, GS1-14
            raise ValueError('Tamanho inválido para código de barras')
        return v

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    is_active: bool
    last_update: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    desc: Optional[str] = Field(None, max_length=200)
    sales_price: Optional[int] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = None  
    image_URL: Optional[str] = None    