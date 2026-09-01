from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.models.portfolio import Portfolio
from app.models.project import ProjectRequiredSkill
from app.models.review import Review
from app.models.skill import Skill


def level_for_score(score: int) -> int:
    if score >= 120:
        return 4
    if score >= 60:
        return 3
    if score >= 20:
        return 2
    return 1


def recalculate_skill(db: Session, skill_id: int) -> Skill:
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise ValueError("skill not found")
    portfolio_count = db.scalar(select(func.count(Portfolio.id)).where(Portfolio.skill_id == skill.id)) or 0
    matching_projects = list(db.scalars(
        select(Application.project_id)
        .join(ProjectRequiredSkill, ProjectRequiredSkill.project_id == Application.project_id)
        .where(
            Application.student_id == skill.user_id,
            Application.status == ApplicationStatus.finished,
            func.lower(ProjectRequiredSkill.skill_name) == skill.normalized_name,
        )
        .distinct()
    ))
    review_points = 0.0
    if matching_projects:
        reviews = db.scalars(select(Review).where(Review.student_id == skill.user_id, Review.project_id.in_(matching_projects)))
        review_points = sum((r.skill_score + r.communication_score + r.delivery_score + r.time_management_score) / 4 * 3 for r in reviews)
    score = int(round(portfolio_count * 10 + len(matching_projects) * 20 + review_points))
    skill.growth_score = score
    skill.level = level_for_score(score)
    db.flush()
    return skill


def recalculate_student_skills(db: Session, student_id: int) -> None:
    for skill in db.scalars(select(Skill).where(Skill.user_id == student_id)):
        recalculate_skill(db, skill.id)
