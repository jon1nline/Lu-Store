from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
 
app = FastAPI()
models.Base.metadata.create_all(bind=engine)

class NewUser(BaseModel):
   email: str
   hashed_password: str
   name: str
   phone: str



def get_db():
   db = SessionLocal()
   try:
     yield db
   finally:
     db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.post("/createuser")
async def create_user(user: NewUser, db: db_dependency):
   db_newuser = models.Users(email=user.email,hashed_password=user.hashed_password,name=user.name,phone=user.phone)
   db.add(db_newuser)
   db.commit()
   db.refresh(db_newuser)
