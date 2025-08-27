from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("parent_id", mode="before")
    @classmethod
    def validate_parent_id(cls, v):
        if v is None:
            return v
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            if v.strip() == "":
                return None
            try:
                return int(v)
            except ValueError:
                raise ValueError(
                    "parent_id must be a valid integer or string that can be converted to integer"
                )
        raise ValueError("parent_id must be an integer, string, or None")


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

    @field_validator("parent_id", mode="before")
    @classmethod
    def validate_parent_id(cls, v):
        if v is None:
            return v
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            # Handle empty string as None
            if v.strip() == "":
                return None
            try:
                return int(v)
            except ValueError:
                raise ValueError(
                    "parent_id must be a valid integer or string that can be converted to integer"
                )
        raise ValueError("parent_id must be an integer, string, or None")


class GroupUserResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class GroupAssetResponse(BaseModel):
    id: int
    name: str
    type: str
    status: Optional[str] = None

    class Config:
        from_attributes = True


class GroupList(BaseModel):
    id: int
    name: str
    type: Optional[str] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    asset_count: int = 0
    user_count: int = 0


class GroupResponse(GroupBase):
    id: int
    users: List[GroupUserResponse] = []
    assets: List[GroupAssetResponse] = []

    class Config:
        from_attributes = True


class GroupListResponse(GroupBase):
    id: int
    user_count: int = 0
    asset_count: int = 0

    class Config:
        from_attributes = True
