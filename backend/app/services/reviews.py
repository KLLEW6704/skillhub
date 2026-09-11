import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.models.collaboration import PositionCategory
from app.models.project import LifecycleStatus, Project
from app.models.review import Review
from app.models.project_validation import ProjectValidationRecord
from app.models.user import User
from app.schemas.review import ReviewCreate
from app.services.rubrics import project_rubric
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
    position = application.position
    category = position.category if position else PositionCategory.general
    rubric_version, criteria = project_rubric(category)
    if payload.criteria_scores is not None:
        if set(payload.criteria_scores) != set(criteria):
            raise HTTPException(status_code=422, detail="岗位评价维度不完整或与岗位分类不匹配")
        scores = [payload.criteria_scores[item] for item in criteria]
    else:
        scores = [
            payload.skill_score,
            payload.communication_score,
            payload.delivery_score,
            payload.time_management_score,
        ]
    if any(score is None or not 1 <= score <= 5 for score in scores):
        raise HTTPException(status_code=422, detail="评价分数必须在 1–5 之间")
    normalized_scores = {criterion: int(score) for criterion, score in zip(criteria, scores)}
    review = Review(
        project_id=project_id,
        reviewer_id=reviewer.id,
        student_id=student_id,
        position_id=application.position_id,
        rubric_category=category.value,
        rubric_version=rubric_version,
        criteria_scores_json=json.dumps(normalized_scores, ensure_ascii=False),
        skill_score=int(scores[0]),
        communication_score=int(scores[1]),
        delivery_score=int(scores[2]),
        time_management_score=int(scores[3]),
        comment=payload.comment,
    )
    db.add(review)
    application.status = ApplicationStatus.finished
    db.flush()
    db.add(
        ProjectValidationRecord(
            project_id=project.id,
            student_id=student_id,
            requester_id=reviewer.id,
            review_id=review.id,
            project_title=project.title,
            position_title=position.title if position else None,
            position_category=category.value,
            rubric_version=rubric_version,
            criteria_scores_snapshot=json.dumps(normalized_scores, ensure_ascii=False),
            deliverables_snapshot=project.deliverables,
            acceptance_criteria_snapshot=project.acceptance_criteria,
            required_skills_snapshot=json.dumps(
                project.required_skills, ensure_ascii=False
            ),
        )
    )
    remaining = db.scalar(select(Application).where(Application.project_id == project_id, Application.status == ApplicationStatus.accepted))
    if remaining is None:
        project.lifecycle_status = LifecycleStatus.completed
    recalculate_student_skills(db, student_id)
    db.commit(); db.refresh(review)
    return review
