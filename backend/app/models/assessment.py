from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AssessmentStage(str, Enum):
    observation = "observation"
    reassessment = "reassessment"


class AssessmentStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class AssessmentRun(Base):
    __tablename__ = "assessment_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    stage: Mapped[AssessmentStage] = mapped_column(SqlEnum(AssessmentStage))
    status: Mapped[AssessmentStatus] = mapped_column(SqlEnum(AssessmentStatus))
    model: Mapped[str] = mapped_column(String(120))
    rubric_version: Mapped[str] = mapped_column(String(80), default="visual-poster-v1")
    input_summary: Mapped[str] = mapped_column(Text)
    raw_output: Mapped[str | None] = mapped_column(Text)
    structured_result: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    source_run_id: Mapped[int | None] = mapped_column(ForeignKey("assessment_runs.id"))
    retry_of_id: Mapped[int | None] = mapped_column(ForeignKey("assessment_runs.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AssessmentRunEvent(Base):
    __tablename__ = "assessment_run_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("assessment_runs.id"), index=True)
    from_status: Mapped[AssessmentStatus | None] = mapped_column(SqlEnum(AssessmentStatus))
    to_status: Mapped[AssessmentStatus] = mapped_column(SqlEnum(AssessmentStatus))
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class DefenseQuestion(Base):
    __tablename__ = "defense_questions"
    __table_args__ = (UniqueConstraint("assessment_run_id", "position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_run_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_runs.id"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    targets_gap: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
