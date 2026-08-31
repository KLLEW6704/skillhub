from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.main import app
from app.models.user import User, UserRole
from app.models.skill import Skill


@pytest.fixture
def db_session(tmp_path: Path) -> Generator[Session, None, None]:
    database_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False)
    Base.metadata.create_all(engine)
    with TestingSessionLocal() as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def student_user(db_session: Session) -> User:
    user = User(
        username="student",
        email="student@example.com",
        password_hash=hash_password("Student123!"),
        role=UserRole.student,
        school="SkillHub University",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def student_headers(student_user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(student_user)}"}


@pytest.fixture
def requester_user(db_session: Session) -> User:
    user = User(
        username="requester",
        email="requester@example.com",
        password_hash=hash_password("Student123!"),
        role=UserRole.requester,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def requester_headers(requester_user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(requester_user)}"}


@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("Student123!"),
        role=UserRole.admin,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_headers(admin_user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(admin_user)}"}


@pytest.fixture
def student_skill(db_session: Session, student_user: User) -> Skill:
    skill = Skill(
        user_id=student_user.id,
        name="摄影",
        normalized_name="摄影",
        description="校园活动记录",
    )
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(skill)
    return skill


@pytest.fixture
def other_student_skill(db_session: Session) -> Skill:
    user = User(
        username="other_student",
        email="other@student.example.com",
        password_hash=hash_password("Student123!"),
        role=UserRole.student,
    )
    db_session.add(user)
    db_session.flush()
    skill = Skill(
        user_id=user.id,
        name="设计",
        normalized_name="设计",
    )
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(skill)
    return skill


@pytest.fixture
def tiny_png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"test-image"


@pytest.fixture
def inactive_token(db_session: Session) -> str:
    user = User(
        username="inactive",
        email="inactive@example.com",
        password_hash=hash_password("Student123!"),
        role=UserRole.student,
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return create_access_token(user)
