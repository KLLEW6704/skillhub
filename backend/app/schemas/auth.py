from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class RegistrationRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal[UserRole.student, UserRole.requester]
    school: str | None = Field(default=None, max_length=120)
    college: str | None = Field(default=None, max_length=120)
    major: str | None = Field(default=None, max_length=120)
    grade: str | None = Field(default=None, max_length=30)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    role: UserRole
    school: str | None
    college: str | None
    major: str | None
    grade: str | None
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
