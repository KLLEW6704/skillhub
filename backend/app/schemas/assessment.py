from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.assessment import AssessmentStage, AssessmentStatus


RUBRIC_CRITERIA = [
    "需求与场景理解",
    "信息层级与可读性",
    "视觉一致性与执行质量",
    "过程与迭代证据",
    "个人贡献与答辩解释",
]


class EvidencePointer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["image_region", "work_description", "defense_answer"]
    reference: str = Field(min_length=1, max_length=500)


class ObservationEvidencePointer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["image_region", "work_description"]
    reference: str = Field(min_length=1, max_length=500)


class ObservableFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation: str = Field(min_length=1, max_length=1000)
    evidence: ObservationEvidencePointer


class QuestionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=1000)
    targets_gap: str = Field(min_length=1, max_length=500)


class ObservationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observable_facts: list[ObservableFact] = Field(min_length=1, max_length=20)
    evidence_gaps: list[str] = Field(min_length=1, max_length=20)
    questions: list[QuestionDraft] = Field(min_length=3, max_length=3)


class RubricEvidence(EvidencePointer):
    reason: str = Field(min_length=1, max_length=1000)


class RubricCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion: str
    score: int = Field(ge=0, le=4)
    evidence: list[RubricEvidence] = Field(min_length=1, max_length=12)


class RubricResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criteria: list[RubricCriterion] = Field(min_length=5, max_length=5)

    @model_validator(mode="after")
    def validate_fixed_criteria(self):
        if [item.criterion for item in self.criteria] != RUBRIC_CRITERIA:
            raise ValueError("量表维度或顺序不符合 visual-poster-v1")
        return self


class DefenseAnswer(BaseModel):
    question_id: int
    answer: str = Field(min_length=1, max_length=6000)


class DefenseAnswers(BaseModel):
    answers: list[DefenseAnswer] = Field(min_length=3, max_length=3)


class DefenseQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    text: str
    targets_gap: str
    answer: str | None
    answered_at: datetime | None


class StatusEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: AssessmentStatus | None
    to_status: AssessmentStatus
    detail: str | None
    created_at: datetime


class AssessmentRunResponse(BaseModel):
    id: int
    run_number: str
    portfolio_id: int
    student_id: int
    stage: AssessmentStage
    status: AssessmentStatus
    model: str
    rubric_version: str
    input_summary: dict
    structured_result: dict | None
    error: str | None
    source_run_id: int | None
    retry_of_id: int | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    questions: list[DefenseQuestionResponse]
    status_history: list[StatusEventResponse]
    result_label: str = "AI 辅助初评、待人工复核"
