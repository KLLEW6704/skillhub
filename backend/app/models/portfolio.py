from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text)
    file_url: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class EvidenceVisibility(str, Enum):
    private = "private"
    project_only = "project_only"
    public = "public"


class PortfolioEvidence(Base):
    __tablename__ = "portfolio_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), unique=True, index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(50), default="other")
    creation_context: Mapped[str | None] = mapped_column(Text)
    personal_role: Mapped[str | None] = mapped_column(Text)
    process_description: Mapped[str | None] = mapped_column(Text)
    iteration_notes: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[EvidenceVisibility] = mapped_column(
        SqlEnum(EvidenceVisibility), default=EvidenceVisibility.private
    )
    ai_processing_consent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class PortfolioEvidenceSkill(Base):
    __tablename__ = "portfolio_evidence_skills"
    __table_args__ = (UniqueConstraint("evidence_id", "skill_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    evidence_id: Mapped[int] = mapped_column(
        ForeignKey("portfolio_evidence.id", ondelete="CASCADE"), index=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), index=True
    )
