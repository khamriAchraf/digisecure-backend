import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import logger
from app.core.security import get_password_hash, verify_password
from app.db.crud import password_reset_token as password_reset_token_crud
from app.db.crud import refresh_token as refresh_token_crud
from app.db.models.user import User
from app.db.models.api_key import ApiKey

SECRET_KEY = settings.JWT_SECRET
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_EXPIRATION_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.JWT_REFRESH_EXPIRATION_DAYS
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _get_user_permissions(user: User) -> list[str]:
    """Extract user permissions in the format 'resource:action'"""
    permissions = []
    if user.role:
        for perm in user.role.permissions:
            permissions.append(f"{perm.resource}:{perm.action}")
    return permissions


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update(
        {"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"}
    )
    logger.debug(f"Creating access token for user {data.get('sub')}, expires={expire}")
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: dict,
    db: Session,
    expires_delta: Optional[timedelta] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    token_id = secrets.token_urlsafe(32)

    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": token_id,
            "type": "refresh",
        }
    )

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    token_hash = get_password_hash(encoded_jwt)
    refresh_token_crud.create_refresh_token(
        db=db,
        user_id=int(data["sub"]),
        token_id=token_id,
        token_hash=token_hash,
        expires_at=expire,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    logger.debug(f"Created refresh token {token_id} for user {data.get('sub')}")
    return encoded_jwt


def authenticate_user(db: Session, email: EmailStr, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"Failed authentication attempt for user {email}")
        return None
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            logger.warning("Token type is not 'access'")
            return None
        user_id: Any | None = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError as e:
        logger.warning(f"Access token verification failed: {str(e)}")
        return None


def decode_access_token_payload(token: str) -> Optional[dict]:
    """Decode access token and return full payload including role_id and permissions"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            logger.warning("Token type is not 'access'")
            return None
        return payload
    except JWTError as e:
        logger.warning(f"Access token verification failed: {str(e)}")
        return None


def decode_refresh_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            logger.warning("Token type is not 'refresh'")
            return None

        token_id = payload.get("jti")
        if not token_id:
            logger.warning("Refresh token missing JTI claim")
            return None

        # Check if token exists and is valid in database
        db_token = refresh_token_crud.get_valid_refresh_token(db, token_id)
        if not db_token:
            logger.warning(f"Refresh token {token_id} not found or invalid in database")
            return None

        user_id: Any | None = payload.get("sub")
        if user_id is None:
            return None

        return user_id, token_id
    except JWTError as e:
        logger.warning(f"Refresh token verification failed: {str(e)}")
        return None


def revoke_refresh_token(token: str, db: Session) -> bool:
    """Revoke a refresh token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_id = payload.get("jti")
        if token_id:
            return refresh_token_crud.revoke_token(db, token_id)
        return False
    except JWTError:
        return False


def revoke_all_user_refresh_tokens(user_id: int, db: Session) -> int:
    """Revoke all refresh tokens for a user"""
    return refresh_token_crud.revoke_all_user_tokens(db, user_id)


def mark_token_as_used(db: Session, token_id: str) -> Optional[Any]:
    """Mark a refresh token as used (for rotation tracking)"""
    return refresh_token_crud.mark_token_as_used(db, token_id)


def create_password_reset_token(
    db: Session,
    email: EmailStr,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Optional[str]:
    """
    Create a password reset token for a user.
    Returns the raw token string if user exists, None otherwise.
    Always succeeds silently to prevent account enumeration.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.info(f"Password reset requested for non-existent email: {email}")
        return None

    # Revoke all previous password reset tokens for this user
    password_reset_token_crud.revoke_all_user_password_reset_tokens(db, user.id)

    # Generate a random, high-entropy token
    token_id = secrets.token_urlsafe(32)
    raw_token = secrets.token_urlsafe(48)

    # Hash the token for storage
    token_hash = get_password_hash(raw_token)

    # Calculate expiration
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
    )

    # Store in database
    password_reset_token_crud.create_password_reset_token(
        db=db,
        user_id=user.id,
        token_id=token_id,
        token_hash=token_hash,
        expires_at=expire,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    logger.info(
        f"Password reset token created for user {user.id}, token_id={token_id}, expires={expire}"
    )
    return raw_token


def verify_password_reset_token(db: Session, token: str) -> Optional[User]:
    """
    Verify a password reset token and return the associated user.
    Returns None if token is invalid, expired, used, or revoked.
    """
    # Try to find a valid token by attempting to verify against all active tokens
    # Since we store hashed tokens, we need to check each one
    now = datetime.now(timezone.utc)
    active_tokens = (
        db.query(password_reset_token_crud.PasswordResetToken)
        .filter(
            password_reset_token_crud.PasswordResetToken.is_revoked == False,
            password_reset_token_crud.PasswordResetToken.used_at.is_(None),
            password_reset_token_crud.PasswordResetToken.expires_at > now,
        )
        .all()
    )

    for db_token in active_tokens:
        if verify_password(token, db_token.token_hash):
            # Token is valid, get the user
            user = get_user_by_id(db, db_token.user_id)
            if user:
                logger.debug(
                    f"Valid password reset token verified for user {user.id}, token_id={db_token.token_id}"
                )
                return user
            break

    logger.warning("Invalid or expired password reset token attempted")
    return None


def reset_user_password(db: Session, token: str, new_password: str) -> Optional[User]:
    """
    Reset a user's password using a valid reset token.
    Returns the user if successful, None otherwise.
    """
    # Verify token and get user
    user = verify_password_reset_token(db, token)
    if not user:
        return None

    # Hash the new password
    new_hashed_password = get_password_hash(new_password)

    # Update user password
    user.hashed_password = new_hashed_password  # type: ignore
    db.commit()
    db.refresh(user)

    # Mark the token as used
    now = datetime.now(timezone.utc)
    active_tokens = (
        db.query(password_reset_token_crud.PasswordResetToken)
        .filter(
            password_reset_token_crud.PasswordResetToken.user_id == user.id,
            password_reset_token_crud.PasswordResetToken.is_revoked == False,
            password_reset_token_crud.PasswordResetToken.used_at.is_(None),
            password_reset_token_crud.PasswordResetToken.expires_at > now,
        )
        .all()
    )

    for db_token in active_tokens:
        if verify_password(token, db_token.token_hash):
            password_reset_token_crud.mark_password_reset_token_used(
                db, db_token.token_id
            )
            break

    # Revoke all refresh tokens (logout from all devices)
    revoked_count = revoke_all_user_refresh_tokens(user.id, db)

    logger.info(
        f"Password reset successful for user {user.id}, revoked {revoked_count} refresh tokens"
    )
    return user


def create_api_key(db: Session, owner_id: int, name: str, expires_at=None):
    raw_key = secrets.token_urlsafe(48)
    key_hash = get_password_hash(raw_key)
    api_key = ApiKey(
        name=name,
        key_hash=key_hash,
        owner_id=owner_id,
        expires_at=expires_at,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return raw_key
