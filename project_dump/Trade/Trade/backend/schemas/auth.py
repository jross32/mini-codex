from pydantic import BaseModel, EmailStr

class UserSignUp(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    
    class Config:
        from_attributes = True

class AuthToken(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
