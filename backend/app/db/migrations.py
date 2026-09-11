import json

from sqlalchemy import inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.portfolio import Portfolio, PortfolioEvidence, PortfolioEvidenceSkill
from app.models.application import Application, ProjectInvitation
from app.models.collaboration import PositionCategory, ProjectPosition, ProjectTask, TaskStatus
from app.models.project import LifecycleStatus, Project
from app.models.project_validation import ProjectValidationRecord
from app.models.review import Review
from app.services.rubrics import project_rubric


def _add_sqlite_column(engine: Engine, table: str, name: str, definition: str) -> None:
    if engine.dialect.name != "sqlite":
        return
    columns = {column["name"] for column in inspect(engine).get_columns(table)}
    if name not in columns:
        with engine.begin() as connection:
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))


def run_additive_migrations(engine: Engine) -> None:
    """Create additive tables and give legacy portfolios private evidence records."""

    Base.metadata.create_all(engine)
    _add_sqlite_column(engine, "applications", "position_id", "INTEGER REFERENCES project_positions(id)")
    _add_sqlite_column(engine, "project_invitations", "position_id", "INTEGER REFERENCES project_positions(id)")
    _add_sqlite_column(engine, "reviews", "position_id", "INTEGER REFERENCES project_positions(id)")
    _add_sqlite_column(engine, "reviews", "rubric_category", "VARCHAR(30) NOT NULL DEFAULT 'general'")
    _add_sqlite_column(engine, "reviews", "rubric_version", "VARCHAR(80) NOT NULL DEFAULT 'general-performance-v1'")
    _add_sqlite_column(engine, "reviews", "criteria_scores_json", "TEXT NOT NULL DEFAULT '{}'")
    _add_sqlite_column(engine, "project_validation_records", "position_title", "VARCHAR(100)")
    _add_sqlite_column(engine, "project_validation_records", "position_category", "VARCHAR(30)")
    _add_sqlite_column(engine, "project_validation_records", "rubric_version", "VARCHAR(80)")
    _add_sqlite_column(engine, "project_validation_records", "criteria_scores_snapshot", "TEXT")
    with Session(engine) as db:
        portfolios = list(db.scalars(select(Portfolio)))
        for portfolio in portfolios:
            evidence = db.scalar(
                select(PortfolioEvidence).where(
                    PortfolioEvidence.portfolio_id == portfolio.id
                )
            )
            if evidence is None:
                evidence = PortfolioEvidence(portfolio_id=portfolio.id)
                db.add(evidence)
                db.flush()
            linked = db.scalar(
                select(PortfolioEvidenceSkill).where(
                    PortfolioEvidenceSkill.evidence_id == evidence.id,
                    PortfolioEvidenceSkill.skill_id == portfolio.skill_id,
                )
            )
            if linked is None:
                db.add(
                    PortfolioEvidenceSkill(
                        evidence_id=evidence.id, skill_id=portfolio.skill_id
                    )
                )
        projects = list(db.scalars(select(Project)))
        for project in projects:
            if not project.positions:
                position = ProjectPosition(
                    project_id=project.id,
                    code="general",
                    title="综合协作岗",
                    category=PositionCategory.general,
                    description="承接该项目原有的综合协作职责",
                    headcount=max(1, len([item for item in db.scalars(select(Application).where(Application.project_id == project.id))])),
                    required_skills_json=json.dumps(project.required_skills, ensure_ascii=False),
                    deliverables=project.deliverables or "按项目约定完成交付",
                    sort_order=0,
                )
                db.add(position)
                db.flush()
                project.positions.append(position)
            default_position = project.positions[0]
            for application in db.scalars(select(Application).where(Application.project_id == project.id, Application.position_id.is_(None))):
                application.position_id = default_position.id
            for invitation in db.scalars(select(ProjectInvitation).where(ProjectInvitation.project_id == project.id, ProjectInvitation.position_id.is_(None))):
                invitation.position_id = default_position.id
            if not project.tasks:
                status = TaskStatus.todo
                if project.lifecycle_status == LifecycleStatus.in_progress:
                    status = TaskStatus.in_progress
                elif project.lifecycle_status in {LifecycleStatus.awaiting_review, LifecycleStatus.completed}:
                    status = TaskStatus.done
                db.add(ProjectTask(
                    project_id=project.id,
                    position_id=default_position.id,
                    title="完成项目约定交付",
                    description=project.deliverables,
                    status=status,
                    due_date=project.deadline,
                    sort_order=0,
                ))
        for review in db.scalars(select(Review)):
            if review.position_id is None:
                application = db.scalar(select(Application).where(
                    Application.project_id == review.project_id,
                    Application.student_id == review.student_id,
                ))
                review.position_id = application.position_id if application else None
            if not review.criteria_scores:
                position = db.get(ProjectPosition, review.position_id) if review.position_id else None
                category = position.category if position else PositionCategory.general
                version, criteria = project_rubric(category)
                values = [review.skill_score, review.communication_score, review.delivery_score, review.time_management_score]
                review.rubric_category = category.value
                review.rubric_version = version
                review.criteria_scores_json = json.dumps(dict(zip(criteria, values)), ensure_ascii=False)
        for record in db.scalars(select(ProjectValidationRecord)):
            review = db.get(Review, record.review_id)
            if review and record.position_title is None:
                record.position_title = review.position_title
                record.position_category = review.rubric_category
                record.rubric_version = review.rubric_version
                record.criteria_scores_snapshot = review.criteria_scores_json
        db.commit()
