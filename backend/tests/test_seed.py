from sqlalchemy import func, select

from app.models.application import Application
from app.models.portfolio import Portfolio
from app.models.project import Project
from app.models.review import Review
from app.models.skill import Skill
from app.models.user import User
from app.seed import seed_database


def table_counts(db_session):
    return {
        "users": db_session.scalar(select(func.count(User.id))) or 0,
        "skills": db_session.scalar(select(func.count(Skill.id))) or 0,
        "portfolios": db_session.scalar(select(func.count(Portfolio.id))) or 0,
        "projects": db_session.scalar(select(func.count(Project.id))) or 0,
        "applications": db_session.scalar(select(func.count(Application.id))) or 0,
        "reviews": db_session.scalar(select(func.count(Review.id))) or 0,
    }


def test_seed_is_idempotent(db_session):
    seed_database(db_session)
    first_counts = table_counts(db_session)
    seed_database(db_session)

    assert table_counts(db_session) == first_counts
    assert first_counts["users"] >= 4
    assert first_counts["projects"] >= 4
    assert first_counts["skills"] >= 2
    assert first_counts["applications"] >= 2
    assert first_counts["reviews"] >= 1


def test_seed_creates_documented_demo_accounts(db_session):
    seed_database(db_session)

    usernames = set(db_session.scalars(select(User.username)))

    assert {"admin", "student", "designer", "campus_org"} <= usernames


def test_seeded_student_can_login_and_read_current_user(client, db_session):
    seed_database(db_session)
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "student", "password": "Student123!"},
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "student"
