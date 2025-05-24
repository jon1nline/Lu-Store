from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Annotated
import models, schemas
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from auth import (
    get_current_user,
    get_current_active_user,
    get_current_superuser,
    authenticate_user,
    create_access_token,
    get_password_hash,
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
def login_for_access_token(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/refresh-token")
async def root():
    return {"message": "will be activated after auth/login"}