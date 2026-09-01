from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.review import Review
from app.models.user import User, UserRole
from app.schemas.review import ReviewCreate, ReviewResponse
from app.services.reviews import create_review


router = APIRouter(tags=["reviews"])
requester_only = require_roles(UserRole.requester)


@router.post("/projects/{project_id}/reviews/{student_id}", response_model=ReviewResponse, status_code=201)
def create(project_id: int, student_id: int, payload: ReviewCreate, current: User = Depends(requester_only), db: Session = Depends(get_db)):
    return create_review(db, current, project_id, student_id, payload)


@router.get("/profiles/students/{student_id}/reviews", response_model=list[ReviewResponse])
def student_reviews(student_id: int, db: Session = Depends(get_db)):
    return list(db.scalars(select(Review).where(Review.student_id == student_id)))
