from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.project import AuditStatus, LifecycleStatus, Project, ProjectRequiredSkill
from app.models.user import User, UserRole
from app.schemas.collaboration import ProjectPlanBrief, ProjectPlanDraft
from app.schemas.project import ProjectCreate, ProjectPage, ProjectResponse, ProjectUpdate
from app.services.model_gateway import DashScopeVisionModel
from app.services.project_planning import generate_plan
from app.services.projects import create_project, update_project


router = APIRouter(prefix="/projects", tags=["projects"])
requester_only = require_roles(UserRole.requester)


def get_planning_model():
    return DashScopeVisionModel()


@router.get("", response_model=ProjectPage)
def public_projects(keyword: str | None = None, category: str | None = None, skill: str | None = None, deadline: date | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    query = select(Project).where(Project.audit_status == AuditStatus.approved, Project.lifecycle_status == LifecycleStatus.recruiting)
    if keyword:
        query = query.where(or_(Project.title.contains(keyword), Project.description.contains(keyword)))
    if category:
        query = query.where(Project.category == category)
    if deadline:
        query = query.where(Project.deadline <= deadline)
    if skill:
        query = query.join(ProjectRequiredSkill).where(func.lower(ProjectRequiredSkill.skill_name) == skill.strip().lower())
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Project.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).unique())
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/mine", response_model=list[ProjectResponse])
def mine(current_user: User = Depends(requester_only), db: Session = Depends(get_db)):
    return list(db.scalars(select(Project).where(Project.creator_id == current_user.id)))


@router.post("/plan-draft", response_model=ProjectPlanDraft)
def plan_draft(
    payload: ProjectPlanBrief,
    _: User = Depends(requester_only),
    model=Depends(get_planning_model),
):
    return generate_plan(payload, model)


@router.post("", response_model=ProjectResponse, status_code=201)
def create(payload: ProjectCreate, current_user: User = Depends(requester_only), db: Session = Depends(get_db)):
    if payload.deadline < date.today():
        raise HTTPException(status_code=422, detail="截止日期不能早于今天")
    return create_project(db, current_user, payload)


@router.patch("/{project_id}", response_model=ProjectResponse)
def patch(project_id: int, payload: ProjectUpdate, current_user: User = Depends(requester_only), db: Session = Depends(get_db)):
    return update_project(db, current_user, project_id, payload)


@router.get("/{project_id}", response_model=ProjectResponse)
def detail(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None or project.audit_status != AuditStatus.approved:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project
