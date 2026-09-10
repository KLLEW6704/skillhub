from datetime import datetime

def upload_evidence(client, student_headers, student_skill, tiny_png, **overrides):
    data = {
        "skill_id": student_skill.id,
        "title": "迎新季视觉海报",
        "description": "为校园迎新活动设计的信息海报",
        "evidence_type": "visual_poster",
        "creation_context": "迎新活动需要在线传播物料",
        "personal_role": "独立完成信息架构与视觉设计",
        "process_description": "先梳理信息层级，再完成两轮排版",
        "iteration_notes": "根据同学反馈提升日期与地点对比度",
        "visibility": "private",
        **overrides,
    }
    return client.post(
        "/api/v1/portfolios",
        headers=student_headers,
        data=data,
        files={"file": ("poster.png", tiny_png, "image/png")},
    )


def test_upload_rejects_disguised_image(
    client, student_headers, student_skill, tmp_path, monkeypatch
):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))

    response = client.post(
        "/api/v1/portfolios",
        headers=student_headers,
        data={"skill_id": student_skill.id, "title": "伪装图片"},
        files={"file": ("fake.png", b"not-an-image", "image/png")},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "文件内容不是有效图片"


def test_student_can_create_and_edit_structured_evidence(
    client, student_headers, student_skill, tiny_png, tmp_path, monkeypatch
):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    created = upload_evidence(
        client, student_headers, student_skill, tiny_png, ai_processing_consent=True
    )

    assert created.status_code == 201
    body = created.json()
    assert body["evidence_type"] == "visual_poster"
    assert body["visibility"] == "private"
    assert body["ai_supported"] is True
    assert body["ai_processing_consent_at"] is not None
    assert datetime.fromisoformat(body["ai_processing_consent_at"])

    updated = client.patch(
        f"/api/v1/portfolios/{body['id']}",
        headers=student_headers,
        json={
            "title": "迎新季视觉海报（二稿）",
            "visibility": "public",
            "iteration_notes": "第三轮补充无障碍配色检查",
        },
    )

    assert updated.status_code == 200
    assert updated.json()["title"].endswith("（二稿）")
    assert updated.json()["visibility"] == "public"


def test_public_profile_never_leaks_private_evidence(
    client, student_headers, student_skill, student_user, tiny_png, tmp_path, monkeypatch
):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    private_item = upload_evidence(client, student_headers, student_skill, tiny_png)
    public_item = upload_evidence(
        client,
        student_headers,
        student_skill,
        tiny_png,
        title="公开海报",
        visibility="public",
    )

    response = client.get(f"/api/v1/profiles/students/{student_user.id}")

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["portfolios"]}
    assert public_item.json()["id"] in ids
    assert private_item.json()["id"] not in ids


def test_requester_sees_identity_skills_message_and_only_selected_work(
    client,
    student_headers,
    student_skill,
    student_user,
    requester_headers,
    admin_headers,
    tiny_png,
    tmp_path,
    monkeypatch,
):
    from tests.test_applications import approved_project

    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    profile = client.patch(
        "/api/v1/profiles/me",
        headers=student_headers,
        json={"display_name": "林同学"},
    )
    assert profile.status_code == 200
    selected = upload_evidence(client, student_headers, student_skill, tiny_png).json()
    unselected = upload_evidence(
        client, student_headers, student_skill, tiny_png, title="未授权作品"
    ).json()
    project = approved_project(client, requester_headers, admin_headers)

    application = client.post(
        f"/api/v1/projects/{project['id']}/applications",
        headers=student_headers,
        json={"message": "我负责过同类海报", "portfolio_ids": [selected["id"]]},
    )
    applicants = client.get(
        f"/api/v1/projects/{project['id']}/applications",
        headers=requester_headers,
    )

    assert application.status_code == 201
    assert applicants.status_code == 200
    applicant = applicants.json()[0]
    assert applicant["student"]["display_name"] == "林同学"
    assert applicant["student"]["skills"][0]["name"] == student_skill.name
    assert applicant["message"] == "我负责过同类海报"
    assert [item["id"] for item in applicant["authorized_portfolios"]] == [
        selected["id"]
    ]
    assert unselected["id"] not in {
        item["id"] for item in applicant["authorized_portfolios"]
    }

    allowed = client.get(selected["file_url"], headers=requester_headers)
    denied = client.get(unselected["file_url"], headers=requester_headers)
    assert allowed.status_code == 200
    assert denied.status_code == 404


def test_application_cannot_grant_another_students_work(
    client,
    student_headers,
    requester_headers,
    admin_headers,
    db_session,
    other_student_skill,
):
    from app.models.portfolio import Portfolio
    from tests.test_applications import approved_project

    foreign = Portfolio(
        user_id=other_student_skill.user_id,
        skill_id=other_student_skill.id,
        title="他人作品",
        file_url="/uploads/foreign.png",
        file_type="image/png",
    )
    db_session.add(foreign)
    db_session.commit()
    project = approved_project(client, requester_headers, admin_headers)

    response = client.post(
        f"/api/v1/projects/{project['id']}/applications",
        headers=student_headers,
        json={"portfolio_ids": [foreign.id]},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "选择的作品不存在"
