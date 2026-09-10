from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.schemas.profile import (
    ProfileUpdate,
    PublicStudentResponse,
    RequesterProfileResponse,
    StudentProfileResponse,
)
from app.services.profiles import (
    get_or_create_profile,
    profile_to_response,
    public_student,
    update_profile,
)


router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=StudentProfileResponse | RequesterProfileResponse)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role in {UserRole.admin, UserRole.reviewer}:
        raise HTTPException(status_code=403, detail="管理员没有业务资料")
    profile = get_or_create_profile(db, current_user)
    return profile_to_response(current_user, profile)


@router.patch("/me", response_model=StudentProfileResponse | RequesterProfileResponse)
def patch_me(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role in {UserRole.admin, UserRole.reviewer}:
        raise HTTPException(status_code=403, detail="管理员没有业务资料")
    return update_profile(db, current_user, payload)


@router.get("/students", response_model=list[PublicStudentResponse])
def students(db: Session = Depends(get_db)) -> list[dict]:
    users = db.scalars(
        select(User).where(User.role == UserRole.student, User.is_active.is_(True))
    )
    return [public_student(db, user) for user in users]


@router.get("/students/{user_id}", response_model=PublicStudentResponse)
def student(user_id: int, db: Session = Depends(get_db)) -> dict:
    user = db.get(User, user_id)
    if user is None or user.role != UserRole.student or not user.is_active:
        raise HTTPException(status_code=404, detail="学生不存在")
    return public_student(db, user)
