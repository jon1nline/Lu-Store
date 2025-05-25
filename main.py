from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from typing import List, Annotated
import models, schemas
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from auth import (
    get_current_user,
    get_current_active_user,
    get_current_superuser,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_password_hash,
    convert_order_status,
    reverse_order_status,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_db
)
 


app = FastAPI()

models.Base.metadata.create_all(bind=engine)


db_dependency = Annotated[Session, Depends(get_db)]

@app.post("/auth/register")
async def create_user(user: schemas.NewUser, db: db_dependency):
   db_user = db.query(models.Users).filter(models.Users.email == user.email).first()
   if db_user:     #acima verifica se o e-mail já está registrado, e se tiver ele não permite o cadastro.
        raise HTTPException(status_code=400, detail="Email already registered")
   hashed_password = get_password_hash(user.password)
   db_newuser = models.Users(email=user.email,hashed_password=hashed_password,name=user.name,phone=user.phone)
   db.add(db_newuser)
   db.commit()
   db.refresh(db_newuser)
   return {"message": "New User sucessfully created."}
   

@app.post("/auth/login")
def login_for_access_token(email: str, password: str, db: Session = Depends(get_db)):
    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }

@app.post("/token",response_model=schemas.Token)
def login_swaggerUI(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {
        "access_token": access_token, "token_type":"bearer"
    }

@app.post("/auth/refresh-token")
async def refresh_token(refresh_data: schemas.TokenRefresh):
    payload = verify_refresh_token(refresh_data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_email = payload.get("sub")
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    
    new_access_token = create_access_token(data={"sub": user_email})
    new_refresh_token = create_refresh_token(data={"sub": user_email})
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token
    }

#Cadastro, exibição, edição e exclusão de clientes.

#Faz cadastro de novo cliente.
@app.post("/clients")
async def create_client(
    client: schemas.ClientCreate,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_active_user)
):
    # Verifica se email já existe
    db_email = db.query(models.Clients).filter(models.Clients.email == client.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Verifica se CPF já existe
    db_cpf = db.query(models.Clients).filter(models.Clients.cpf == client.cpf).first()
    if db_cpf:
        raise HTTPException(status_code=400, detail="CPF já cadastrado")
    
    db_client = models.Clients(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

#lista todos os clientes com paginação e filtros opcionais.
@app.get("/clients")
async def list_clients(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = Query(None, min_length=1),
    email: Optional[str] = Query(None, min_length=1),
    include_inactive: bool = Query(False, description="Incluir clientes inativos"),
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_active_user)
):
    query = db.query(models.Clients)
    
    # Filtro padrão para mostrar apenas ativos, a menos que solicitado
    if not include_inactive:
        query = query.filter(models.Clients.is_active == True)  # ou == 1, dependendo do seu DB
    
   #exibe os clientes
    if name:
        query = query.filter(models.Clients.name.ilike(f"%{name}%"))
    if email:
        query = query.filter(models.Clients.email.ilike(f"%{email}%"))
    
    clients = query.offset(skip).limit(limit).all()
    return clients


#seleciona um cliente especifico utilizando o cliente id
@app.get("/clients/{client_id}", response_model=schemas.ClientBase)
async def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_active_user)
):
    db_client = db.query(models.Clients).filter(models.Clients.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return db_client

# Atualização de clientes - Somente permitido para SuperUsers.
@app.put("/clients/{client_id}", response_model=schemas.ClientBase)
async def update_client(
    client_id: int,
    client: schemas.ClientCreate,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_superuser)  
):
    db_client = db.query(models.Clients).filter(models.Clients.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Verifica se novo email já existe (outro cliente)
    if client.email != db_client.email:
        db_email = db.query(models.Clients).filter(models.Clients.email == client.email).first()
        if db_email:
            raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Verifica se novo CPF já existe (outro cliente)
    if client.cpf != db_client.cpf:
        db_cpf = db.query(models.Clients).filter(models.Clients.cpf == client.cpf).first()
        if db_cpf:
            raise HTTPException(status_code=400, detail="CPF já cadastrado")
    
    for key, value in client.model_dump().items():
        setattr(db_client, key, value)
    
    db.commit()
    db.refresh(db_client)
    return db_client

# Exclui usuário - soft delete(marca apenas active = false)
@app.delete("/clients/{client_id}")
async def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_superuser)
):
    db_client = db.query(models.Clients).filter(models.Clients.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Soft delete (marca como inativo)
    db_client.is_active = False
    db.commit()
    
    return {"message": "Cliente desativado com sucesso"}


#Cadastro, exibição, edição e exclusão de PRODUTOS

#Rota para adicionar produto
@app.post("/products", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_superuser)
):
    
    product_data = product.model_dump()
    if product_data.get('expiry_date') == "":
        product_data['expiry_date'] = None

    
    # Verifica se código de barras já existe
    db_product = db.query(models.Products).filter(models.Products.barcode == product.barcode).first()
    if db_product:
        raise HTTPException(status_code=400, detail="Código de barras já cadastrado")
    
    db_product = models.Products(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

#rota para exibir produtos com paginação e filtros
@app.get("/products", response_model=List[schemas.Product])
async def list_products(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = Query(100, le=1000),  # Limite máximo de 1000 itens
    category: Optional[str] = Query(None, min_length=1),
    min_price: Optional[float] = Query(None, gt=0, description="Filtro por preço mínimo"),
    max_price: Optional[float] = Query(None, gt=0, description="Filtro por preço máximo"),
    is_active: Optional[bool] = Query(True, description="Filtrar produtos ativos/inativos"),
    current_user: models.Users = Depends(get_current_active_user)
):
    query = db.query(models.Products)
    
    # Filtro básico para produtos ativos
    query = query.filter(models.Products.is_active == is_active)
    
    if category:
        query = query.filter(models.Products.category.ilike(f"%{category}%"))
    
    if min_price:
        query = query.filter(models.Products.sale_price >= min_price)
    
    if max_price:
        query = query.filter(models.Products.sale_price <= max_price)
    
    
    products = query.offset(skip).limit(limit).all()
    return products

#rota para exibir produto especifico
@app.get("/products/{product_id}", response_model=schemas.Product)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_active_user)
):
    db_product = db.query(models.Products).filter(models.Products.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return db_product

# iv. Atualizar produto
@app.put("/products/{product_id}", response_model=schemas.Product)
async def update_product(
    product_id: int,
    product: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_superuser)
):
    db_product = db.query(models.Products).filter(models.Products.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    update_data = product.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

# v. Excluir produto (soft delete)
@app.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_superuser)
):
    db_product = db.query(models.Products).filter(models.Products.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    db_product.is_active = False
    db.commit()
    return {"message": "Produto desativado com sucesso"}

#Cadastro e manipulação de pedidos

#cadastra um novo pedido
@app.post("/orders", response_model=schemas.OrderResponse, status_code=201)
async def create_order(
    order_data: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_active_user)
):
    try:
        # Verifica se já existe transação para não causar erro.
        if db.in_transaction():
            db.begin_nested()  # Usa savepoint se necessário
        else:
            db.begin()  # Inicia nova transação apenas se não existir

        order_items = []
        total_amount = 0

        # Processa itens do pedido
        for item in order_data.items:
            product = db.query(models.Products).filter(
               models.Products.id == item.product_id
            ).with_for_update().one()  # Lock para evitar race conditions

            if product.stock < item.quantity:
                db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Estoque insuficiente: {product.desc}"
                )

            item_total = product.sales_price * item.quantity
            total_amount += item_total
            order_items.append({
                "product": product,
                "quantity": item.quantity,
                "unit_price": product.sales_price
            })
        # Cria o pedido
        db_status = convert_order_status(order_data.status)
        order = models.Order(
            client_id=order_data.client_id,
            status=db_status,
            total_amount=total_amount
        )
        db.add(order)
        db.flush()  # Obtém ID para os itens

        # Adiciona itens e atualiza estoque
        for item in order_items:
            db.add(models.OrderItem(
                order_id=order.id,
                product_id=item["product"].id,
                quantity=item["quantity"],
                unit_price=item["unit_price"]
            ))
            item["product"].stock -= item["quantity"]

        db.commit()
        return order

    except SQLAlchemyError as e:
        db.rollback()  # Importante! caso dê erro ele não atualiza o banco.
        raise HTTPException(
            status_code=500,
            detail=f"Erro no banco de dados: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao processar pedido: {str(e)}"
        )
    
#Lista pedidos utilizando filtros
@app.get("/orders", response_model=List[schemas.OrderResponse])
async def list_orders(
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None,
    order_id: Optional[int] = None,
    status: Optional[schemas.OrderStatusEnum] = None,
    client_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: models.Users = Depends(get_current_active_user)
):
    query = db.query(models.Order)
    
    if start_date:
        query = query.filter(models.Order.created_at >= start_date)
    if end_date:
        query = query.filter(models.Order.created_at <= end_date)
    if order_id:
        query = query.filter(models.Order.id == order_id)
    if status:
        query = query.filter(models.Order.status == status.value)
    if client_id:
        query = query.filter(models.Order.client_id == client_id)
    if category:
        query = query.join(models.Order.items).join(models.OrderItem.product).filter(models.Product.category == category)
    
    orders = query.offset(skip).limit(limit).all()
    return orders    

#pega um pedido especifico
@app.get("/orders/{order_id}", response_model=schemas.OrderResponse)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_active_user)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return order

#faz atualização no pedido
@app.put("/orders/{order_id}", response_model=schemas.OrderResponse)
async def update_order(
    order_id: int,
    order_update: schemas.OrderUpdate,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_active_user)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    db_status = convert_order_status(order_update.status.value)
    if order_update.status:
        order.status = db_status
    
    db.commit()
    db.refresh(order)
    return order

#Exclusão de pedidos. Só pode ser realizado por um superuser
@app.delete("/orders/{order_id}")
async def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.Users = Depends(get_current_superuser)
):
    try:
        # Verifica se já existe transação para não causar erro.
        if db.in_transaction():
            db.begin_nested()  # Usa savepoint se necessário
        else:
            db.begin()  # Inicia nova transação apenas se não existir
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        db_status = reverse_order_status(order.status)
        print(db_status)
        if db_status != schemas.OrderStatusEnum.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Só é possível cancelar pedidos pendentes"
            )
        
        # Devolve os itens ao estoque
        for item in order.items:
            product = db.query(models.Products).filter(models.Products.id == item.product_id).first()
            if product:
                product.stock += item.quantity
        db_status = convert_order_status(models.OrderStatus.CANCELLED.value)
        order.status = db_status
        db.commit()
    
        return {"message": "Pedido cancelado com sucesso"}
    
    except SQLAlchemyError as e:
        db.rollback()  # Importante! caso dê erro ele não atualiza o banco.
        raise HTTPException(
            status_code=500,
            detail=f"Erro no banco de dados: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao processar o cancelemanto: {str(e)}"
        )
