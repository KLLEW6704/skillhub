def registration_payload(**overrides):
    payload = {
        "username": "student_new",
        "email": "new@example.com",
        "password": "StrongPass123",
        "role": "student",
        "school": "SkillHub University",
        "college": "计算机学院",
        "major": "软件工程",
        "grade": "2025",
    }
    payload.update(overrides)
    return payload


def test_student_can_register(client):
    response = client.post("/api/v1/auth/register", json=registration_payload())

    assert response.status_code == 201
    assert response.json()["role"] == "student"
    assert "password" not in response.json()


def test_admin_role_cannot_be_self_registered(client):
    response = client.post(
        "/api/v1/auth/register",
        json=registration_payload(
            username="bad_admin", email="bad@example.com", role="admin"
        ),
    )

    assert response.status_code == 422


def test_reviewer_role_cannot_be_self_registered(client):
    response = client.post(
        "/api/v1/auth/register",
        json=registration_payload(
            username="bad_reviewer", email="reviewer@example.com", role="reviewer"
        ),
    )

    assert response.status_code == 422


def test_duplicate_username_is_rejected(client):
    assert client.post("/api/v1/auth/register", json=registration_payload()).status_code == 201

    response = client.post(
        "/api/v1/auth/register",
        json=registration_payload(email="another@example.com"),
    )

    assert response.status_code == 409


def test_login_returns_bearer_token(client, student_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": student_user.username, "password": "Student123!"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_rejects_wrong_password(client, student_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": student_user.username, "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_inactive_user_cannot_access_me(client, inactive_token):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {inactive_token}"},
    )

    assert response.status_code == 403
