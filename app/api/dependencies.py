from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.db.models.user import User
from app.db.session import get_db
from app.services.auth_service import decode_access_token, get_user_by_id
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    user = get_user_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    logger.debug(f"User {user.id} authenticated with token {token}")
    db.execute(text(f"SET LOCAL app.current_user_id = '{user.id}'"))
    return user


def get_user_service(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserService:
    return UserService(db, current_user)
