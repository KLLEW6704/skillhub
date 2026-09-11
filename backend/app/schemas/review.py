from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReviewCreate(BaseModel):
    skill_score: int | None = Field(default=None, ge=1, le=5)
    communication_score: int | None = Field(default=None, ge=1, le=5)
    delivery_score: int | None = Field(default=None, ge=1, le=5)
    time_management_score: int | None = Field(default=None, ge=1, le=5)
    criteria_scores: dict[str, int] | None = None
    comment: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def require_complete_scores(self):
        legacy = [self.skill_score, self.communication_score, self.delivery_score, self.time_management_score]
        if self.criteria_scores is None and any(value is None for value in legacy):
            raise ValueError("请完整填写岗位评价")
        if self.criteria_scores is not None and any(not 1 <= value <= 5 for value in self.criteria_scores.values()):
            raise ValueError("评价分数必须在 1–5 之间")
        return self


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    reviewer_id: int
    student_id: int
    position_id: int | None
    rubric_category: str
    rubric_version: str
    criteria_scores: dict[str, int]
    project_title: str
    position_title: str | None
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
    position_title: str | None
    position_category: str | None
    rubric_version: str | None
    criteria_scores: dict[str, int]
    deliverables: str | None
    acceptance_criteria: str | None
    required_skills: list[str]
    outcome: str
    created_at: datetime
