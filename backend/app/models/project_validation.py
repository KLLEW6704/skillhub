from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProjectValidationRecord(Base):
    __tablename__ = "project_validation_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), unique=True)
    project_title: Mapped[str] = mapped_column(String(150))
    position_title: Mapped[str | None] = mapped_column(String(100))
    position_category: Mapped[str | None] = mapped_column(String(30))
    rubric_version: Mapped[str | None] = mapped_column(String(80))
    criteria_scores_snapshot: Mapped[str | None] = mapped_column(Text)
    deliverables_snapshot: Mapped[str | None] = mapped_column(Text)
    acceptance_criteria_snapshot: Mapped[str | None] = mapped_column(Text)
    required_skills_snapshot: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(String(40), default="completed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
