from pathlib import Path


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
