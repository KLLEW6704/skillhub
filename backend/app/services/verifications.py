import json
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentRun, DefenseQuestion
from app.models.portfolio import Portfolio, PortfolioEvidence
from app.models.user import User, UserRole
from app.models.verification import (
    ReviewAssignment,
    ReviewDecision,
    SkillCredential,
    SkillVerification,
    VerificationStatus,
)
from app.schemas.verification import ReviewDecisionCreate
from app.services.portfolios import portfolio_to_response
from app.services.rubrics import EVIDENCE_RUBRIC_WEIGHTS, evidence_rubric


def create_pending_verification(db: Session, run: AssessmentRun, portfolio: Portfolio) -> SkillVerification:
    existing = db.scalar(
        select(SkillVerification).where(
            SkillVerification.assessment_run_id == run.id
        )
    )
    if existing is not None:
        return existing
    verification = SkillVerification(
        assessment_run_id=run.id,
        student_id=run.student_id,
        portfolio_id=run.portfolio_id,
        skill_id=portfolio.skill_id,
        status=VerificationStatus.pending_human_review,
        ai_result_snapshot=run.structured_result or "{}",
    )
    db.add(verification)
    return verification


def credential_to_response(credential: SkillCredential | None) -> dict | None:
    if credential is None:
        return None
    return {
        "name": "SkillHub 试行技能徽章",
        "credential_number": credential.credential_number,
        "qr_url": f"/api/v1/credentials/{credential.credential_number}/qr",
        "issued_at": credential.issued_at,
        "status": "revoked" if credential.revoked_at else "active",
    }


def verification_to_response(db: Session, verification: SkillVerification) -> dict:
    credential = db.scalar(
        select(SkillCredential).where(
            SkillCredential.verification_id == verification.id
        )
    )
    return {
        "id": verification.id,
        "assessment_run_id": verification.assessment_run_id,
        "student_id": verification.student_id,
        "portfolio_id": verification.portfolio_id,
        "skill_id": verification.skill_id,
        "status": verification.status,
        "human_result": (
            json.loads(verification.human_result) if verification.human_result else None
        ),
        "credential": credential_to_response(credential),
        "created_at": verification.created_at,
        "updated_at": verification.updated_at,
    }


def assign_reviewer(
    db: Session,
    admin: User,
    verification_id: int,
    reviewer_id: int,
) -> dict:
    verification = db.get(SkillVerification, verification_id)
    if verification is None:
        raise HTTPException(status_code=404, detail="人工复核记录不存在")
    if verification.status != VerificationStatus.pending_human_review:
        raise HTTPException(status_code=409, detail="当前状态不能分配评审")
    reviewer = db.get(User, reviewer_id)
    if reviewer is None or reviewer.role != UserRole.reviewer or not reviewer.is_active:
        raise HTTPException(status_code=422, detail="只能分配给已启用的评审用户")
    assignment = db.scalar(
        select(ReviewAssignment).where(
            ReviewAssignment.verification_id == verification.id
        )
    )
    if assignment is None:
        assignment = ReviewAssignment(
            verification_id=verification.id,
            reviewer_id=reviewer.id,
            assigned_by_id=admin.id,
        )
        db.add(assignment)
    else:
        assignment.reviewer_id = reviewer.id
        assignment.assigned_by_id = admin.id
        assignment.assigned_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assignment)
    return reviewer_assignment_to_response(db, assignment, verification)


def reviewer_assignment_to_response(
    db: Session, assignment: ReviewAssignment, verification: SkillVerification
) -> dict:
    run = db.get(AssessmentRun, verification.assessment_run_id)
    source = db.get(AssessmentRun, run.source_run_id) if run and run.source_run_id else None
    questions = (
        list(
            db.scalars(
                select(DefenseQuestion)
                .where(DefenseQuestion.assessment_run_id == source.id)
                .order_by(DefenseQuestion.position)
            )
        )
        if source
        else []
    )
    portfolio = db.get(Portfolio, verification.portfolio_id)
    evidence = db.scalar(
        select(PortfolioEvidence).where(
            PortfolioEvidence.portfolio_id == verification.portfolio_id
        )
    )
    portfolio_payload = portfolio_to_response(db, portfolio)
    portfolio_payload.update(
        {
            "creation_context": evidence.creation_context if evidence else None,
            "personal_role": evidence.personal_role if evidence else None,
            "process_description": evidence.process_description if evidence else None,
            "iteration_notes": evidence.iteration_notes if evidence else None,
        }
    )
    return {
        "assignment_id": assignment.id,
        "verification": verification_to_response(db, verification),
        "evidence": portfolio_payload,
        "defense": [
            {
                "question_id": question.id,
                "question": question.text,
                "answer": question.answer,
            }
            for question in questions
        ],
        "ai_result": json.loads(verification.ai_result_snapshot),
        "rubric_version": run.rubric_version,
    }


def reviewer_assignments(db: Session, reviewer: User) -> list[dict]:
    assignments = list(
        db.scalars(
            select(ReviewAssignment)
            .join(
                SkillVerification,
                SkillVerification.id == ReviewAssignment.verification_id,
            )
            .where(
                ReviewAssignment.reviewer_id == reviewer.id,
                SkillVerification.status == VerificationStatus.pending_human_review,
            )
            .order_by(ReviewAssignment.assigned_at.desc())
        )
    )
    return [
        reviewer_assignment_to_response(
            db, assignment, db.get(SkillVerification, assignment.verification_id)
        )
        for assignment in assignments
    ]


def decide_verification(
    db: Session,
    reviewer: User,
    verification_id: int,
    payload: ReviewDecisionCreate,
) -> dict:
    verification = db.get(SkillVerification, verification_id)
    assignment = db.scalar(
        select(ReviewAssignment).where(
            ReviewAssignment.verification_id == verification_id,
            ReviewAssignment.reviewer_id == reviewer.id,
        )
    )
    if verification is None or assignment is None:
        raise HTTPException(status_code=404, detail="复核任务不存在")
    if verification.status != VerificationStatus.pending_human_review:
        raise HTTPException(status_code=409, detail="复核任务已处理")
    before = json.loads(verification.ai_result_snapshot)
    after = deepcopy(before)
    if payload.adjusted_scores:
        by_name = {item["criterion"]: item for item in after["criteria"]}
        if not set(payload.adjusted_scores).issubset(by_name):
            raise HTTPException(status_code=422, detail="包含未知量表维度")
        for criterion, score in payload.adjusted_scores.items():
            by_name[criterion]["score"] = score
        portfolio = db.get(Portfolio, verification.portfolio_id)
        evidence = db.scalar(select(PortfolioEvidence).where(PortfolioEvidence.portfolio_id == portfolio.id))
        rubric = evidence_rubric(evidence.evidence_type if evidence else "")
        weights_list = EVIDENCE_RUBRIC_WEIGHTS.get(evidence.evidence_type if evidence else "", [20] * len(by_name))
        criteria = rubric[1] if rubric else list(by_name)
        weights = dict(zip(criteria, weights_list))
        total = sum(
            by_name[name]["score"] * weights[name] / 4
            for name in criteria
        )
        after["total_score"] = round(total, 1)
    after["review_status"] = payload.outcome.value
    after["human_review_reason"] = payload.reason
    decision = ReviewDecision(
        verification_id=verification.id,
        decided_by_id=reviewer.id,
        from_status=verification.status,
        to_status=payload.outcome,
        reason=payload.reason,
        before_result=json.dumps(before, ensure_ascii=False),
        after_result=json.dumps(after, ensure_ascii=False),
    )
    verification.status = payload.outcome
    verification.human_result = json.dumps(after, ensure_ascii=False)
    db.add(decision)
    if payload.outcome == VerificationStatus.verified:
        db.add(
            SkillCredential(
                verification_id=verification.id,
                credential_number=f"SH-PILOT-{datetime.now(timezone.utc):%Y}-{uuid4().hex[:10].upper()}",
                qr_token=uuid4().hex,
                issued_by_id=reviewer.id,
            )
        )
    db.commit()
    db.refresh(verification)
    return verification_to_response(db, verification)


def revoke_credential(
    db: Session, admin: User, credential_number: str, reason: str
) -> dict:
    credential = db.scalar(
        select(SkillCredential).where(
            SkillCredential.credential_number == credential_number
        )
    )
    if credential is None:
        raise HTTPException(status_code=404, detail="试行技能徽章不存在")
    verification = db.get(SkillVerification, credential.verification_id)
    if verification.status != VerificationStatus.verified or credential.revoked_at:
        raise HTTPException(status_code=409, detail="该试行技能徽章不能撤销")
    before = json.loads(verification.human_result or verification.ai_result_snapshot)
    after = deepcopy(before)
    after["review_status"] = VerificationStatus.revoked.value
    db.add(
        ReviewDecision(
            verification_id=verification.id,
            decided_by_id=admin.id,
            from_status=verification.status,
            to_status=VerificationStatus.revoked,
            reason=reason,
            before_result=json.dumps(before, ensure_ascii=False),
            after_result=json.dumps(after, ensure_ascii=False),
        )
    )
    verification.status = VerificationStatus.revoked
    verification.human_result = json.dumps(after, ensure_ascii=False)
    credential.revoked_at = datetime.now(timezone.utc)
    credential.revocation_reason = reason
    db.commit()
    db.refresh(verification)
    return verification_to_response(db, verification)


def public_credential(db: Session, credential_number: str) -> tuple[SkillCredential, dict]:
    credential = db.scalar(
        select(SkillCredential).where(
            SkillCredential.credential_number == credential_number
        )
    )
    if credential is None:
        raise HTTPException(status_code=404, detail="试行技能徽章不存在")
    verification = db.get(SkillVerification, credential.verification_id)
    run = db.get(AssessmentRun, verification.assessment_run_id)
    issuer = db.get(User, credential.issued_by_id)
    portfolio = db.get(Portfolio, verification.portfolio_id)
    evidence = db.scalar(
        select(PortfolioEvidence).where(
            PortfolioEvidence.portfolio_id == portfolio.id
        )
    )
    result = json.loads(verification.human_result or verification.ai_result_snapshot)
    ai_result = json.loads(verification.ai_result_snapshot)
    return credential, {
        "name": "SkillHub 试行技能徽章",
        "credential_number": credential.credential_number,
        "status": "revoked" if credential.revoked_at else "active",
        "rubric_version": run.rubric_version,
        "issuer": issuer.username,
        "issued_at": credential.issued_at,
        "revoked_at": credential.revoked_at,
        "evidence_summary": {
            "portfolio_id": portfolio.id,
            "title": portfolio.title,
            "evidence_type": evidence.evidence_type if evidence else "other",
        },
        "ai_result": ai_result,
        "verified_result": result,
    }
