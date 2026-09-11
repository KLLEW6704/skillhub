from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.collaboration import ProjectDraftPayload, ProjectDraftResponse, ProjectTaskCreate, ProjectTaskResponse, ProjectTaskStatusUpdate, ProjectWorkspaceResponse
from app.services.collaboration import create_task, student_workspace_ids, update_task_status, workspace_payload
from app.services.project_drafts import delete_project_draft, list_project_drafts, save_project_draft


router = APIRouter(tags=["project collaboration"])
requester_only = require_roles(UserRole.requester)
student_only = require_roles(UserRole.student)


@router.get("/project-drafts", response_model=list[ProjectDraftResponse])
def project_drafts(current: User = Depends(requester_only), db: Session = Depends(get_db)):
    return list_project_drafts(db, current)


@router.post("/project-drafts", response_model=ProjectDraftResponse, status_code=201)
def create_project_draft(payload: ProjectDraftPayload, current: User = Depends(requester_only), db: Session = Depends(get_db)):
    return save_project_draft(db, current, payload)


@router.patch("/project-drafts/{draft_id}", response_model=ProjectDraftResponse)
def update_project_draft(draft_id: int, payload: ProjectDraftPayload, current: User = Depends(requester_only), db: Session = Depends(get_db)):
    return save_project_draft(db, current, payload, draft_id)


@router.delete("/project-drafts/{draft_id}", status_code=204)
def remove_project_draft(draft_id: int, current: User = Depends(requester_only), db: Session = Depends(get_db)):
    delete_project_draft(db, current, draft_id)


@router.get("/projects/{project_id}/workspace", response_model=ProjectWorkspaceResponse)
def project_workspace(project_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return workspace_payload(db, current, project_id)


@router.get("/project-workspaces/mine", response_model=list[ProjectWorkspaceResponse])
def my_workspaces(current: User = Depends(student_only), db: Session = Depends(get_db)):
    return [workspace_payload(db, current, project_id) for project_id in student_workspace_ids(db, current.id)]


@router.post("/projects/{project_id}/tasks", response_model=ProjectTaskResponse, status_code=201)
def add_task(project_id: int, payload: ProjectTaskCreate, current: User = Depends(requester_only), db: Session = Depends(get_db)):
    return create_task(db, current, project_id, payload)


@router.patch("/project-tasks/{task_id}/status", response_model=ProjectTaskResponse)
def change_task_status(task_id: int, payload: ProjectTaskStatusUpdate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return update_task_status(db, current, task_id, payload.status, payload.expected_version)
