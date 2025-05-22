from fastapi import FastAPI, HTTPException, Depends
from pydentic import BaseModel
from typing import List, Annotaded

app = FastApi()

class ChoiceBase(BaseModel):
    choice_text: str
    is_correct: bool

class QuestionBase(BaseModel):
    question_text: str
    choices: list(ChoiceBase)
