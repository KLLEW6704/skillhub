import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.application import Application, ApplicationPortfolioGrant, ApplicationStatus
from app.models.portfolio import Portfolio
from app.models.assessment import AssessmentRun, AssessmentStage, AssessmentStatus
from app.models.profile import StudentProfile
from app.models.skill import Skill
from app.models.verification import SkillVerification
from app.models.project import LifecycleStatus, Project
from app.models.user import User, UserRole
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    RequesterApplicationResponse,
)
from app.schemas.project import ProjectResponse
from app.services.applications import apply_to_project, handle_application, transition_project
from app.services.portfolios import portfolio_to_response


router = APIRouter(tags=["applications"])
student_only = require_roles(UserRole.student)
requester_only = require_roles(UserRole.requester)


@router.post("/projects/{project_id}/applications", response_model=ApplicationResponse, status_code=201)
def apply(project_id: int, payload: ApplicationCreate, current: User = Depends(student_only), db: Session = Depends(get_db)):
    return apply_to_project(db, current, project_id, payload.message, payload.portfolio_ids)


@router.get("/applications/mine", response_model=list[ApplicationResponse])
def mine(current: User = Depends(student_only), db: Session = Depends(get_db)):
    return list(db.scalars(select(Application).where(Application.student_id == current.id)))


@router.get("/projects/{project_id}/applications", response_model=list[RequesterApplicationResponse])
def project_applications(project_id: int, current: User = Depends(requester_only), db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None or project.creator_id != current.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="项目不存在")
    applications = list(
        db.scalars(select(Application).where(Application.project_id == project_id))
    )
    result = []
    for application in applications:
        student = db.get(User, application.student_id)
        profile = db.scalar(
            select(StudentProfile).where(StudentProfile.user_id == application.student_id)
        )
        skills = list(
            db.scalars(select(Skill).where(Skill.user_id == application.student_id))
        )
        portfolio_ids = list(
            db.scalars(
                select(ApplicationPortfolioGrant.portfolio_id).where(
                    ApplicationPortfolioGrant.application_id == application.id
                )
            )
        )
        portfolios = (
            list(db.scalars(select(Portfolio).where(Portfolio.id.in_(portfolio_ids))))
            if portfolio_ids
            else []
        )
        authorized = []
        for item in portfolios:
            latest = db.scalar(
                select(AssessmentRun)
                .where(
                    AssessmentRun.portfolio_id == item.id,
                    AssessmentRun.stage == AssessmentStage.reassessment,
                    AssessmentRun.status == AssessmentStatus.succeeded,
                )
                .order_by(AssessmentRun.created_at.desc())
            )
            verification = (
                db.scalar(
                    select(SkillVerification).where(
                        SkillVerification.assessment_run_id == latest.id
                    )
                )
                if latest
                else None
            )
            portfolio_payload = portfolio_to_response(db, item)
            portfolio_payload.update(
                {
                    "ai_assessment": (
                        json.loads(latest.structured_result)
                        if latest and latest.structured_result
                        else None
                    ),
                    "verification_status": (
                        verification.status if verification else None
                    ),
                    "result_label": (
                        "AI 辅助初评、待人工复核" if latest else None
                    ),
                }
            )
            authorized.append(portfolio_payload)
        result.append(
            {
                "id": application.id,
                "project_id": application.project_id,
                "student_id": application.student_id,
                "message": application.message,
                "status": application.status,
                "created_at": application.created_at,
                "student": {
                    "user_id": application.student_id,
                    "display_name": profile.display_name if profile else student.username,
                    "skills": skills,
                },
                "authorized_portfolios": authorized,
            }
        )
    return result


@router.post("/applications/{application_id}/accept", response_model=ApplicationResponse)
def accept(application_id: int, current: User = Depends(requester_only), db: Session = Depends(get_db)):
    return handle_application(db, current, application_id, ApplicationStatus.accepted)


@router.post("/applications/{application_id}/reject", response_model=ApplicationResponse)
def reject(application_id: int, current: User = Depends(requester_only), db: Session = Depends(get_db)):
    return handle_application(db, current, application_id, ApplicationStatus.rejected)


@router.post("/projects/{project_id}/start", response_model=ProjectResponse)
def start(project_id: int, current: User = Depends(requester_only), db: Session = Depends(get_db)):
    return transition_project(db, current, project_id, LifecycleStatus.in_progress)


@router.post("/projects/{project_id}/finish-work", response_model=ProjectResponse)
def finish_work(project_id: int, current: User = Depends(requester_only), db: Session = Depends(get_db)):
    return transition_project(db, current, project_id, LifecycleStatus.awaiting_review)
