from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.application import ApplicationStatus, InvitationStatus
from app.schemas.portfolio import PortfolioResponse
from app.schemas.project import ProjectResponse
from app.schemas.skill import SkillResponse
from app.models.verification import VerificationStatus


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


class AuthorizedPortfolioResponse(PortfolioResponse):
    ai_assessment: dict | None
    verification_status: VerificationStatus | None
    result_label: str | None


class RequesterApplicationResponse(ApplicationResponse):
    student: ApplicantSummary
    authorized_portfolios: list[AuthorizedPortfolioResponse]


class InvitationCreate(BaseModel):
    student_id: int = Field(gt=0)
    message: str | None = Field(default=None, max_length=1000)


class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    student_id: int
    inviter_id: int
    message: str | None
    status: InvitationStatus
    created_at: datetime
    viewed_at: datetime | None
    project: ProjectResponse
