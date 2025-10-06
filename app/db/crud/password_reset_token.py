from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import PasswordResetToken


def create_password_reset_token(
    db: Session,
    user_id: int,
    token_id: str,
    token_hash: str,
    expires_at: datetime,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> PasswordResetToken:
    """Create a new password reset token record"""
    reset_token = PasswordResetToken(
        user_id=user_id,
        token_id=token_id,
        token_hash=token_hash,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)
    return reset_token


def get_password_reset_token_by_id(
    db: Session, token_id: str
) -> Optional[PasswordResetToken]:
    """Get password reset token by token ID"""
    return (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_id == token_id)
        .first()
    )


def get_valid_password_reset_token(
    db: Session, token_id: str
) -> Optional[PasswordResetToken]:
    """Get a valid (not revoked, not expired, not used) password reset token"""
    now = datetime.now(timezone.utc)
    return (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_id == token_id,
            PasswordResetToken.is_revoked == False,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .first()
    )


def mark_password_reset_token_used(
    db: Session, token_id: str
) -> Optional[PasswordResetToken]:
    """Mark a password reset token as used (single-use)"""
    token = get_password_reset_token_by_id(db, token_id)
    if token:
        token.used_at = datetime.now(timezone.utc)  # type: ignore
        db.commit()
        db.refresh(token)
    return token


def revoke_password_reset_token(db: Session, token_id: str) -> bool:
    """Revoke a specific password reset token"""
    token = get_password_reset_token_by_id(db, token_id)
    if token:
        token.is_revoked = True  # type: ignore
        db.commit()
        return True
    return False


def revoke_all_user_password_reset_tokens(db: Session, user_id: int) -> int:
    """Revoke all active password reset tokens for a user (on new request)"""
    result = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.is_revoked == False,
        )
        .update({"is_revoked": True})
    )
    db.commit()
    return result


def cleanup_expired_password_reset_tokens(db: Session) -> int:
    """Remove expired password reset tokens from the database"""
    now = datetime.now(timezone.utc)
    result = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.expires_at < now)
        .delete()
    )
    db.commit()
    return result
