from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.models.project import LifecycleStatus, Project
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate
from app.services.growth import recalculate_student_skills


def create_review(db: Session, reviewer: User, project_id: int, student_id: int, payload: ReviewCreate) -> Review:
    project = db.get(Project, project_id)
    if project is None or project.creator_id != reviewer.id:
        raise HTTPException(status_code=404, detail="项目不存在")
    if project.lifecycle_status not in {LifecycleStatus.awaiting_review, LifecycleStatus.completed}:
        raise HTTPException(status_code=409, detail="项目尚未进入评价阶段")
    application = db.scalar(select(Application).where(Application.project_id == project_id, Application.student_id == student_id))
    if application is None or application.status not in {ApplicationStatus.accepted, ApplicationStatus.finished}:
        raise HTTPException(status_code=409, detail="只能评价已录用学生")
    if db.scalar(select(Review).where(Review.project_id == project_id, Review.student_id == student_id)):
        raise HTTPException(status_code=409, detail="不能重复评价")
    review = Review(project_id=project_id, reviewer_id=reviewer.id, student_id=student_id, **payload.model_dump())
    db.add(review)
    application.status = ApplicationStatus.finished
    db.flush()
    remaining = db.scalar(select(Application).where(Application.project_id == project_id, Application.status == ApplicationStatus.accepted))
    if remaining is None:
        project.lifecycle_status = LifecycleStatus.completed
    recalculate_student_skills(db, student_id)
    db.commit(); db.refresh(review)
    return review
