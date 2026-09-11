from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApplicationStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    finished = "finished"


class InvitationStatus(str, Enum):
    pending = "pending"
    viewed = "viewed"
    applied = "applied"


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("project_id", "student_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    position_id: Mapped[int | None] = mapped_column(ForeignKey("project_positions.id"), index=True)
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ApplicationStatus] = mapped_column(SqlEnum(ApplicationStatus), default=ApplicationStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    project: Mapped["Project"] = relationship(lazy="joined")
    position: Mapped["ProjectPosition | None"] = relationship(lazy="joined")


class ApplicationPortfolioGrant(Base):
    __tablename__ = "application_portfolio_grants"
    __table_args__ = (UniqueConstraint("application_id", "portfolio_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ProjectInvitation(Base):
    __tablename__ = "project_invitations"
    __table_args__ = (
        UniqueConstraint("project_id", "student_id", name="uq_project_invitation_student"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    position_id: Mapped[int | None] = mapped_column(ForeignKey("project_positions.id"), index=True)
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[InvitationStatus] = mapped_column(
        SqlEnum(InvitationStatus), default=InvitationStatus.pending, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    project: Mapped["Project"] = relationship(lazy="joined")
    position: Mapped["ProjectPosition | None"] = relationship(lazy="joined")
