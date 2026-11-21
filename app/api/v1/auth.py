from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.rate_limiting import limiter
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import (ForgotPasswordRequest, ForgotPasswordResponse,
                              LogoutResponse, ResetPasswordRequest,
                              ResetPasswordResponse, TokenRefresh,
                              UserLogin, UserResponse)
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse
from app.services import auth_service
from app.services.email_service import send_password_reset_email
from app.utils.connection_logger import log_login_attempt, log_successful_login

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/register", response_model=UserResponse)
@limiter.limit("5/hour")
def register(request: Request):
    raise HTTPException(
        status_code=403,
        detail="Public registration is disabled. Contact an administrator.",
    )


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

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role_id": user.role.id if user.role else None,
        "permissions": auth_service._get_user_permissions(user),
    }

    access_token = auth_service.create_access_token(data=token_data)
    refresh_token = auth_service.create_refresh_token(
        data=token_data,
        db=db,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return UserLogin(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


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

    # Prepare token data with role_id and permissions
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role_id": user.role.id if user.role else None,
        "permissions": auth_service._get_user_permissions(user),
    }

    # Create new tokens (rotation)
    access_token = auth_service.create_access_token(data=token_data)
    new_refresh_token = auth_service.create_refresh_token(
        data=token_data,
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
def logout(
    request: Request,
    body: Optional[RefreshTokenRequest] = None,
    refresh_token: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Logout and revoke refresh token"""
    if body and refresh_token and body.refresh_token != refresh_token:
        raise HTTPException(
            status_code=422, detail="Conflicting refresh tokens were provided"
        )
    token_to_revoke = body.refresh_token if body else refresh_token
    if not token_to_revoke:
        raise HTTPException(status_code=422, detail="refresh_token is required")
    success = auth_service.revoke_refresh_token(token_to_revoke, db)
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


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit("3/hour")
def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Request a password reset token.
    Always returns success to prevent account enumeration.
    If the email exists, a reset token will be created and an email will be sent.
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Create token (returns None if user doesn't exist, but we don't tell the client)
    token = auth_service.create_password_reset_token(
        db=db,
        email=body.email,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Send email with reset link if user exists
    if token:
        # Get user info for personalization
        user = db.query(User).filter(User.email == body.email).first()
        user_full_name = user.full_name if user and user.full_name else None

        # Send password reset email via Java cron job service
        email_sent = send_password_reset_email(
            email=body.email,
            token=token,
            user_full_name=user_full_name,
        )

        if email_sent:
            logger.info(f"Password reset email scheduled for {body.email}")
        else:
            logger.error(f"Failed to schedule password reset email for {body.email}")
            # Don't fail the request - still return success to prevent enumeration

    # Always return the same response to prevent account enumeration
    return ForgotPasswordResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
@limiter.limit("5/hour")
def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Reset password using a valid reset token.
    """
    user = auth_service.reset_user_password(
        db=db,
        token=body.token,
        new_password=body.new_password,
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired password reset token",
        )

    logger.info(f"Password successfully reset for user {user.id}")
    return ResetPasswordResponse(
        message="Password successfully reset. All sessions have been logged out."
    )


@router.post("/api-key", response_model=ApiKeyCreate)
def create_api_key(
    request: Request,
    api_key_data: ApiKeyCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    user_id = auth_service.decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = auth_service.get_user_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    api_key = auth_service.create_api_key(api_key_data, user, db)