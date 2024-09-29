from pydantic import BaseModel

class UserRegistration(BaseModel):
    login: str
    password: str