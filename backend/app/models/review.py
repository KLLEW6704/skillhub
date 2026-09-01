from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("project_id", "student_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    skill_score: Mapped[int] = mapped_column(Integer)
    communication_score: Mapped[int] = mapped_column(Integer)
    delivery_score: Mapped[int] = mapped_column(Integer)
    time_management_score: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
