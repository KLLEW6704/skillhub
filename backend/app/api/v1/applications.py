from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.application import Application, ApplicationStatus
from app.models.project import LifecycleStatus, Project
from app.models.user import User, UserRole
from app.schemas.application import ApplicationCreate, ApplicationResponse
from app.schemas.project import ProjectResponse
from app.services.applications import apply_to_project, handle_application, transition_project


router = APIRouter(tags=["applications"])
student_only = require_roles(UserRole.student)
requester_only = require_roles(UserRole.requester)


@router.post("/projects/{project_id}/applications", response_model=ApplicationResponse, status_code=201)
def apply(project_id: int, payload: ApplicationCreate, current: User = Depends(student_only), db: Session = Depends(get_db)):
    return apply_to_project(db, current, project_id, payload.message)


@router.get("/applications/mine", response_model=list[ApplicationResponse])
def mine(current: User = Depends(student_only), db: Session = Depends(get_db)):
    return list(db.scalars(select(Application).where(Application.student_id == current.id)))


@router.get("/projects/{project_id}/applications", response_model=list[ApplicationResponse])
def project_applications(project_id: int, current: User = Depends(requester_only), db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None or project.creator_id != current.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="项目不存在")
    return list(db.scalars(select(Application).where(Application.project_id == project_id)))


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
