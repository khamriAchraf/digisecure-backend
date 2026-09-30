from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone

class ApiKeyCreate(BaseModel):
    name: str
    role_id: Optional[int] = None
    expires_in_days: Optional[int] = None


class ApiKeyResponse(BaseModel):
    id: int
    raw_key: str

    class Config:
        orm_mode = True
