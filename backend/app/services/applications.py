from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.models.project import AuditStatus, LifecycleStatus, Project
from app.models.user import User


def apply_to_project(db: Session, student: User, project_id: int, message: str | None) -> Application:
    project = db.get(Project, project_id)
    if project is None or project.audit_status != AuditStatus.approved:
        raise HTTPException(status_code=404, detail="项目不存在")
    if project.lifecycle_status != LifecycleStatus.recruiting:
        raise HTTPException(status_code=409, detail="项目当前不接受申请")
    if project.deadline < date.today():
        raise HTTPException(status_code=409, detail="项目申请已截止")
    existing = db.scalar(select(Application).where(Application.project_id == project_id, Application.student_id == student.id))
    if existing:
        raise HTTPException(status_code=409, detail="不能重复申请同一项目")
    application = Application(project_id=project_id, student_id=student.id, message=message)
    db.add(application); db.commit(); db.refresh(application)
    return application


def handle_application(db: Session, owner: User, application_id: int, target: ApplicationStatus) -> Application:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="申请不存在")
    project = db.get(Project, application.project_id)
    if project is None or project.creator_id != owner.id:
        raise HTTPException(status_code=404, detail="申请不存在")
    if application.status != ApplicationStatus.pending:
        raise HTTPException(status_code=409, detail="申请已处理")
    if project.lifecycle_status != LifecycleStatus.recruiting:
        raise HTTPException(status_code=409, detail="项目已不在招募状态")
    application.status = target
    db.commit(); db.refresh(application)
    return application


def transition_project(db: Session, owner: User, project_id: int, target: LifecycleStatus) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.creator_id == owner.id))
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    predecessors = {LifecycleStatus.in_progress: LifecycleStatus.recruiting, LifecycleStatus.awaiting_review: LifecycleStatus.in_progress}
    if project.lifecycle_status != predecessors[target]:
        raise HTTPException(status_code=409, detail="项目状态不能跳步")
    if target == LifecycleStatus.in_progress:
        accepted = db.scalar(select(Application).where(Application.project_id == project.id, Application.status == ApplicationStatus.accepted))
        if accepted is None:
            raise HTTPException(status_code=409, detail="至少录用一名学生后才能开始项目")
    project.lifecycle_status = target
    db.commit(); db.refresh(project)
    return project
