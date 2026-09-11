import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.review import Review
from app.models.project_validation import ProjectValidationRecord
from app.models.user import User, UserRole
from app.schemas.review import ProjectValidationResponse, ReviewCreate, ReviewResponse
from app.schemas.collaboration import RubricDefinitionResponse
from app.services.reviews import create_review
from app.services.rubrics import POSITION_CATEGORY_LABELS, PROJECT_REVIEW_RUBRICS


router = APIRouter(tags=["reviews"])
requester_only = require_roles(UserRole.requester)


@router.get("/review-rubrics", response_model=list[RubricDefinitionResponse])
def review_rubrics():
    return [
        {"category": category, "label": POSITION_CATEGORY_LABELS[category], "version": version, "criteria": criteria}
        for category, (version, criteria) in PROJECT_REVIEW_RUBRICS.items()
    ]


@router.post("/projects/{project_id}/reviews/{student_id}", response_model=ReviewResponse, status_code=201)
def create(project_id: int, student_id: int, payload: ReviewCreate, current: User = Depends(requester_only), db: Session = Depends(get_db)):
    return create_review(db, current, project_id, student_id, payload)


@router.get("/profiles/students/{student_id}/reviews", response_model=list[ReviewResponse])
def student_reviews(student_id: int, db: Session = Depends(get_db)):
    return list(db.scalars(select(Review).where(Review.student_id == student_id)))


@router.get(
    "/profiles/students/{student_id}/project-validations",
    response_model=list[ProjectValidationResponse],
)
def student_project_validations(student_id: int, db: Session = Depends(get_db)):
    records = list(
        db.scalars(
            select(ProjectValidationRecord)
            .where(ProjectValidationRecord.student_id == student_id)
            .order_by(ProjectValidationRecord.created_at.desc())
        )
    )
    return [
        {
            "id": record.id,
            "project_id": record.project_id,
            "student_id": record.student_id,
            "requester_id": record.requester_id,
            "project_title": record.project_title,
            "position_title": record.position_title,
            "position_category": record.position_category,
            "rubric_version": record.rubric_version,
            "criteria_scores": json.loads(record.criteria_scores_snapshot or "{}"),
            "deliverables": record.deliverables_snapshot,
            "acceptance_criteria": record.acceptance_criteria_snapshot,
            "required_skills": json.loads(record.required_skills_snapshot),
            "outcome": record.outcome,
            "created_at": record.created_at,
        }
        for record in records
    ]
