from pydantic import BaseModel, ConfigDict, Field

from app.schemas.skill import SkillResponse


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=80)
    avatar_url: str | None = Field(default=None, max_length=500)
    bio: str | None = Field(default=None, max_length=2000)
    organization_name: str | None = Field(default=None, max_length=120)
    organization_type: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=2000)


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    display_name: str
    avatar_url: str | None
    bio: str | None


class RequesterProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    organization_name: str
    organization_type: str | None
    description: str | None


class PublicStudentResponse(StudentProfileResponse):
    username: str
    school: str | None
    college: str | None
    major: str | None
    grade: str | None
    skills: list[SkillResponse]
