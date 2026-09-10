from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import (
    Application,
    ApplicationPortfolioGrant,
    ApplicationStatus,
    InvitationStatus,
    ProjectInvitation,
)
from app.models.portfolio import Portfolio
from app.models.project import AuditStatus, LifecycleStatus, Project
from app.models.user import User, UserRole


def invite_student_to_project(
    db: Session,
    requester: User,
    project_id: int,
    student_id: int,
    message: str | None,
) -> ProjectInvitation:
    project = db.get(Project, project_id)
    if project is None or project.creator_id != requester.id:
        raise HTTPException(status_code=404, detail="项目不存在")
    if project.audit_status != AuditStatus.approved:
        raise HTTPException(status_code=409, detail="项目通过审核后才能发出邀约")
    if project.lifecycle_status != LifecycleStatus.recruiting:
        raise HTTPException(status_code=409, detail="只有招募中的项目可以发出邀约")
    if project.deadline < date.today():
        raise HTTPException(status_code=409, detail="项目申请已截止")

    student = db.get(User, student_id)
    if student is None or student.role != UserRole.student or not student.is_active:
        raise HTTPException(status_code=404, detail="学生档案不存在")
    existing_application = db.scalar(
        select(Application).where(
            Application.project_id == project_id,
            Application.student_id == student_id,
        )
    )
    if existing_application:
        raise HTTPException(status_code=409, detail="该学生已申请过此项目")
    existing_invitation = db.scalar(
        select(ProjectInvitation).where(
            ProjectInvitation.project_id == project_id,
            ProjectInvitation.student_id == student_id,
        )
    )
    if existing_invitation:
        raise HTTPException(status_code=409, detail="已向该学生发送过此项目邀约")

    invitation = ProjectInvitation(
        project_id=project_id,
        student_id=student_id,
        inviter_id=requester.id,
        message=message.strip() if message and message.strip() else None,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def mark_invitation_viewed(
    db: Session, student: User, invitation_id: int
) -> ProjectInvitation:
    invitation = db.get(ProjectInvitation, invitation_id)
    if invitation is None or invitation.student_id != student.id:
        raise HTTPException(status_code=404, detail="项目邀约不存在")
    if invitation.status == InvitationStatus.pending:
        invitation.status = InvitationStatus.viewed
        invitation.viewed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(invitation)
    return invitation


def apply_to_project(
    db: Session,
    student: User,
    project_id: int,
    message: str | None,
    portfolio_ids: list[int] | None = None,
) -> Application:
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
    selected_ids = list(dict.fromkeys(portfolio_ids or []))
    if selected_ids:
        owned_ids = set(
            db.scalars(
                select(Portfolio.id).where(
                    Portfolio.user_id == student.id, Portfolio.id.in_(selected_ids)
                )
            )
        )
        if owned_ids != set(selected_ids):
            raise HTTPException(status_code=404, detail="选择的作品不存在")
    application = Application(project_id=project_id, student_id=student.id, message=message)
    db.add(application)
    db.flush()
    for portfolio_id in selected_ids:
        db.add(
            ApplicationPortfolioGrant(
                application_id=application.id, portfolio_id=portfolio_id
            )
        )
    invitation = db.scalar(
        select(ProjectInvitation).where(
            ProjectInvitation.project_id == project_id,
            ProjectInvitation.student_id == student.id,
        )
    )
    if invitation:
        invitation.status = InvitationStatus.applied
        invitation.viewed_at = invitation.viewed_at or datetime.now(timezone.utc)
    db.commit(); db.refresh(application)
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
