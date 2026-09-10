from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_user, require_roles
from app.core.config import Settings
from app.models.application import Application, ApplicationPortfolioGrant
from app.models.portfolio import EvidenceVisibility, Portfolio, PortfolioEvidence
from app.models.project import Project
from app.models.verification import ReviewAssignment, SkillVerification
from app.models.user import User, UserRole
from app.schemas.portfolio import PortfolioResponse, PortfolioUpdate
from app.services.portfolios import (
    create_portfolio,
    delete_portfolio,
    portfolio_to_response,
    update_portfolio,
)
from app.services.uploads import upload_path


router = APIRouter(prefix="/portfolios", tags=["portfolios"])
student_only = require_roles(UserRole.student)


@router.get("", response_model=list[PortfolioResponse])
def list_portfolios(
    current_user: User = Depends(student_only), db: Session = Depends(get_db)
) -> list[dict]:
    portfolios = list(
        db.scalars(select(Portfolio).where(Portfolio.user_id == current_user.id))
    )
    return [portfolio_to_response(db, item) for item in portfolios]


@router.post("", response_model=PortfolioResponse, status_code=201)
async def upload_portfolio(
    skill_id: int = Form(),
    title: str = Form(min_length=1, max_length=150),
    description: str | None = Form(default=None, max_length=2000),
    evidence_type: str = Form(default="other", min_length=1, max_length=50),
    creation_context: str | None = Form(default=None, max_length=4000),
    personal_role: str | None = Form(default=None, max_length=4000),
    process_description: str | None = Form(default=None, max_length=6000),
    iteration_notes: str | None = Form(default=None, max_length=6000),
    visibility: EvidenceVisibility = Form(default=EvidenceVisibility.private),
    related_skill_ids: list[int] = Form(default=[]),
    ai_processing_consent: bool = Form(default=False),
    file: UploadFile = File(),
    current_user: User = Depends(student_only),
    db: Session = Depends(get_db),
) -> dict:
    settings = Settings()
    return await create_portfolio(
        db,
        current_user,
        skill_id,
        title,
        description,
        file,
        settings.upload_dir,
        settings.max_upload_mb * 1024 * 1024,
        evidence_type=evidence_type,
        creation_context=creation_context,
        personal_role=personal_role,
        process_description=process_description,
        iteration_notes=iteration_notes,
        visibility=visibility,
        related_skill_ids=related_skill_ids or None,
        ai_processing_consent=ai_processing_consent,
    )


@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
def patch_portfolio(
    portfolio_id: int,
    payload: PortfolioUpdate,
    current_user: User = Depends(student_only),
    db: Session = Depends(get_db),
) -> dict:
    return update_portfolio(db, current_user, portfolio_id, payload)


@router.get("/{portfolio_id}/file")
def portfolio_file(
    portfolio_id: int,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    portfolio = db.get(Portfolio, portfolio_id)
    if portfolio is None:
        raise HTTPException(status_code=404, detail="作品文件不存在")
    evidence = db.scalar(
        select(PortfolioEvidence).where(
            PortfolioEvidence.portfolio_id == portfolio.id
        )
    )
    allowed = bool(
        evidence is not None and evidence.visibility == EvidenceVisibility.public
    )
    if current_user is not None:
        allowed = allowed or current_user.id == portfolio.user_id
        allowed = allowed or current_user.role == UserRole.admin
        if current_user.role == UserRole.requester:
            grant = db.scalar(
                select(ApplicationPortfolioGrant)
                .join(
                    Application,
                    Application.id == ApplicationPortfolioGrant.application_id,
                )
                .join(Project, Project.id == Application.project_id)
                .where(
                    ApplicationPortfolioGrant.portfolio_id == portfolio.id,
                    Project.creator_id == current_user.id,
                )
            )
            allowed = allowed or grant is not None
        if current_user.role == UserRole.reviewer:
            assignment = db.scalar(
                select(ReviewAssignment)
                .join(
                    SkillVerification,
                    SkillVerification.id == ReviewAssignment.verification_id,
                )
                .where(
                    ReviewAssignment.reviewer_id == current_user.id,
                    SkillVerification.portfolio_id == portfolio.id,
                )
            )
            allowed = allowed or assignment is not None
    if not allowed:
        raise HTTPException(status_code=404, detail="作品文件不存在")
    path = upload_path(Settings().upload_dir, portfolio.file_url)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="作品文件不存在")
    return FileResponse(path, media_type=portfolio.file_type, filename=path.name)


@router.delete("/{portfolio_id}", status_code=204)
def remove_portfolio(
    portfolio_id: int,
    current_user: User = Depends(student_only),
    db: Session = Depends(get_db),
) -> None:
    delete_portfolio(db, current_user, portfolio_id, Settings().upload_dir)
