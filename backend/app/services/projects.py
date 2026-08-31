from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import AuditStatus, Project, ProjectRequiredSkill
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, user: User, payload: ProjectCreate) -> Project:
    project = Project(**payload.model_dump(exclude={"required_skills"}), creator_id=user.id)
    project.skill_requirements = [ProjectRequiredSkill(skill_name=name) for name in payload.required_skills]
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, user: User, project_id: int, payload: ProjectUpdate) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.creator_id == user.id))
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    if project.audit_status != AuditStatus.pending:
        raise HTTPException(status_code=409, detail="只有待审核项目可编辑")
    data = payload.model_dump(exclude_unset=True, exclude={"required_skills"})
    for field, value in data.items():
        setattr(project, field, value)
    if payload.required_skills is not None:
        names = ProjectCreate.normalize_skills(payload.required_skills)
        project.skill_requirements = [ProjectRequiredSkill(skill_name=name) for name in names]
    db.commit()
    db.refresh(project)
    return project


def audit_project(db: Session, project_id: int, status: AuditStatus) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    if project.audit_status != AuditStatus.pending:
        raise HTTPException(status_code=409, detail="项目已审核")
    project.audit_status = status
    db.commit()
    db.refresh(project)
    return project
