import json
from datetime import date, datetime, timezone
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PositionCategory(str, Enum):
    design = "design"
    development = "development"
    data = "data"
    content = "content"
    operations = "operations"
    general = "general"


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class ProjectPosition(Base):
    __tablename__ = "project_positions"
    __table_args__ = (UniqueConstraint("project_id", "code", name="uq_project_position_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(60))
    title: Mapped[str] = mapped_column(String(100))
    category: Mapped[PositionCategory] = mapped_column(SqlEnum(PositionCategory), default=PositionCategory.general)
    description: Mapped[str] = mapped_column(Text)
    headcount: Mapped[int] = mapped_column(Integer, default=1)
    required_skills_json: Mapped[str] = mapped_column(Text, default="[]")
    deliverables: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    @property
    def required_skills(self) -> list[str]:
        return json.loads(self.required_skills_json or "[]")


class ProjectTask(Base):
    __tablename__ = "project_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    position_id: Mapped[int | None] = mapped_column(ForeignKey("project_positions.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(SqlEnum(TaskStatus), default=TaskStatus.todo, index=True)
    assignee_student_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    due_date: Mapped[date | None] = mapped_column(Date)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    position: Mapped[ProjectPosition | None] = relationship(lazy="joined")


class ProjectTaskEvent(Base):
    __tablename__ = "project_task_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("project_tasks.id", ondelete="CASCADE"), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    from_status: Mapped[TaskStatus] = mapped_column(SqlEnum(TaskStatus))
    to_status: Mapped[TaskStatus] = mapped_column(SqlEnum(TaskStatus))
    version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ProjectDraft(Base):
    __tablename__ = "project_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), index=True)

    @property
    def payload(self) -> dict:
        return json.loads(self.payload_json or "{}")
