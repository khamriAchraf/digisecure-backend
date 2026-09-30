from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.db.models.api_key import ApiKey
import secrets
from app.core.security import get_password_hash

def create_api_key(db: Session, owner_id: int, name: str, role_id: int, expires_at=None):
    raw_key = secrets.token_urlsafe(48)
    key_hash = get_password_hash(raw_key)
    api_key = ApiKey(
        name=name,
        key_hash=key_hash,
        role_id=role_id,
        owner_id=owner_id,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return raw_key, api_key.id
