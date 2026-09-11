import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import (
    AuditStatus,
    Project,
    ProjectDeliveryRequirements,
    ProjectRequiredSkill,
)
from app.models.collaboration import ProjectDraft, ProjectPosition, ProjectTask
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, user: User, payload: ProjectCreate) -> Project:
    source_draft = None
    if payload.draft_id is not None:
        source_draft = db.scalar(select(ProjectDraft).where(ProjectDraft.id == payload.draft_id, ProjectDraft.creator_id == user.id))
        if source_draft is None:
            raise HTTPException(status_code=404, detail="项目草稿不存在")
    project = Project(
        **payload.model_dump(
            exclude={"draft_id", "required_skills", "deliverables", "acceptance_criteria", "positions", "tasks"}
        ),
        creator_id=user.id,
    )
    project.skill_requirements = [ProjectRequiredSkill(skill_name=name) for name in payload.required_skills]
    project.delivery_requirements = ProjectDeliveryRequirements(
        deliverables=payload.deliverables,
        acceptance_criteria=payload.acceptance_criteria,
    )
    codes: dict[str, ProjectPosition] = {}
    for position_payload in payload.positions:
        position = ProjectPosition(
            code=position_payload.code,
            title=position_payload.title,
            category=position_payload.category,
            description=position_payload.description,
            headcount=position_payload.headcount,
            required_skills_json=json.dumps(position_payload.required_skills, ensure_ascii=False),
            deliverables=position_payload.deliverables,
            sort_order=position_payload.sort_order,
        )
        project.positions.append(position)
        codes[position.code] = position
    db.add(project)
    db.flush()
    for task_payload in payload.tasks:
        position = codes.get(task_payload.position_code) if task_payload.position_code else None
        if task_payload.position_code and position is None:
            raise HTTPException(status_code=422, detail=f"任务引用了不存在的岗位：{task_payload.position_code}")
        project.tasks.append(ProjectTask(
            title=task_payload.title,
            description=task_payload.description,
            position_id=position.id if position else None,
            assignee_student_id=task_payload.assignee_student_id,
            due_date=task_payload.due_date,
            sort_order=task_payload.sort_order,
        ))
    if source_draft is not None:
        db.delete(source_draft)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, user: User, project_id: int, payload: ProjectUpdate) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.creator_id == user.id))
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    if project.audit_status != AuditStatus.pending:
        raise HTTPException(status_code=409, detail="只有待审核项目可编辑")
    data = payload.model_dump(
        exclude_unset=True,
        exclude={"required_skills", "deliverables", "acceptance_criteria"},
    )
    for field, value in data.items():
        setattr(project, field, value)
    if payload.required_skills is not None:
        names = ProjectCreate.normalize_skills(payload.required_skills)
        project.skill_requirements = [ProjectRequiredSkill(skill_name=name) for name in names]
    if "deliverables" in payload.model_fields_set or "acceptance_criteria" in payload.model_fields_set:
        if project.delivery_requirements is None:
            project.delivery_requirements = ProjectDeliveryRequirements()
        if "deliverables" in payload.model_fields_set:
            project.delivery_requirements.deliverables = payload.deliverables
        if "acceptance_criteria" in payload.model_fields_set:
            project.delivery_requirements.acceptance_criteria = payload.acceptance_criteria
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
