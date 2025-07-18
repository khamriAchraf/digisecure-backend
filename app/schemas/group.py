from typing import List, Optional

from pydantic import BaseModel, Field


class GroupBase(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Group name (must be unique)"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Optional description of the group"
    )
    type: Optional[str] = Field(
        None, description="Type of group (e.g., 'skill', 'org', 'notification')"
    )
    contain_users: Optional[bool] = Field(
        True, description="Whether this group can contain user members"
    )
    contain_items: Optional[bool] = Field(
        True, description="Whether this group can contain asset items"
    )
    comment: Optional[str] = Field(
        None, max_length=1000, description="Optional comments about the group"
    )
    parent_id: Optional[int] = Field(
        None, description="Parent group ID if this is a subgroup"
    )


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
