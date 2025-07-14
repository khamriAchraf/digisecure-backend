from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.rate_limiting import limiter
from app.core.security import get_password_hash
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import (LogoutResponse, TokenRefresh, UserCreate,
                              UserLogin, UserResponse)
from app.services import auth_service
from app.utils.connection_logger import log_login_attempt, log_successful_login

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/register", response_model=UserResponse)
@limiter.limit("5/hour")
def register(request: Request, user_create: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_create.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user_create.password)
    # Find the super-admin role
    from app.db.models.role import Role

    super_admin_role = db.query(Role).filter_by(name="Super-Admin").first()
    if not super_admin_role:
        raise HTTPException(status_code=500, detail="Super-Admin role not found")
    new_user = User(
        email=user_create.email,
        username=user_create.username,
        full_name=user_create.full_name,
        hashed_password=hashed_password,
        language=user_create.language,
        theme=user_create.theme,
        status=user_create.status,
        location=user_create.location,
        phone=user_create.phone,
        secondary_phone=user_create.secondary_phone,
        timezone=user_create.timezone,
        valid_from=user_create.valid_from,
        valid_until=user_create.valid_until,
        administartive_number=user_create.administartive_number,
        roles=[super_admin_role],
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=UserLogin)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    logger.info(f"Login attempt: email={form_data.username}")
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        log_login_attempt(request=request, email=form_data.username, success=False)
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    log_successful_login(request, user, success=True)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    refresh_token = auth_service.create_refresh_token(
        data={"sub": str(user.id), "email": user.email},
        db=db,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    print(f"Access token: {access_token}")
    return UserLogin(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


from pydantic import BaseModel


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenRefresh)
@limiter.limit("10/minute")
def refresh_token(
    request: Request, body: RefreshTokenRequest, db: Session = Depends(get_db)
):
    # Decode and validate refresh token
    result = auth_service.decode_refresh_token(body.refresh_token, db)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id, token_id = result
    user = auth_service.get_user_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Mark the current token as used (for rotation)
    auth_service.mark_token_as_used(db, token_id)

    # Get client information for new token
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Create new tokens (rotation)
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    new_refresh_token = auth_service.create_refresh_token(
        data={"sub": str(user.id), "email": user.email},
        db=db,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    logger.info(
        f"Token refreshed for user {user.id}, old token {token_id} marked as used"
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout", response_model=LogoutResponse)
def logout(request: Request, refresh_token: str, db: Session = Depends(get_db)):
    """Logout and revoke refresh token"""
    success = auth_service.revoke_refresh_token(refresh_token, db)
    if success:
        logger.info(f"User logged out successfully, token revoked")
        return {"message": "Successfully logged out"}
    else:
        # Even if token is invalid, return success to avoid information leakage
        return {"message": "Successfully logged out"}


@router.post("/logout-all", response_model=LogoutResponse)
def logout_all_devices(
    request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """Logout from all devices by revoking all refresh tokens"""
    user_id = auth_service.decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    revoked_count = auth_service.revoke_all_user_refresh_tokens(int(user_id), db)
    logger.info(
        f"User {user_id} logged out from all devices, {revoked_count} tokens revoked"
    )
    return {
        "message": f"Successfully logged out from all devices ({revoked_count} sessions terminated)"
    }


@router.get("/me", response_model=UserResponse)
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user_id = auth_service.decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = auth_service.get_user_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
