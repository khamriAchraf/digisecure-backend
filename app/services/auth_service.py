import secrets
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import logger
from app.core.security import get_password_hash, verify_password
from app.db.crud import refresh_token as refresh_token_crud
from app.db.models.user import User

SECRET_KEY = settings.JWT_SECRET
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_EXPIRATION_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.JWT_REFRESH_EXPIRATION_DAYS

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})
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
    expire = datetime.utcnow() + (
        expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    token_id = secrets.token_urlsafe(32)

    to_encode.update(
        {"exp": expire, "iat": datetime.utcnow(), "jti": token_id, "type": "refresh"}
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
