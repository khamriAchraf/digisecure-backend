from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class UserRef(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class GroupRef(BaseModel):
    id: int
    name: str
    type: Optional[str] = None

    class Config:
        from_attributes = True


class ComplianceEventBase(BaseModel):
    name: str
    description: Optional[str] = None
    frequency: Optional[str] = None
    next_due_date: Optional[date] = None
    last_done_date: Optional[date] = None
    notify: Optional[bool] = None
    remind_before_days: Optional[int] = None
    notes: Optional[str] = None


class ComplianceEventCreate(ComplianceEventBase):
    scope_id: int
    notify_user_ids: Optional[List[int]] = []
    notify_group_ids: Optional[List[int]] = []


class ComplianceEventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    next_due_date: Optional[date] = None
    last_done_date: Optional[date] = None
    notify: Optional[bool] = None
    remind_before_days: Optional[int] = None
    notes: Optional[str] = None
    notify_user_ids: Optional[List[int]] = None
    notify_group_ids: Optional[List[int]] = None


class ComplianceEvent(ComplianceEventBase):
    id: int
    scope_id: int
    notify_users: List[UserRef] = []
    notify_groups: List[GroupRef] = []

    class Config:
        from_attributes = True


class ComplianceEventList(BaseModel):
    id: int
    scope_id: int
    name: str
    description: Optional[str] = None
    frequency: Optional[str] = None
    next_due_date: Optional[date] = None
    last_done_date: Optional[date] = None
    notify: Optional[bool] = None
    remind_before_days: Optional[int] = None
    notify_user_count: int = 0
    notify_group_count: int = 0

    class Config:
        from_attributes = True
