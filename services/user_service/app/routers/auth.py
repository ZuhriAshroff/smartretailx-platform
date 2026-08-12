import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.events import publish_user_registered
from app.schemas import LoginRequest, TokenResponse, UserPublic, UserRegister
from libs.common.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, verify_password

logger = logging.getLogger("user_service.auth")
router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """Public self-registration. Always creates a 'customer' role account."""
    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = crud.create_user(db, payload.email, payload.password, payload.full_name, role="customer")

    try:
        publish_user_registered(user.id, user.email, user.full_name, user.role)
    except Exception:
        logger.exception("Failed to publish user.registered event for user %s", user.id)

    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    token = create_access_token(user.id, user.email, user.role)
    return TokenResponse(access_token=token, expires_in_minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
