from typing import List, Optional

from pydantic import BaseModel


class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: Optional[str] = None  # e.g., 'skill', 'org', 'notification'
    contain_users: Optional[bool] = True
    contain_items: Optional[bool] = True
    comment: Optional[str] = None
    parent_id: Optional[int] = None


class GroupCreate(GroupBase):
    pass


class GroupCreateWithUsers(GroupCreate):
    user_ids: list[int] = []


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    contain_users: Optional[bool] = None
    contain_items: Optional[bool] = None
    comment: Optional[str] = None
    parent_id: Optional[int] = None


class GroupUserResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class GroupResponse(GroupBase):
    id: int
    users: List[GroupUserResponse] = []

    class Config:
        from_attributes = True
