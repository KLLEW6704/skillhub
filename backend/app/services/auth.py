from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegistrationRequest
from app.services.profiles import create_profile_for_user


def register_user(db: Session, payload: RegistrationRequest) -> User | None:
    existing = db.scalar(
        select(User).where(
            or_(User.username == payload.username, User.email == payload.email)
        )
    )
    if existing:
        return None
    user = User(
        **payload.model_dump(exclude={"password"}),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()
    create_profile_for_user(db, user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
