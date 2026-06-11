from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User as UserModel, RoleEnum, VolunteerProfile
from ..schemas import UserCreate, Token, User
from ..auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user
)
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=User)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(UserModel).filter(UserModel.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = UserModel(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        name=user_data.name,
        role=user_data.role,
        phone=user_data.phone,
        email=user_data.email
    )
    db.add(user)
    db.flush()

    if user_data.role == RoleEnum.VOLUNTEER:
        profile = VolunteerProfile(
            user_id=user.id,
            real_name=user_data.name,
            phone=user_data.phone
        )
        db.add(profile)

    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role.value},
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=User.model_validate(user)
    )


@router.get("/me", response_model=User)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
