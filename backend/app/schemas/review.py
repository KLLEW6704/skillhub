from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    skill_score: int = Field(ge=1, le=5)
    communication_score: int = Field(ge=1, le=5)
    delivery_score: int = Field(ge=1, le=5)
    time_management_score: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    reviewer_id: int
    student_id: int
    skill_score: int
    communication_score: int
    delivery_score: int
    time_management_score: int
    comment: str | None
    created_at: datetime


class ProjectValidationResponse(BaseModel):
    id: int
    project_id: int
    student_id: int
    requester_id: int
    project_title: str
    deliverables: str | None
    acceptance_criteria: str | None
    required_skills: list[str]
    outcome: str
    created_at: datetime
