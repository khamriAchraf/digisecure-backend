from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import can_access, get_password_hash, has_permission
from app.db.crud import api_key as api_key_crud
from app.db.models.user import User
from app.db.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse
from app.services.email_service import send_welcome_email

class PermissionError(Exception):
    pass


class ApiKeyService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
        
    def create_api_key(self, name: str, role_id: Optional[int] = None, expires_in_days: Optional[int] = None) -> Tuple[ApiKeyResponse, str]:
        logger.info(
            f"User {self.current_user.id} attempts to CREATE API key at {datetime.now(timezone.utc).isoformat()}"
        )
        if not has_permission(self.current_user, "create", "api_key"):
            logger.warning(
                f"User {self.current_user.id} denied CREATE access to API keys"
            )
            raise PermissionError("Not allowed to create API keys.")
        
        
        raw_key, id=api_key_crud.create_api_key(
            db=self.db,
            owner_id=self.current_user.id,
            name=name,
            role_id=role_id,
            expires_at=(datetime.now(timezone.utc) + timedelta(days=expires_in_days)) if expires_in_days else None
        )
        
        logger.info(f"User {self.current_user.id} successfully CREATED API key {id}")
        
        api_key_response = ApiKeyResponse(id, raw_key)
        
        return api_key_response