from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logger import logger, request_id_ctx
from app.db.models.user import User
from app.db.session import get_db
from app.services.asset_service import AssetService
from app.services.auth_service import decode_access_token, get_user_by_id
from app.services.configuration_service import ConfigurationService
from app.services.group_service import GroupService
from app.services.table_config_service import TableConfigService
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
    logger.debug(f"User {user.id} authenticated")
    request_id = request_id_ctx.get() or "-"
    db.execute(text(f"SET LOCAL app.current_user_id = '{user.id}'"))
    db.execute(text(f"SET LOCAL app.request_id = '{request_id}'"))
    return user


def get_user_service(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserService:
    return UserService(db, current_user)


def get_group_service(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GroupService:
    return GroupService(db, current_user)


def get_configuration_service(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConfigurationService:
    return ConfigurationService(db, current_user)


def get_asset_service(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssetService:
    return AssetService(db, current_user)


def get_table_config_service(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TableConfigService:
    return TableConfigService(db, current_user)
