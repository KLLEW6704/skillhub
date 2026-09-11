from datetime import date, datetime, timezone
from enum import Enum
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum as SqlEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class LifecycleStatus(str, Enum):
    recruiting = "recruiting"
    in_progress = "in_progress"
    awaiting_review = "awaiting_review"
    completed = "completed"
    closed = "closed"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(80), index=True)
    budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    deadline: Mapped[date] = mapped_column(Date, index=True)
    audit_status: Mapped[AuditStatus] = mapped_column(SqlEnum(AuditStatus), default=AuditStatus.pending)
    lifecycle_status: Mapped[LifecycleStatus] = mapped_column(SqlEnum(LifecycleStatus), default=LifecycleStatus.recruiting)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    skill_requirements: Mapped[list["ProjectRequiredSkill"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    delivery_requirements: Mapped["ProjectDeliveryRequirements | None"] = relationship(
        cascade="all, delete-orphan", lazy="selectin", uselist=False
    )
    positions: Mapped[list["ProjectPosition"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="ProjectPosition.sort_order"
    )
    tasks: Mapped[list["ProjectTask"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="ProjectTask.sort_order"
    )

    @property
    def required_skills(self) -> list[str]:
        return [item.skill_name for item in self.skill_requirements]

    @property
    def deliverables(self) -> str | None:
        return (
            self.delivery_requirements.deliverables
            if self.delivery_requirements
            else None
        )

    @property
    def acceptance_criteria(self) -> str | None:
        return (
            self.delivery_requirements.acceptance_criteria
            if self.delivery_requirements
            else None
        )


class ProjectRequiredSkill(Base):
    __tablename__ = "project_required_skills"

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    skill_name: Mapped[str] = mapped_column(String(80), primary_key=True)


class ProjectDeliveryRequirements(Base):
    __tablename__ = "project_delivery_requirements"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    deliverables: Mapped[str | None] = mapped_column(Text)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text)
