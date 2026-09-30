from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.security import APIKeyHeader
from app.core.logger import logger, request_id_ctx
from app.db.models.user import User
from app.db.models.api_key import ApiKey
from app.core.security import verify_password
from datetime import UTC, datetime

from app.db.session import get_db
from app.services.asset_service import AssetService
from app.services.auth_service import decode_access_token, get_user_by_id
from app.services.group_service import GroupService
from app.services.recycle_bin_service import RecycleBinService
from app.services.reference_data_service import ReferenceDataService
from app.services.schema_service import SchemaService
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

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_current_external_service(
    api_key: str = Depends(api_key_header), db: Session = Depends(get_db)
):
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    keys = db.query(ApiKey).filter(ApiKey.is_active == True).all()
    for db_key in keys:
        if verify_password(api_key, db_key.key_hash):
            if db_key.expires_at and db_key.expires_at < datetime.now(UTC):
                raise HTTPException(status_code=401, detail="API key expired")
            return db_key
    raise HTTPException(status_code=401, detail="Invalid API key")


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


def get_reference_data_service(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReferenceDataService:
    return ReferenceDataService(db, current_user)


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


def get_schema_service(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SchemaService:
    return SchemaService(db, current_user)


def get_recycle_bin_service(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecycleBinService:
    return RecycleBinService(db, current_user)
