from typing import Literal

from pydantic import BaseModel

from app.models.user import UserRole


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserRoleUpdate(BaseModel):
    role: Literal[UserRole.student, UserRole.requester, UserRole.reviewer]


class AdminStats(BaseModel):
    users: int
    projects: int
    applications: int = 0
    completed_projects: int
