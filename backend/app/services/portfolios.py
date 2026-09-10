from datetime import datetime, timezone
import json
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.portfolio import (
    EvidenceVisibility,
    Portfolio,
    PortfolioDraft,
    PortfolioEvidence,
    PortfolioEvidenceSkill,
)
from app.models.application import ApplicationPortfolioGrant
from app.models.assessment import AssessmentRun
from app.models.skill import Skill
from app.models.user import User
from app.services.uploads import IMAGE_FORMATS, remove_upload, save_upload
from app.services.growth import recalculate_skill


def _draft_skill_ids(
    db: Session, user: User, skill_id: int | None, related_skill_ids: list[int]
) -> list[int]:
    unique_ids = list(dict.fromkeys(related_skill_ids))
    requested_ids = set(unique_ids)
    if skill_id is not None:
        requested_ids.add(skill_id)
    if requested_ids:
        owned_ids = set(
            db.scalars(
                select(Skill.id).where(
                    Skill.user_id == user.id, Skill.id.in_(requested_ids)
                )
            )
        )
        if owned_ids != requested_ids:
            raise HTTPException(status_code=404, detail="关联技能不存在")
    return unique_ids


def draft_to_response(draft: PortfolioDraft) -> dict:
    try:
        related_skill_ids = json.loads(draft.related_skill_ids_json)
    except (TypeError, ValueError):
        related_skill_ids = []
    return {
        "id": draft.id,
        "user_id": draft.user_id,
        "skill_id": draft.skill_id,
        "title": draft.title,
        "description": draft.description,
        "evidence_type": draft.evidence_type,
        "creation_context": draft.creation_context,
        "personal_role": draft.personal_role,
        "process_description": draft.process_description,
        "iteration_notes": draft.iteration_notes,
        "visibility": draft.visibility,
        "related_skill_ids": related_skill_ids,
        "ai_processing_consent": draft.ai_processing_consent,
        "created_at": draft.created_at,
        "updated_at": draft.updated_at,
    }


def create_portfolio_draft(db: Session, user: User, payload) -> dict:
    values = payload.model_dump()
    related_skill_ids = _draft_skill_ids(
        db, user, values.get("skill_id"), values.pop("related_skill_ids")
    )
    draft = PortfolioDraft(
        user_id=user.id,
        related_skill_ids_json=json.dumps(related_skill_ids),
        **values,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft_to_response(draft)


def update_portfolio_draft(
    db: Session, user: User, draft_id: int, payload
) -> dict:
    draft = db.scalar(
        select(PortfolioDraft).where(
            PortfolioDraft.id == draft_id, PortfolioDraft.user_id == user.id
        )
    )
    if draft is None:
        raise HTTPException(status_code=404, detail="草稿不存在")
    values = payload.model_dump(exclude_unset=True)
    try:
        current_related_skill_ids = json.loads(draft.related_skill_ids_json)
    except (TypeError, ValueError):
        current_related_skill_ids = []
    supplied_related_skill_ids = values.pop("related_skill_ids", None)
    related_skill_ids = _draft_skill_ids(
        db,
        user,
        values.get("skill_id", draft.skill_id),
        supplied_related_skill_ids
        if supplied_related_skill_ids is not None
        else current_related_skill_ids,
    )
    for field, value in values.items():
        setattr(draft, field, value)
    if supplied_related_skill_ids is not None:
        draft.related_skill_ids_json = json.dumps(related_skill_ids)
    draft.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(draft)
    return draft_to_response(draft)


def delete_portfolio_draft(db: Session, user: User, draft_id: int) -> None:
    draft = db.scalar(
        select(PortfolioDraft).where(
            PortfolioDraft.id == draft_id, PortfolioDraft.user_id == user.id
        )
    )
    if draft is None:
        raise HTTPException(status_code=404, detail="草稿不存在")
    db.delete(draft)
    db.commit()


def _evidence_for(db: Session, portfolio_id: int) -> PortfolioEvidence | None:
    return db.scalar(
        select(PortfolioEvidence).where(PortfolioEvidence.portfolio_id == portfolio_id)
    )


def portfolio_to_response(db: Session, portfolio: Portfolio) -> dict:
    evidence = _evidence_for(db, portfolio.id)
    related_skill_ids = (
        list(
            db.scalars(
                select(PortfolioEvidenceSkill.skill_id).where(
                    PortfolioEvidenceSkill.evidence_id == evidence.id
                )
            )
        )
        if evidence
        else [portfolio.skill_id]
    )
    extension = Path(portfolio.file_url).suffix.lower()
    return {
        "id": portfolio.id,
        "user_id": portfolio.user_id,
        "skill_id": portfolio.skill_id,
        "title": portfolio.title,
        "description": portfolio.description,
        "file_url": f"/api/v1/portfolios/{portfolio.id}/file",
        "file_type": portfolio.file_type,
        "evidence_type": evidence.evidence_type if evidence else "other",
        "creation_context": evidence.creation_context if evidence else None,
        "personal_role": evidence.personal_role if evidence else None,
        "process_description": evidence.process_description if evidence else None,
        "iteration_notes": evidence.iteration_notes if evidence else None,
        "visibility": evidence.visibility if evidence else EvidenceVisibility.private,
        "related_skill_ids": related_skill_ids,
        "ai_processing_consent_at": (
            evidence.ai_processing_consent_at if evidence else None
        ),
        "ai_supported": extension in IMAGE_FORMATS,
        "created_at": portfolio.created_at,
    }


def _replace_related_skills(
    db: Session,
    evidence: PortfolioEvidence,
    user: User,
    skill_ids: list[int],
) -> None:
    unique_ids = list(dict.fromkeys(skill_ids))
    owned_ids = set(
        db.scalars(
            select(Skill.id).where(Skill.user_id == user.id, Skill.id.in_(unique_ids))
        )
    )
    if owned_ids != set(unique_ids):
        raise HTTPException(status_code=404, detail="关联技能不存在")
    existing = list(
        db.scalars(
            select(PortfolioEvidenceSkill).where(
                PortfolioEvidenceSkill.evidence_id == evidence.id
            )
        )
    )
    for item in existing:
        db.delete(item)
    for skill_id in unique_ids:
        db.add(PortfolioEvidenceSkill(evidence_id=evidence.id, skill_id=skill_id))


async def create_portfolio(
    db: Session,
    user: User,
    skill_id: int,
    title: str,
    description: str | None,
    file: UploadFile,
    upload_dir: Path,
    max_bytes: int,
    *,
    evidence_type: str = "other",
    creation_context: str | None = None,
    personal_role: str | None = None,
    process_description: str | None = None,
    iteration_notes: str | None = None,
    visibility: EvidenceVisibility = EvidenceVisibility.private,
    related_skill_ids: list[int] | None = None,
    ai_processing_consent: bool = False,
    draft_id: int | None = None,
) -> dict:
    skill = db.scalar(
        select(Skill).where(Skill.id == skill_id, Skill.user_id == user.id)
    )
    if skill is None:
        raise HTTPException(status_code=404, detail="技能不存在")
    draft = None
    if draft_id is not None:
        draft = db.scalar(
            select(PortfolioDraft).where(
                PortfolioDraft.id == draft_id, PortfolioDraft.user_id == user.id
            )
        )
        if draft is None:
            raise HTTPException(status_code=404, detail="草稿不存在")
    stored_name = await save_upload(file, upload_dir, max_bytes)
    portfolio = Portfolio(
        user_id=user.id,
        skill_id=skill.id,
        title=title,
        description=description,
        file_url=f"/uploads/{stored_name}",
        file_type=file.content_type or "application/octet-stream",
    )
    try:
        db.add(portfolio)
        db.flush()
        evidence = PortfolioEvidence(
            portfolio_id=portfolio.id,
            evidence_type=evidence_type,
            creation_context=creation_context,
            personal_role=personal_role,
            process_description=process_description,
            iteration_notes=iteration_notes,
            visibility=visibility,
            ai_processing_consent_at=(
                datetime.now(timezone.utc) if ai_processing_consent else None
            ),
        )
        db.add(evidence)
        db.flush()
        _replace_related_skills(
            db, evidence, user, related_skill_ids or [skill.id]
        )
        if draft is not None:
            db.delete(draft)
        recalculate_skill(db, skill.id)
        db.commit()
        db.refresh(portfolio)
    except BaseException:
        remove_upload(upload_dir, portfolio.file_url)
        raise
    return portfolio_to_response(db, portfolio)


def update_portfolio(db: Session, user: User, portfolio_id: int, payload) -> dict:
    portfolio = db.scalar(
        select(Portfolio).where(
            Portfolio.id == portfolio_id, Portfolio.user_id == user.id
        )
    )
    if portfolio is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    evidence = _evidence_for(db, portfolio.id)
    if evidence is None:
        evidence = PortfolioEvidence(portfolio_id=portfolio.id)
        db.add(evidence)
        db.flush()
    values = payload.model_dump(exclude_unset=True)
    related_skill_ids = values.pop("related_skill_ids", None)
    consent = values.pop("ai_processing_consent", None)
    for field in ("title", "description"):
        if field in values:
            setattr(portfolio, field, values.pop(field))
    for field, value in values.items():
        setattr(evidence, field, value)
    if consent is True:
        evidence.ai_processing_consent_at = datetime.now(timezone.utc)
    elif consent is False:
        evidence.ai_processing_consent_at = None
    if related_skill_ids is not None:
        if not related_skill_ids:
            raise HTTPException(status_code=422, detail="至少关联一项技能")
        _replace_related_skills(db, evidence, user, related_skill_ids)
    db.commit()
    db.refresh(portfolio)
    return portfolio_to_response(db, portfolio)


def delete_portfolio(
    db: Session, user: User, portfolio_id: int, upload_dir: Path
) -> None:
    portfolio = db.scalar(
        select(Portfolio).where(
            Portfolio.id == portfolio_id, Portfolio.user_id == user.id
        )
    )
    if portfolio is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    assessed = db.scalar(
        select(AssessmentRun.id).where(AssessmentRun.portfolio_id == portfolio.id)
    )
    if assessed is not None:
        raise HTTPException(
            status_code=409,
            detail="作品已有 AI 评估记录，不能删除；可改为仅自己可见",
        )
    file_url = portfolio.file_url
    skill_id = portfolio.skill_id
    evidence = _evidence_for(db, portfolio.id)
    grants = list(
        db.scalars(
            select(ApplicationPortfolioGrant).where(
                ApplicationPortfolioGrant.portfolio_id == portfolio.id
            )
        )
    )
    for grant in grants:
        db.delete(grant)
    if evidence is not None:
        links = list(
            db.scalars(
                select(PortfolioEvidenceSkill).where(
                    PortfolioEvidenceSkill.evidence_id == evidence.id
                )
            )
        )
        for link in links:
            db.delete(link)
        db.delete(evidence)
    db.delete(portfolio)
    db.flush()
    recalculate_skill(db, skill_id)
    db.commit()
    remove_upload(upload_dir, file_url)
