from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Date, func, Enum, Numeric
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, JSONB
from database import Base
from enum import Enum as PyEnum

class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(100))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)


class Clients(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True)
    cpf = Column(String(14), unique=True, index=True) #Formato é 000.000.000-00
    telefone = Column(String(20))
    empresa = Column(String(100))
    endereco = Column(String(200))
    is_active = Column(Boolean, default=True)
    last_update = Column(DateTime(timezone=True), onupdate=func.now())

class Produtos(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)  
    nome = Column(String(100), nullable=False)
    descricao = Column(String(100), nullable=False)
    sessao = Column(String(100), nullable=False)
    codigo_barras = Column(BIGINT, unique=True, nullable=False) 
    preco = Column(Integer, nullable=False)
    estoque_inicial = Column(Integer, nullable=False)
    estoque_atual = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    data_validade = Column(Date, nullable=True) 
    images = Column(ARRAY(String))

class OrderStatus(PyEnum):
    DRAFT = "rascunho"
    PENDING = "pendente"
    CONFIRMED = "confirmado"
    PROCESSING = "processando"
    SHIPPED = "enviado"
    DELIVERED = "entregue"
    CANCELLED = "cancelado"
    RETURNED = "devolvido"

class Pedidos(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(20), unique=True, index=True)
    id_cliente = Column(Integer, ForeignKey("clients.id"), nullable=False)
    id_vendedor = Column(Integer, ForeignKey("users.id"), nullable=False)
    items = Column(JSONB, nullable=False)  # {product_id, quantity, unit_price, total_price}
    quantidade = Column(Integer)

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)

 
    




