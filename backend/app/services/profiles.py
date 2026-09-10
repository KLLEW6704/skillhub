from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import RequesterProfile, StudentProfile
from app.models.skill import Skill
from app.models.portfolio import EvidenceVisibility, Portfolio, PortfolioEvidence
from app.models.user import User, UserRole
from app.schemas.profile import ProfileUpdate
from app.services.portfolios import portfolio_to_response


def create_profile_for_user(db: Session, user: User) -> None:
    if user.role == UserRole.student:
        db.add(StudentProfile(user_id=user.id, display_name=user.username))
    elif user.role == UserRole.requester:
        db.add(RequesterProfile(user_id=user.id, organization_name=user.username))


def get_or_create_profile(db: Session, user: User):
    model = StudentProfile if user.role == UserRole.student else RequesterProfile
    profile = db.scalar(select(model).where(model.user_id == user.id))
    if profile is None:
        create_profile_for_user(db, user)
        db.commit()
        profile = db.scalar(select(model).where(model.user_id == user.id))
    return profile


def update_profile(db: Session, user: User, payload: ProfileUpdate):
    profile = get_or_create_profile(db, user)
    allowed = (
        {"display_name", "avatar_url", "bio"}
        if user.role == UserRole.student
        else {"organization_name", "organization_type", "description"}
    )
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field in allowed:
            setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


def public_student(db: Session, user: User) -> dict:
    profile = get_or_create_profile(db, user)
    skills = list(db.scalars(select(Skill).where(Skill.user_id == user.id)))
    portfolios = list(
        db.scalars(
            select(Portfolio)
            .join(
                PortfolioEvidence,
                PortfolioEvidence.portfolio_id == Portfolio.id,
            )
            .where(
                Portfolio.user_id == user.id,
                PortfolioEvidence.visibility == EvidenceVisibility.public,
            )
        )
    )
    return {
        "user_id": user.id,
        "username": user.username,
        "school": user.school,
        "college": user.college,
        "major": user.major,
        "grade": user.grade,
        "display_name": profile.display_name,
        "avatar_url": profile.avatar_url,
        "bio": profile.bio,
        "skills": skills,
        "portfolios": [portfolio_to_response(db, item) for item in portfolios],
    }
