from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.db.models.user import User
from app.db.session import get_db
from app.services.auth_service import decode_access_token, get_user_by_id
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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
    logger.info(f"User {user.id} authenticated with token {token}")
    return user


def get_user_service(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserService:
    return UserService(db, current_user)
