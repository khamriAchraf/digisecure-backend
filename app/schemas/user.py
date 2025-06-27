import enum
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


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


class UserCreate(UserBase):
    password: str
    roles: Optional[List[int]] = None


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
    roles: Optional[List[int]] = None


class UserLogin(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class UserResponse(UserBase):
    id: int
    roles: List[RoleResponse] = []

    class Config:
        from_attributes = True
