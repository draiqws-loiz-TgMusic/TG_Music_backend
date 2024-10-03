from pydantic import BaseModel

class UserRegistration(BaseModel):
    login: str
    password: str

class Music_play(BaseModel):
    name : str
    author : str
    genre : str
    src : str

class Genre(BaseModel):
    genre : str

class Name(BaseModel):
    name: str