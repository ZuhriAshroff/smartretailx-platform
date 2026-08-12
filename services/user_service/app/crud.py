from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User
from libs.common.security import hash_password


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create_user(db: Session, email: str, password: str, full_name: str, role: str = "customer") -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, page: int, page_size: int) -> tuple[list[User], int]:
    total = db.execute(select(func.count()).select_from(User)).scalar_one()
    items = (
        db.execute(select(User).order_by(User.id).offset((page - 1) * page_size).limit(page_size))
        .scalars()
        .all()
    )
    return items, total


def update_user_role(db: Session, user: User, role: str) -> User:
    user.role = role
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
