from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VerificationStatus(str, Enum):
    pending_human_review = "pending_human_review"
    verified = "verified"
    more_evidence = "more_evidence"
    rejected = "rejected"
    revoked = "revoked"


class SkillVerification(Base):
    __tablename__ = "skill_verifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_run_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_runs.id"), unique=True, index=True
    )
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), index=True)
    status: Mapped[VerificationStatus] = mapped_column(
        SqlEnum(VerificationStatus), default=VerificationStatus.pending_human_review
    )
    ai_result_snapshot: Mapped[str] = mapped_column(Text)
    human_result: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ReviewAssignment(Base):
    __tablename__ = "review_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    verification_id: Mapped[int] = mapped_column(
        ForeignKey("skill_verifications.id"), unique=True, index=True
    )
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    assigned_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    verification_id: Mapped[int] = mapped_column(
        ForeignKey("skill_verifications.id"), index=True
    )
    decided_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    from_status: Mapped[VerificationStatus] = mapped_column(SqlEnum(VerificationStatus))
    to_status: Mapped[VerificationStatus] = mapped_column(SqlEnum(VerificationStatus))
    reason: Mapped[str] = mapped_column(Text)
    before_result: Mapped[str] = mapped_column(Text)
    after_result: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class SkillCredential(Base):
    __tablename__ = "skill_credentials"
    __table_args__ = (UniqueConstraint("credential_number"), UniqueConstraint("verification_id"))

    id: Mapped[int] = mapped_column(primary_key=True)
    verification_id: Mapped[int] = mapped_column(
        ForeignKey("skill_verifications.id"), index=True
    )
    credential_number: Mapped[str] = mapped_column(String(50), index=True)
    qr_token: Mapped[str] = mapped_column(String(64), unique=True)
    issued_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[str | None] = mapped_column(Text)
