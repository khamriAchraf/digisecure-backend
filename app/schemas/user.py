from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True
