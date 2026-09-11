from datetime import datetime, timezone

import json

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("project_id", "student_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    position_id: Mapped[int | None] = mapped_column(ForeignKey("project_positions.id"), index=True)
    rubric_category: Mapped[str] = mapped_column(String(30), default="general")
    rubric_version: Mapped[str] = mapped_column(String(80), default="general-performance-v1")
    criteria_scores_json: Mapped[str] = mapped_column(Text, default="{}")
    skill_score: Mapped[int] = mapped_column(Integer)
    communication_score: Mapped[int] = mapped_column(Integer)
    delivery_score: Mapped[int] = mapped_column(Integer)
    time_management_score: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    project: Mapped["Project"] = relationship(lazy="joined")
    position: Mapped["ProjectPosition | None"] = relationship(lazy="joined")

    @property
    def criteria_scores(self) -> dict[str, int]:
        return json.loads(self.criteria_scores_json or "{}")

    @property
    def project_title(self) -> str:
        return self.project.title

    @property
    def position_title(self) -> str | None:
        return self.position.title if self.position else None
