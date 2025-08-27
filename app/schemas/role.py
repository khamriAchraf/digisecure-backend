from typing import List, Optional

from pydantic import BaseModel


class PermissionResponse(BaseModel):
    id: int
    action: str
    resource: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    is_builtin: Optional[bool] = False


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[int]] = None


class RoleResponse(RoleBase):
    id: int
    is_builtin: Optional[bool] = False
    rank: int
    permissions: List[PermissionResponse] = []

    class Config:
        from_attributes = True
