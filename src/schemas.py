from pydantic import BaseModel, EmailStr

class User(BaseModel):
    name: str
    email: EmailStr
    role: str
    password: str

class Login(BaseModel):
    email: EmailStr
    password: str

class Job(BaseModel):
    title: str
    description: str
    field: str
    pay: str
    currency: str