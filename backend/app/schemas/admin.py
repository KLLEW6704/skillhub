from pydantic import BaseModel


class UserStatusUpdate(BaseModel):
    is_active: bool


class AdminStats(BaseModel):
    users: int
    projects: int
    applications: int = 0
    completed_projects: int
