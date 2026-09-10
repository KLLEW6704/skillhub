from app.models.portfolio import Portfolio


def test_student_registration_creates_editable_profile(client):
    registration = {
        "username": "profile_student",
        "email": "profile@student.example.com",
        "password": "StrongPass123",
        "role": "student",
        "school": "SkillHub University",
    }
    registered = client.post("/api/v1/auth/register", json=registration)
    token = client.post(
        "/api/v1/auth/login",
        data={"username": registration["username"], "password": registration["password"]},
    ).json()["access_token"]

    response = client.patch(
        "/api/v1/profiles/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"display_name": "林同学", "bio": "数据产品学习者"},
    )

    assert registered.status_code == 201
    assert response.status_code == 200
    assert response.json()["display_name"] == "林同学"


def test_requester_registration_creates_requester_profile(client):
    registration = {
        "username": "campus_team",
        "email": "team@example.com",
        "password": "StrongPass123",
        "role": "requester",
    }
    client.post("/api/v1/auth/register", json=registration)
    token = client.post(
        "/api/v1/auth/login",
        data={"username": registration["username"], "password": registration["password"]},
    ).json()["access_token"]

    response = client.patch(
        "/api/v1/profiles/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"organization_name": "校园媒体中心", "organization_type": "学生组织"},
    )

    assert response.status_code == 200
    assert response.json()["organization_name"] == "校园媒体中心"


def test_student_adds_skill(client, student_headers):
    response = client.post(
        "/api/v1/skills",
        headers=student_headers,
        json={"name": "Python", "description": "数据处理与接口开发"},
    )

    assert response.status_code == 201
    assert response.json()["level"] == 1
    assert response.json()["growth_score"] == 0


def test_requester_cannot_add_skill(client, requester_headers):
    response = client.post(
        "/api/v1/skills",
        headers=requester_headers,
        json={"name": "摄影", "description": "活动记录"},
    )

    assert response.status_code == 403


def test_duplicate_normalized_skill_name_is_rejected(client, student_headers):
    first = client.post(
        "/api/v1/skills", headers=student_headers, json={"name": " Python "}
    )
    duplicate = client.post(
        "/api/v1/skills", headers=student_headers, json={"name": "python"}
    )

    assert first.status_code == 201
    assert first.json()["name"] == "Python"
    assert duplicate.status_code == 409


def test_public_student_profile_contains_skill_growth(client, student_headers, student_user):
    client.post(
        "/api/v1/skills", headers=student_headers, json={"name": "数据分析"}
    )

    response = client.get(f"/api/v1/profiles/students/{student_user.id}")

    assert response.status_code == 200
    assert response.json()["skills"][0]["level"] == 1
    assert response.json()["skills"][0]["growth_score"] == 0


def test_student_can_update_and_delete_unlinked_skill(client, student_headers):
    created = client.post(
        "/api/v1/skills",
        headers=student_headers,
        json={"name": "Python", "description": "数据处理"},
    ).json()

    updated = client.patch(
        f"/api/v1/skills/{created['id']}",
        headers=student_headers,
        json={"name": "Python 自动化", "description": "数据处理与自动化"},
    )
    deleted = client.delete(
        f"/api/v1/skills/{created['id']}", headers=student_headers
    )

    assert updated.status_code == 200
    assert updated.json()["name"] == "Python 自动化"
    assert deleted.status_code == 204
    assert client.get("/api/v1/skills", headers=student_headers).json() == []


def test_skill_linked_to_evidence_cannot_be_deleted(
    client, student_headers, student_skill, student_user, db_session
):
    db_session.add(
        Portfolio(
            user_id=student_user.id,
            skill_id=student_skill.id,
            title="关联作品",
            file_url="/uploads/evidence.png",
            file_type="image/png",
        )
    )
    db_session.commit()

    response = client.delete(
        f"/api/v1/skills/{student_skill.id}", headers=student_headers
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "技能仍有关联作品，不能删除"
