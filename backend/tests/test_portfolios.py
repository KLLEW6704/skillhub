from pathlib import Path

from app.core.security import create_access_token
from app.models.user import User


def test_upload_portfolio_uses_generated_safe_filename(
    client, student_headers, student_skill, tiny_png, tmp_path: Path, monkeypatch
):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    response = client.post(
        "/api/v1/portfolios",
        headers=student_headers,
        data={
            "skill_id": student_skill.id,
            "title": "校园海报",
            "description": "迎新视觉",
        },
        files={"file": ("../../photo.png", tiny_png, "image/png")},
    )

    assert response.status_code == 201
    assert response.json()["file_url"] == f"/api/v1/portfolios/{response.json()['id']}/file"
    stored_files = list(upload_dir.iterdir())
    assert len(stored_files) == 1
    assert stored_files[0].name != "photo.png"
    assert stored_files[0].read_bytes() == tiny_png


def test_upload_rejects_executable(
    client, student_headers, student_skill, tmp_path: Path, monkeypatch
):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    response = client.post(
        "/api/v1/portfolios",
        headers=student_headers,
        data={"skill_id": student_skill.id, "title": "危险文件"},
        files={"file": ("run.exe", b"MZ-danger", "application/octet-stream")},
    )

    assert response.status_code == 415
    assert not upload_dir.exists() or list(upload_dir.iterdir()) == []


def test_upload_rejects_file_disguised_as_allowed_document(
    client, student_headers, student_skill, tmp_path: Path, monkeypatch
):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    response = client.post(
        "/api/v1/portfolios",
        headers=student_headers,
        data={"skill_id": student_skill.id, "title": "伪装文档"},
        files={"file": ("report.pdf", b"MZ-not-a-pdf", "application/pdf")},
    )

    assert response.status_code == 415
    assert not upload_dir.exists() or list(upload_dir.iterdir()) == []


def test_upload_rejects_oversized_file(
    client, student_headers, student_skill, tmp_path: Path, monkeypatch
):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("MAX_UPLOAD_MB", "1")
    response = client.post(
        "/api/v1/portfolios",
        headers=student_headers,
        data={"skill_id": student_skill.id, "title": "过大文件"},
        files={"file": ("large.png", b"x" * (1024 * 1024 + 1), "image/png")},
    )

    assert response.status_code == 413
    assert not upload_dir.exists() or list(upload_dir.iterdir()) == []


def test_cannot_attach_portfolio_to_another_students_skill(
    client, student_headers, other_student_skill, tiny_png, tmp_path: Path, monkeypatch
):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    response = client.post(
        "/api/v1/portfolios",
        headers=student_headers,
        data={"skill_id": other_student_skill.id, "title": "越权作品"},
        files={"file": ("photo.png", tiny_png, "image/png")},
    )

    assert response.status_code == 404
    assert not upload_dir.exists() or list(upload_dir.iterdir()) == []


def test_delete_portfolio_removes_owned_file(
    client, student_headers, student_skill, tiny_png, tmp_path: Path, monkeypatch
):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    created = client.post(
        "/api/v1/portfolios",
        headers=student_headers,
        data={"skill_id": student_skill.id, "title": "待删除作品"},
        files={"file": ("photo.png", tiny_png, "image/png")},
    )
    stored_path = next(upload_dir.iterdir())

    response = client.delete(
        f"/api/v1/portfolios/{created.json()['id']}", headers=student_headers
    )

    assert response.status_code == 204
    assert not stored_path.exists()


def test_skill_with_portfolio_evidence_cannot_be_deleted(
    client, student_headers, student_skill, tiny_png, tmp_path: Path, monkeypatch
):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    client.post(
        "/api/v1/portfolios",
        headers=student_headers,
        data={"skill_id": student_skill.id, "title": "保留证据"},
        files={"file": ("photo.png", tiny_png, "image/png")},
    )

    response = client.delete(
        f"/api/v1/skills/{student_skill.id}", headers=student_headers
    )

    assert response.status_code == 409


def test_student_can_save_and_resume_incomplete_portfolio_draft(
    client, student_headers, student_skill, tiny_png, tmp_path, monkeypatch
):
    created = client.post(
        "/api/v1/portfolios/drafts",
        headers=student_headers,
        json={
            "title": "尚未完成的视觉方案",
            "creation_context": "先记录创作背景，文件之后再补",
            "visibility": "private",
        },
    )

    assert created.status_code == 201
    assert created.json()["title"] == "尚未完成的视觉方案"
    assert created.json()["skill_id"] is None

    draft_id = created.json()["id"]
    updated = client.patch(
        f"/api/v1/portfolios/drafts/{draft_id}",
        headers=student_headers,
        json={
            "skill_id": student_skill.id,
            "title": "已补充技能的视觉方案",
            "related_skill_ids": [student_skill.id],
            "ai_processing_consent": True,
        },
    )
    drafts = client.get("/api/v1/portfolios/drafts", headers=student_headers)
    portfolios = client.get("/api/v1/portfolios", headers=student_headers)

    assert updated.status_code == 200
    assert updated.json()["related_skill_ids"] == [student_skill.id]
    assert updated.json()["creation_context"] == "先记录创作背景，文件之后再补"
    assert drafts.status_code == 200
    assert [item["id"] for item in drafts.json()] == [draft_id]
    assert portfolios.json() == []

    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    published = client.post(
        "/api/v1/portfolios",
        headers=student_headers,
        data={
            "skill_id": student_skill.id,
            "title": "已完成的视觉方案",
            "draft_id": draft_id,
        },
        files={"file": ("work.png", tiny_png, "image/png")},
    )

    assert published.status_code == 201
    assert client.get(
        "/api/v1/portfolios/drafts", headers=student_headers
    ).json() == []


def test_portfolio_draft_is_private_to_its_student(
    client, db_session, student_headers, other_student_skill
):
    created = client.post(
        "/api/v1/portfolios/drafts",
        headers=student_headers,
        json={"title": "私人草稿"},
    )
    other_user = db_session.get(User, other_student_skill.user_id)
    other_headers = {"Authorization": f"Bearer {create_access_token(other_user)}"}

    response = client.patch(
        f"/api/v1/portfolios/drafts/{created.json()['id']}",
        headers=other_headers,
        json={"title": "越权修改"},
    )

    assert response.status_code == 404


def test_non_student_cannot_read_portfolio_drafts(client, requester_headers):
    response = client.get("/api/v1/portfolios/drafts", headers=requester_headers)

    assert response.status_code == 403
