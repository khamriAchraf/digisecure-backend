from datetime import datetime
from typing import List

from pydantic import BaseModel, constr


class TableConfigBase(BaseModel):
    table_key: constr(strip_whitespace=True, min_length=1, max_length=64)


class TableConfigCreate(TableConfigBase):
    columns: List[str]


class TableConfigUpdate(BaseModel):
    columns: List[str]


class TableConfigResponse(TableConfigBase):
    id: int
    user_id: int
    columns: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
