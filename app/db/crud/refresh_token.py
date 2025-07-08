from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import RefreshToken


def create_refresh_token(
    db: Session,
    user_id: int,
    token_id: str,
    token_hash: str,
    expires_at: datetime,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> RefreshToken:
    """Create a new refresh token record"""
    refresh_token = RefreshToken(
        user_id=user_id,
        token_id=token_id,
        token_hash=token_hash,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token


def get_refresh_token_by_id(db: Session, token_id: str) -> Optional[RefreshToken]:
    """Get refresh token by JWT ID"""
    return db.query(RefreshToken).filter(RefreshToken.token_id == token_id).first()


def get_valid_refresh_token(db: Session, token_id: str) -> Optional[RefreshToken]:
    """Get a valid (not revoked, not expired) refresh token"""
    now = datetime.utcnow()
    return (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_id == token_id,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > now,
        )
        .first()
    )


def mark_token_as_used(db: Session, token_id: str) -> Optional[RefreshToken]:
    """Mark a refresh token as used (for rotation)"""
    token = get_refresh_token_by_id(db, token_id)
    if token:
        token.used_at = datetime.now(timezone.utc)  # type: ignore
        db.commit()
        db.refresh(token)
    return token


def revoke_token(db: Session, token_id: str) -> bool:
    """Revoke a specific refresh token"""
    token = get_refresh_token_by_id(db, token_id)
    if token:
        token.is_revoked = True  # type: ignore
        db.commit()
        return True
    return False


def revoke_all_user_tokens(db: Session, user_id: int) -> int:
    """Revoke all refresh tokens for a specific user"""
    result = (
        db.query(RefreshToken)
        .filter(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
        .update({"is_revoked": True})
    )
    db.commit()
    return result


def cleanup_expired_tokens(db: Session) -> int:
    """Remove expired tokens from the database"""
    now = datetime.utcnow()
    result = db.query(RefreshToken).filter(RefreshToken.expires_at < now).delete()
    db.commit()
    return result


def get_user_active_tokens(db: Session, user_id: int) -> list[RefreshToken]:
    """Get all active (not revoked, not expired) tokens for a user"""
    now = datetime.utcnow()
    return (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > now,
        )
        .all()
    )
