from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import get_password_hash
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services import auth_service

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/register", response_model=UserResponse)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
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
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    logger.info(f"Login attempt: username={form_data.username}")
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    refresh_token = auth_service.create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    return UserLogin(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    user_id = auth_service.decode_refresh_token(refresh_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = auth_service.get_user_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    access_token = auth_service.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user_id = auth_service.decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = auth_service.get_user_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
