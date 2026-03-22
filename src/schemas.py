from pydantic import BaseModel, EmailStr

class User(BaseModel):
    name: str
    email: EmailStr
    role: str
    password: str

class Product(BaseModel):
    image_id: str
    user_id: str
    post_url: str
    caption: str
    product_type: str
    price: int
    availability: int
    sold: int

class Login(BaseModel):
    email: EmailStr
    password: str