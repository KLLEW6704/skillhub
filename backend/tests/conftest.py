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
