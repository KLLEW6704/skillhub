from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.application import Application
from app.models.project import AuditStatus, LifecycleStatus, Project
from app.models.user import User, UserRole
from app.schemas.admin import AdminStats, UserRoleUpdate, UserStatusUpdate
from app.schemas.auth import UserResponse
from app.schemas.project import ProjectResponse
from app.services.projects import audit_project


router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_roles(UserRole.admin)


@router.get("/stats", response_model=AdminStats)
def stats(_: User = Depends(admin_only), db: Session = Depends(get_db)):
    return {"users": db.scalar(select(func.count(User.id))) or 0, "projects": db.scalar(select(func.count(Project.id))) or 0, "applications": db.scalar(select(func.count(Application.id))) or 0, "completed_projects": db.scalar(select(func.count(Project.id)).where(Project.lifecycle_status == LifecycleStatus.completed)) or 0}


@router.get("/users", response_model=list[UserResponse])
def users(_: User = Depends(admin_only), db: Session = Depends(get_db)):
    return list(db.scalars(select(User)))


@router.patch("/users/{user_id}/status", response_model=UserResponse)
def user_status(user_id: int, payload: UserStatusUpdate, current: User = Depends(admin_only), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current.id and not payload.is_active:
        raise HTTPException(status_code=409, detail="不能停用当前管理员")
    user.is_active = payload.is_active
    db.commit(); db.refresh(user)
    return user


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def user_role(user_id: int, payload: UserRoleUpdate, current: User = Depends(admin_only), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current.id:
        raise HTTPException(status_code=409, detail="不能修改当前管理员角色")
    user.role = payload.role
    db.commit(); db.refresh(user)
    return user


@router.get("/projects", response_model=list[ProjectResponse])
def projects(_: User = Depends(admin_only), db: Session = Depends(get_db)):
    return list(db.scalars(select(Project)))


@router.post("/projects/{project_id}/approve", response_model=ProjectResponse)
def approve(project_id: int, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    return audit_project(db, project_id, AuditStatus.approved)


@router.post("/projects/{project_id}/reject", response_model=ProjectResponse)
def reject(project_id: int, _: User = Depends(admin_only), db: Session = Depends(get_db)):
    return audit_project(db, project_id, AuditStatus.rejected)
