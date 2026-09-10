from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.application import ApplicationStatus
from app.schemas.portfolio import PortfolioResponse
from app.schemas.skill import SkillResponse


class ApplicationCreate(BaseModel):
    message: str | None = Field(default=None, max_length=2000)
    portfolio_ids: list[int] = Field(default_factory=list, max_length=12)


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    student_id: int
    message: str | None
    status: ApplicationStatus
    created_at: datetime


class ApplicantSummary(BaseModel):
    user_id: int
    display_name: str
    skills: list[SkillResponse]


class RequesterApplicationResponse(ApplicationResponse):
    student: ApplicantSummary
    authorized_portfolios: list[PortfolioResponse]
