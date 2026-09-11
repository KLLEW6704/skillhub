from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.verification import VerificationStatus


class ReviewAssignmentCreate(BaseModel):
    reviewer_id: int


class ReviewDecisionCreate(BaseModel):
    outcome: Literal[
        VerificationStatus.verified,
        VerificationStatus.more_evidence,
        VerificationStatus.rejected,
    ]
    reason: str = Field(min_length=2, max_length=4000)
    adjusted_scores: dict[str, int] = Field(default_factory=dict)

    @field_validator("adjusted_scores")
    @classmethod
    def validate_scores(cls, scores: dict[str, int]) -> dict[str, int]:
        if any(score < 0 or score > 4 for score in scores.values()):
            raise ValueError("人工调整分值必须在 0–4 之间")
        return scores

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, reason: str) -> str:
        reason = reason.strip()
        if len(reason) < 2:
            raise ValueError("人工决定必须填写理由")
        return reason


class RevocationCreate(BaseModel):
    reason: str = Field(min_length=2, max_length=4000)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, reason: str) -> str:
        reason = reason.strip()
        if len(reason) < 2:
            raise ValueError("撤销必须填写理由")
        return reason


class CredentialResponse(BaseModel):
    name: str = "SkillHub 试行技能徽章"
    credential_number: str
    qr_url: str
    issued_at: datetime
    status: Literal["active", "revoked"]


class VerificationResponse(BaseModel):
    id: int
    assessment_run_id: int
    student_id: int
    portfolio_id: int
    skill_id: int
    status: VerificationStatus
    human_result: dict | None
    credential: CredentialResponse | None
    created_at: datetime
    updated_at: datetime


class ReviewerAssignmentResponse(BaseModel):
    assignment_id: int
    verification: VerificationResponse
    evidence: dict
    defense: list[dict]
    ai_result: dict
    rubric_version: str


class PublicCredentialResponse(BaseModel):
    name: str = "SkillHub 试行技能徽章"
    credential_number: str
    status: Literal["active", "revoked"]
    rubric_version: str
    issuer: str
    issued_at: datetime
    revoked_at: datetime | None
    evidence_summary: dict
    ai_result: dict
    verified_result: dict
