from pydantic import BaseModel, ConfigDict, Field

from app.schemas.skill import SkillResponse
from app.schemas.portfolio import PortfolioResponse


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=80)
    avatar_url: str | None = Field(default=None, max_length=500)
    bio: str | None = Field(default=None, max_length=2000)
    school: str | None = Field(default=None, max_length=120)
    college: str | None = Field(default=None, max_length=120)
    major: str | None = Field(default=None, max_length=120)
    grade: str | None = Field(default=None, max_length=30)
    organization_name: str | None = Field(default=None, max_length=120)
    organization_type: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=2000)


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    display_name: str
    avatar_url: str | None
    bio: str | None
    school: str | None
    college: str | None
    major: str | None
    grade: str | None


class RequesterProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    organization_name: str
    organization_type: str | None
    description: str | None


class PublicStudentResponse(StudentProfileResponse):
    username: str
    skills: list[SkillResponse]
    portfolios: list[PortfolioResponse]
