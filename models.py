from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Date, func, Enum, Numeric
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, JSONB
from sqlalchemy.orm import relationship
from database import Base
from enum import Enum as PyEnum
from datetime import datetime


class Users(Base): #tabela que regista os usuários.
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(100))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)


class Clients(Base): #tabela que registra os clientes
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True)
    cpf = Column(String(14), unique=True, index=True) #Formato é 000.000.000-00
    phone = Column(String(20))
    company = Column(String(100))
    address = Column(String(200))
    is_active = Column(Boolean, default=True)
    last_update = Column(DateTime(timezone=True), onupdate=func.now())

class Products(Base): #tabela que registra os produtos
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)  
    name = Column(String(100), nullable=False)
    desc = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    barcode = Column(String(13), unique=True, index=True) 
    sales_price = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False)
    expiry_date = Column(Date, nullable=True) 
    is_active = Column(Boolean, default=True)
    last_update = Column(DateTime(timezone=True), onupdate=func.now())
    image_URL = Column(String(200), nullable=True)

#tabelas para organizar os pedidos
class OrderStatus(PyEnum):
    PENDING = "pendente"
    PROCESSING = "processando"
    SHIPPED = "enviado"
    DELIVERED = "entregue"
    CANCELLED = "cancelado"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    status = Column(
        Enum(OrderStatus, name="orderstatus"),  # Nome do tipo ENUM no PostgreSQL
        default=OrderStatus.PENDING,
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    total_amount = Column(Numeric(10, 2))
    
    items = relationship("OrderItem", back_populates="order")
    client = relationship("Clients")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    unit_price = Column(Numeric(10, 2))
    
    order = relationship("Order", back_populates="items")
    product = relationship("Products", lazy="joined")

 
    




