from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.models.collaboration import ProjectPosition, ProjectTask, ProjectTaskEvent, TaskStatus
from app.models.profile import StudentProfile
from app.models.project import LifecycleStatus, Project
from app.models.user import User, UserRole
from app.schemas.collaboration import ProjectTaskCreate


MEMBER_STATUSES = {ApplicationStatus.accepted, ApplicationStatus.finished}


def _member_application(db: Session, project_id: int, user_id: int) -> Application | None:
    return db.scalar(select(Application).where(
        Application.project_id == project_id,
        Application.student_id == user_id,
        Application.status.in_(MEMBER_STATUSES),
    ))


def _project_for_workspace(db: Session, user: User, project_id: int) -> tuple[Project, Application | None]:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    if user.role == UserRole.requester and project.creator_id == user.id:
        return project, None
    if user.role == UserRole.student:
        membership = _member_application(db, project_id, user.id)
        if membership is not None:
            return project, membership
    raise HTTPException(status_code=404, detail="项目协作空间不存在")


def workspace_payload(db: Session, user: User, project_id: int) -> dict:
    project, _ = _project_for_workspace(db, user, project_id)
    applications = list(db.scalars(select(Application).where(
        Application.project_id == project_id,
        Application.status.in_(MEMBER_STATUSES),
    )))
    profiles = {
        profile.user_id: profile for profile in db.scalars(
            select(StudentProfile).where(StudentProfile.user_id.in_([item.student_id for item in applications]))
        )
    } if applications else {}
    positions = {position.id: position for position in project.positions}
    members = [{
        "student_id": item.student_id,
        "display_name": profiles[item.student_id].display_name if item.student_id in profiles else f"学生 {item.student_id}",
        "position_id": item.position_id,
        "position_title": positions[item.position_id].title if item.position_id in positions else None,
    } for item in applications]
    counts = {status: 0 for status in TaskStatus}
    for task in project.tasks:
        counts[task.status] += 1
    total = len(project.tasks)
    return {
        "project": {"id": project.id, "title": project.title, "lifecycle_status": project.lifecycle_status},
        "positions": project.positions,
        "members": members,
        "tasks": project.tasks,
        "progress": {
            "total": total,
            "todo": counts[TaskStatus.todo],
            "in_progress": counts[TaskStatus.in_progress],
            "done": counts[TaskStatus.done],
            "completion_percent": round(counts[TaskStatus.done] * 100 / total) if total else 0,
        },
        "can_manage": user.role == UserRole.requester and project.creator_id == user.id,
    }


def create_task(db: Session, owner: User, project_id: int, payload: ProjectTaskCreate) -> ProjectTask:
    project = db.get(Project, project_id)
    if project is None or project.creator_id != owner.id:
        raise HTTPException(status_code=404, detail="项目不存在")
    if project.lifecycle_status not in {LifecycleStatus.recruiting, LifecycleStatus.in_progress}:
        raise HTTPException(status_code=409, detail="当前阶段不能新增事项")
    position = None
    if payload.position_code:
        position = db.scalar(select(ProjectPosition).where(
            ProjectPosition.project_id == project_id,
            ProjectPosition.code == payload.position_code,
        ))
        if position is None:
            raise HTTPException(status_code=422, detail="岗位不存在")
    if payload.assignee_student_id:
        membership = _member_application(db, project_id, payload.assignee_student_id)
        if membership is None:
            raise HTTPException(status_code=422, detail="负责人不是项目成员")
        if position and membership.position_id not in {None, position.id}:
            raise HTTPException(status_code=422, detail="负责人不属于该岗位")
    task = ProjectTask(
        project_id=project_id,
        position_id=position.id if position else None,
        title=payload.title,
        description=payload.description,
        assignee_student_id=payload.assignee_student_id,
        due_date=payload.due_date,
        sort_order=payload.sort_order,
        updated_by_id=owner.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task_status(db: Session, user: User, task_id: int, target: TaskStatus, expected_version: int) -> ProjectTask:
    task = db.get(ProjectTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="事项不存在")
    project, membership = _project_for_workspace(db, user, task.project_id)
    if project.lifecycle_status != LifecycleStatus.in_progress:
        raise HTTPException(status_code=409, detail="只有进行中的项目可以更新事项")
    if task.version != expected_version:
        raise HTTPException(status_code=409, detail="事项已被其他成员更新，请刷新后重试")
    if membership is not None:
        owns_task = task.assignee_student_id == user.id
        shares_position = task.assignee_student_id is None and task.position_id == membership.position_id
        if not (owns_task or shares_position):
            raise HTTPException(status_code=403, detail="只能更新本人或本岗位的事项")
    previous = task.status
    if previous == target:
        return task
    task.status = target
    task.version += 1
    task.updated_by_id = user.id
    db.add(ProjectTaskEvent(task_id=task.id, actor_id=user.id, from_status=previous, to_status=target, version=task.version))
    db.commit()
    db.refresh(task)
    return task


def student_workspace_ids(db: Session, student_id: int) -> list[int]:
    return list(db.scalars(select(Application.project_id).where(
        Application.student_id == student_id,
        Application.status.in_(MEMBER_STATUSES),
    ).order_by(Application.created_at.desc())))
