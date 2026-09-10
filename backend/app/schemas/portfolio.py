from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.portfolio import EvidenceVisibility


class PortfolioUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    evidence_type: str | None = Field(default=None, min_length=1, max_length=50)
    creation_context: str | None = Field(default=None, max_length=4000)
    personal_role: str | None = Field(default=None, max_length=4000)
    process_description: str | None = Field(default=None, max_length=6000)
    iteration_notes: str | None = Field(default=None, max_length=6000)
    visibility: EvidenceVisibility | None = None
    related_skill_ids: list[int] | None = Field(default=None, max_length=12)
    ai_processing_consent: bool | None = None


class PortfolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    skill_id: int
    title: str
    description: str | None
    file_url: str
    file_type: str
    evidence_type: str
    creation_context: str | None
    personal_role: str | None
    process_description: str | None
    iteration_notes: str | None
    visibility: EvidenceVisibility
    related_skill_ids: list[int]
    ai_processing_consent_at: datetime | None
    ai_supported: bool
    created_at: datetime
