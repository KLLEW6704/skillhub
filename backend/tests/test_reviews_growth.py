from datetime import date, timedelta

import pytest

from app.models.application import Application, ApplicationStatus
from app.models.portfolio import Portfolio
from app.models.project import AuditStatus, LifecycleStatus, Project, ProjectRequiredSkill
from app.models.project_validation import ProjectValidationRecord
from app.services.growth import level_for_score


@pytest.mark.parametrize(
    ("score", "level"),
    [(0, 1), (19, 1), (20, 2), (59, 2), (60, 3), (119, 3), (120, 4)],
)
def test_level_thresholds(score, level):
    assert level_for_score(score) == level


@pytest.fixture
def awaiting_review_evidence(db_session, requester_user, student_user, student_skill):
    project = Project(
        creator_id=requester_user.id,
        title="校园摄影实践",
        description="记录校园文化活动全过程",
        category="校园文化",
        deadline=date.today() + timedelta(days=10),
        audit_status=AuditStatus.approved,
        lifecycle_status=LifecycleStatus.awaiting_review,
        skill_requirements=[ProjectRequiredSkill(skill_name="摄影")],
    )
    db_session.add(project)
    db_session.flush()
    application = Application(
        project_id=project.id,
        student_id=student_user.id,
        message="擅长活动摄影",
        status=ApplicationStatus.accepted,
    )
    portfolio = Portfolio(
        user_id=student_user.id,
        skill_id=student_skill.id,
        title="摄影作品",
        file_url="/uploads/example.png",
        file_type="image/png",
    )
    db_session.add_all([application, portfolio])
    db_session.commit()
    return project, application


def review_payload(**overrides):
    payload = {
        "skill_score": 4,
        "communication_score": 4,
        "delivery_score": 4,
        "time_management_score": 4,
        "comment": "按时完成，成果清晰",
    }
    payload.update(overrides)
    return payload


def test_review_completes_application_project_and_recalculates_growth(
    client,
    requester_headers,
    student_user,
    student_skill,
    awaiting_review_evidence,
    db_session,
):
    project, application = awaiting_review_evidence

    response = client.post(
        f"/api/v1/projects/{project.id}/reviews/{student_user.id}",
        headers=requester_headers,
        json=review_payload(),
    )

    db_session.refresh(application)
    db_session.refresh(project)
    db_session.refresh(student_skill)
    assert response.status_code == 201
    assert application.status == ApplicationStatus.finished
    assert project.lifecycle_status == LifecycleStatus.completed
    assert student_skill.growth_score == 42
    assert student_skill.level == 2
    validation = db_session.query(ProjectValidationRecord).one()
    assert validation.project_id == project.id
    assert validation.student_id == student_user.id
    public = client.get(
        f"/api/v1/profiles/students/{student_user.id}/project-validations"
    )
    assert public.status_code == 200
    assert public.json()[0]["project_title"] == "校园摄影实践"
    assert public.json()[0]["required_skills"] == ["摄影"]


def test_review_scores_must_be_between_one_and_five(
    client, requester_headers, student_user, awaiting_review_evidence
):
    project, _ = awaiting_review_evidence

    response = client.post(
        f"/api/v1/projects/{project.id}/reviews/{student_user.id}",
        headers=requester_headers,
        json=review_payload(skill_score=6),
    )

    assert response.status_code == 422


def test_duplicate_review_is_rejected(
    client, requester_headers, student_user, awaiting_review_evidence
):
    project, _ = awaiting_review_evidence
    url = f"/api/v1/projects/{project.id}/reviews/{student_user.id}"

    assert client.post(url, headers=requester_headers, json=review_payload()).status_code == 201
    duplicate = client.post(url, headers=requester_headers, json=review_payload())

    assert duplicate.status_code == 409
