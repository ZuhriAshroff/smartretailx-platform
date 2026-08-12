import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.events import publish_user_registered
from app.schemas import PaginatedUsers, RoleUpdate, UserAdminCreate, UserPublic
from libs.common.security import TokenPayload, get_current_user, require_roles

logger = logging.getLogger("user_service.users")
router = APIRouter(prefix="/v1/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
def get_my_profile(
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_id(db, int(current_user.sub))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("", response_model=PaginatedUsers)
def list_all_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: TokenPayload = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    items, total = crud.list_users(db, page, page_size)
    return PaginatedUsers(total=total, page=page, page_size=page_size, items=items)


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def create_user_as_admin(
    payload: UserAdminCreate,
    _admin: TokenPayload = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    """Admin-only creation endpoint that allows assigning any role.

    Used by the seed script to bootstrap admin/warehouse_staff accounts.
    """
    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = crud.create_user(db, payload.email, payload.password, payload.full_name, role=payload.role)

    try:
        publish_user_registered(user.id, user.email, user.full_name, user.role)
    except Exception:
        logger.exception("Failed to publish user.registered event for user %s", user.id)

    return user


@router.get("/{user_id}", response_model=UserPublic)
def get_user(
    user_id: int,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin" and int(current_user.sub) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted to view this user")
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}/role", response_model=UserPublic)
def change_user_role(
    user_id: int,
    payload: RoleUpdate,
    _admin: TokenPayload = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return crud.update_user_role(db, user, payload.role)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user(
    user_id: int,
    _admin: TokenPayload = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    crud.delete_user(db, user)
