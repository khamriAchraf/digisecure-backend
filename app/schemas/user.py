import enum
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr

from app.schemas.group import GroupResponse as Group
from app.schemas.role import RoleResponse as Role


class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    deleted = "deleted"


class UserRole(str, enum.Enum):
    super_admin = "Super-Admin"
    admin = "Admin"
    supervisor = "Supervisor"
    technician = "Technician"
    hotliner = "Hotliner"
    observer = "Observer"
    self_service = "Self-Service"


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleResponse(RoleBase):
    id: int
    is_builtin: Optional[bool] = False

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    language: Optional[str] = "en"
    theme: Optional[str] = "light"
    status: Optional[UserStatus] = UserStatus.active
    location: Optional[str] = None
    phone: Optional[str] = None
    secondary_phone: Optional[str] = None
    timezone: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    administartive_number: Optional[str] = None


class UserList(BaseModel):
    id: int
    username: str
    role: Role
    status: str


class UserCreate(UserBase):
    password: str
    role_id: Optional[int] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    language: Optional[str] = None
    theme: Optional[str] = None
    status: Optional[UserStatus] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    secondary_phone: Optional[str] = None
    timezone: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    administartive_number: Optional[str] = None
    role_id: Optional[int] = None


class UserInDBBase(UserBase):
    id: int
    valid_until: Optional[datetime] = None
    administartive_number: Optional[str] = None
    role: Optional[Role] = None
    groups: List[Group] = []

    class Config:
        from_attributes = True


class UserResponse(UserInDBBase):
    pass


class UserLogin(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenRefresh(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class LogoutResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    message: str
