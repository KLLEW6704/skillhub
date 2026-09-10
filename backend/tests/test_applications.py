from datetime import date, timedelta

from app.models.project import Project


def approved_project(client, requester_headers, admin_headers, *, deadline=None):
    response = client.post(
        "/api/v1/projects",
        headers=requester_headers,
        json={
            "title": "校园数据可视化",
            "description": "制作校园活动数据展示页面",
            "category": "技术实践",
            "budget": 800,
            "deadline": (deadline or date.today() + timedelta(days=20)).isoformat(),
            "required_skills": ["Python"],
        },
    )
    project = response.json()
    client.post(
        f"/api/v1/admin/projects/{project['id']}/approve", headers=admin_headers
    )
    return project


def apply(client, project_id, student_headers):
    return client.post(
        f"/api/v1/projects/{project_id}/applications",
        headers=student_headers,
        json={"message": "我有相关课程项目经验"},
    )


def test_student_applies_and_duplicate_is_rejected(
    client, requester_headers, admin_headers, student_headers
):
    project = approved_project(client, requester_headers, admin_headers)

    first = apply(client, project["id"], student_headers)
    duplicate = apply(client, project["id"], student_headers)

    assert first.status_code == 201
    assert first.json()["status"] == "pending"
    assert duplicate.status_code == 409

    stats = client.get("/api/v1/admin/stats", headers=admin_headers)
    assert stats.json()["applications"] == 1


def test_requester_cannot_apply(client, requester_headers, admin_headers):
    project = approved_project(client, requester_headers, admin_headers)

    response = client.post(
        f"/api/v1/projects/{project['id']}/applications",
        headers=requester_headers,
        json={"message": "错误角色"},
    )

    assert response.status_code == 403


def test_expired_project_rejects_application(
    client, requester_headers, admin_headers, student_headers, db_session
):
    project = approved_project(client, requester_headers, admin_headers)
    stored = db_session.get(Project, project["id"])
    stored.deadline = date.today() - timedelta(days=1)
    db_session.commit()

    response = apply(client, project["id"], student_headers)

    assert response.status_code == 409


def test_owner_accepts_application(
    client, requester_headers, admin_headers, student_headers
):
    project = approved_project(client, requester_headers, admin_headers)
    application = apply(client, project["id"], student_headers).json()

    response = client.post(
        f"/api/v1/applications/{application['id']}/accept",
        headers=requester_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


def test_project_cannot_start_without_accepted_member(
    client, requester_headers, admin_headers
):
    project = approved_project(client, requester_headers, admin_headers)

    response = client.post(
        f"/api/v1/projects/{project['id']}/start", headers=requester_headers
    )

    assert response.status_code == 409


def test_project_transitions_in_order(
    client, requester_headers, admin_headers, student_headers
):
    project = approved_project(client, requester_headers, admin_headers)
    application = apply(client, project["id"], student_headers).json()
    client.post(
        f"/api/v1/applications/{application['id']}/accept",
        headers=requester_headers,
    )

    premature_finish = client.post(
        f"/api/v1/projects/{project['id']}/finish-work", headers=requester_headers
    )
    started = client.post(
        f"/api/v1/projects/{project['id']}/start", headers=requester_headers
    )
    finished = client.post(
        f"/api/v1/projects/{project['id']}/finish-work", headers=requester_headers
    )

    assert premature_finish.status_code == 409
    assert started.json()["lifecycle_status"] == "in_progress"
    assert finished.json()["lifecycle_status"] == "awaiting_review"


def test_requester_invites_student_and_student_marks_invitation_viewed(
    client,
    requester_headers,
    admin_headers,
    student_headers,
    student_user,
):
    project = approved_project(client, requester_headers, admin_headers)

    invited = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        headers=requester_headers,
        json={"student_id": student_user.id, "message": "你的视觉档案很适合这个项目"},
    )
    listed = client.get("/api/v1/invitations/mine", headers=student_headers)
    viewed = client.post(
        f"/api/v1/invitations/{invited.json()['id']}/view",
        headers=student_headers,
    )

    assert invited.status_code == 201
    assert invited.json()["status"] == "pending"
    assert invited.json()["project"]["title"] == "校园数据可视化"
    assert listed.status_code == 200
    assert listed.json()[0]["message"] == "你的视觉档案很适合这个项目"
    assert viewed.json()["status"] == "viewed"
    assert viewed.json()["viewed_at"] is not None


def test_invitation_is_unique_and_becomes_applied_after_student_applies(
    client,
    requester_headers,
    admin_headers,
    student_headers,
    student_user,
):
    project = approved_project(client, requester_headers, admin_headers)
    payload = {"student_id": student_user.id, "message": "欢迎了解项目"}

    first = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        headers=requester_headers,
        json=payload,
    )
    duplicate = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        headers=requester_headers,
        json=payload,
    )
    application = apply(client, project["id"], student_headers)
    listed = client.get("/api/v1/invitations/mine", headers=student_headers)

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "已向该学生发送过此项目邀约"
    assert application.status_code == 201
    assert listed.json()[0]["status"] == "applied"


def test_only_project_owner_can_invite_students(
    client,
    requester_headers,
    admin_headers,
    student_headers,
    student_user,
):
    project = approved_project(client, requester_headers, admin_headers)
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "username": "invitation_requester",
            "email": "invitation@requester.example.com",
            "password": "StrongPass123",
            "role": "requester",
        },
    )
    assert registration.status_code == 201
    token = client.post(
        "/api/v1/auth/login",
        data={"username": "invitation_requester", "password": "StrongPass123"},
    ).json()["access_token"]

    not_owner = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        headers={"Authorization": f"Bearer {token}"},
        json={"student_id": student_user.id},
    )
    wrong_role = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        headers=student_headers,
        json={"student_id": student_user.id},
    )

    assert not_owner.status_code == 404
    assert wrong_role.status_code == 403
