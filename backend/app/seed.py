from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.application import Application, ApplicationStatus
from app.models.portfolio import Portfolio
from app.models.profile import RequesterProfile, StudentProfile
from app.models.project import AuditStatus, LifecycleStatus, Project, ProjectRequiredSkill
from app.models.review import Review
from app.models.skill import Skill
from app.models.user import User, UserRole
from app.services.growth import recalculate_student_skills


DEMO_PASSWORD = "Student123!"


def ensure_user(db: Session, username: str, email: str, role: UserRole, **fields) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if user:
        if user.email != email:
            user.email = email
            db.flush()
        return user
    user = User(username=username, email=email, password_hash=hash_password(DEMO_PASSWORD), role=role, **fields)
    db.add(user); db.flush()
    if role == UserRole.student:
        db.add(StudentProfile(user_id=user.id, display_name=fields.get("display_name", username)))
    elif role == UserRole.requester:
        db.add(RequesterProfile(user_id=user.id, organization_name="校园创新中心", organization_type="校园组织", description="发布真实校园实践项目"))
    db.flush()
    return user


def ensure_skill(db: Session, user: User, name: str, description: str) -> Skill:
    normalized = name.casefold()
    skill = db.scalar(select(Skill).where(Skill.user_id == user.id, Skill.normalized_name == normalized))
    if skill:
        return skill
    skill = Skill(user_id=user.id, name=name, normalized_name=normalized, description=description)
    db.add(skill); db.flush()
    return skill


def ensure_project(db: Session, creator: User, title: str, audit: AuditStatus, lifecycle: LifecycleStatus, skills: list[str], days: int) -> Project:
    project = db.scalar(select(Project).where(Project.title == title))
    if project:
        return project
    project = Project(
        creator_id=creator.id,
        title=title,
        description=f"{title}，用于 SkillHub 课程演示。",
        category="校园实践",
        budget=1000,
        deadline=date.today() + timedelta(days=days),
        audit_status=audit,
        lifecycle_status=lifecycle,
        skill_requirements=[ProjectRequiredSkill(skill_name=name) for name in skills],
    )
    db.add(project); db.flush()
    return project


def ensure_application(db: Session, project: Project, student: User, status: ApplicationStatus) -> Application:
    application = db.scalar(select(Application).where(Application.project_id == project.id, Application.student_id == student.id))
    if application:
        return application
    application = Application(project_id=project.id, student_id=student.id, message="希望把课堂技能用于真实校园场景", status=status)
    db.add(application); db.flush()
    return application


def seed_database(db: Session) -> None:
    ensure_user(db, "admin", "admin@skillhub.example.com", UserRole.admin)
    student = ensure_user(db, "student", "student@skillhub.example.com", UserRole.student, school="SkillHub 大学", college="计算机学院", major="数据科学", grade="2025")
    designer = ensure_user(db, "designer", "designer@skillhub.example.com", UserRole.student, school="SkillHub 大学", college="设计学院", major="视觉传达", grade="2024")
    requester = ensure_user(db, "campus_org", "campus_org@skillhub.example.com", UserRole.requester)

    python_skill = ensure_skill(db, student, "Python", "数据处理、接口开发与自动化")
    design_skill = ensure_skill(db, designer, "视觉设计", "校园品牌与活动视觉设计")
    if not db.scalar(select(Portfolio).where(Portfolio.user_id == student.id, Portfolio.title == "校园数据看板")):
        db.add(Portfolio(user_id=student.id, skill_id=python_skill.id, title="校园数据看板", description="课程数据可视化作品", file_url="/uploads/demo-dashboard.pdf", file_type="application/pdf"))
    if not db.scalar(select(Portfolio).where(Portfolio.user_id == designer.id, Portfolio.title == "迎新视觉系统")):
        db.add(Portfolio(user_id=designer.id, skill_id=design_skill.id, title="迎新视觉系统", description="迎新季主视觉与延展", file_url="/uploads/demo-design.png", file_type="image/png"))
    db.flush()

    ensure_project(db, requester, "校园公益短片招募", AuditStatus.approved, LifecycleStatus.recruiting, ["视觉设计"], 30)
    ensure_project(db, requester, "社团数据整理", AuditStatus.pending, LifecycleStatus.recruiting, ["Python"], 25)
    active = ensure_project(db, requester, "校园活动数据平台", AuditStatus.approved, LifecycleStatus.in_progress, ["Python"], 18)
    completed = ensure_project(db, requester, "毕业季视觉设计", AuditStatus.approved, LifecycleStatus.completed, ["视觉设计"], 10)
    ensure_application(db, active, student, ApplicationStatus.accepted)
    ensure_application(db, completed, designer, ApplicationStatus.finished)
    if not db.scalar(select(Review).where(Review.project_id == completed.id, Review.student_id == designer.id)):
        db.add(Review(project_id=completed.id, reviewer_id=requester.id, student_id=designer.id, skill_score=5, communication_score=4, delivery_score=5, time_management_score=4, comment="成果完整，沟通顺畅"))
    db.flush()
    recalculate_student_skills(db, student.id)
    recalculate_student_skills(db, designer.id)
    db.commit()


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_database(db)
    print("SkillHub demo data is ready.")


if __name__ == "__main__":
    main()
