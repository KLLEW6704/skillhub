from datetime import date, timedelta


def project_payload(**overrides):
    payload = {
        "title": "校园毕业季影像记录",
        "description": "为毕业季活动拍摄照片并制作回顾内容",
        "category": "校园文化",
        "budget": 1200,
        "deadline": (date.today() + timedelta(days=30)).isoformat(),
        "required_skills": ["摄影", "视频剪辑"],
        "deliverables": "精选照片 30 张与 90 秒回顾短片",
        "acceptance_criteria": "画面清晰、授权完整，并在截止日前交付",
    }
    payload.update(overrides)
    return payload


def create_project(client, requester_headers, **overrides):
    return client.post(
        "/api/v1/projects",
        headers=requester_headers,
        json=project_payload(**overrides),
    )


def test_requester_creates_pending_project(client, requester_headers):
    response = create_project(client, requester_headers)

    assert response.status_code == 201
    assert response.json()["audit_status"] == "pending"
    assert response.json()["lifecycle_status"] == "recruiting"
    assert response.json()["required_skills"] == ["摄影", "视频剪辑"]
    assert response.json()["deliverables"] == "精选照片 30 张与 90 秒回顾短片"
    assert "截止日前" in response.json()["acceptance_criteria"]


def test_student_cannot_create_project(client, student_headers):
    response = client.post(
        "/api/v1/projects", headers=student_headers, json=project_payload()
    )

    assert response.status_code == 403


def test_only_creator_can_edit_pending_project(
    client, requester_headers, db_session
):
    project = create_project(client, requester_headers).json()
    other = client.post(
        "/api/v1/auth/register",
        json={
            "username": "other_requester",
            "email": "other@requester.example.com",
            "password": "StrongPass123",
            "role": "requester",
        },
    )
    assert other.status_code == 201
    token = client.post(
        "/api/v1/auth/login",
        data={"username": "other_requester", "password": "StrongPass123"},
    ).json()["access_token"]

    forbidden = client.patch(
        f"/api/v1/projects/{project['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "越权修改"},
    )
    allowed = client.patch(
        f"/api/v1/projects/{project['id']}",
        headers=requester_headers,
        json={"title": "毕业季影像志"},
    )

    assert forbidden.status_code == 404
    assert allowed.status_code == 200
    assert allowed.json()["title"] == "毕业季影像志"


def test_admin_approves_project_and_public_filter_finds_it(
    client, requester_headers, admin_headers
):
    project = create_project(client, requester_headers).json()

    approved = client.post(
        f"/api/v1/admin/projects/{project['id']}/approve", headers=admin_headers
    )
    response = client.get(
        "/api/v1/projects",
        params={"skill": "摄影", "category": "校园文化", "keyword": "毕业季"},
    )

    assert approved.status_code == 200
    assert approved.json()["audit_status"] == "approved"
    assert [item["id"] for item in response.json()["items"]] == [project["id"]]


def test_non_admin_cannot_audit_project(client, requester_headers):
    project = create_project(client, requester_headers).json()

    response = client.post(
        f"/api/v1/admin/projects/{project['id']}/approve",
        headers=requester_headers,
    )

    assert response.status_code == 403


def test_rejected_project_is_not_public(
    client, requester_headers, admin_headers
):
    project = create_project(client, requester_headers).json()
    rejected = client.post(
        f"/api/v1/admin/projects/{project['id']}/reject", headers=admin_headers
    )

    response = client.get("/api/v1/projects")

    assert rejected.status_code == 200
    assert rejected.json()["audit_status"] == "rejected"
    assert response.json()["items"] == []


def test_admin_stats_and_user_status(client, admin_headers, student_user):
    stats = client.get("/api/v1/admin/stats", headers=admin_headers)
    disabled = client.patch(
        f"/api/v1/admin/users/{student_user.id}/status",
        headers=admin_headers,
        json={"is_active": False},
    )

    assert stats.status_code == 200
    assert stats.json()["users"] >= 2
    assert disabled.status_code == 200
    assert disabled.json()["is_active"] is False
