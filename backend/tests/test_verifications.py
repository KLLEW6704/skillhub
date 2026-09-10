import json

from app.api.v1.assessments import get_vision_model
from app.models.verification import ReviewDecision, SkillVerification, VerificationStatus
from tests.test_assessments import (
    CRITERIA,
    FakeVisionModel,
    OBSERVATION_RESULT,
    create_visual_evidence,
    rubric_result,
)


def create_pending_verification(
    client,
    student_headers,
    student_skill,
    tiny_png,
    tmp_path,
    monkeypatch,
):
    portfolio = create_visual_evidence(
        client, student_headers, student_skill, tiny_png, tmp_path, monkeypatch
    )
    model = FakeVisionModel(
        [
            json.dumps(OBSERVATION_RESULT, ensure_ascii=False),
            json.dumps(rubric_result((3, 3, 3, 3, 3)), ensure_ascii=False),
        ]
    )
    client.app.dependency_overrides[get_vision_model] = lambda: model
    observation = client.post(
        f"/api/v1/portfolios/{portfolio['id']}/assessments",
        headers=student_headers,
    ).json()
    reassessment = client.post(
        f"/api/v1/assessments/{observation['run_number']}/answers",
        headers=student_headers,
        json={
            "answers": [
                {"question_id": item["id"], "answer": f"有依据的回答 {index + 1}"}
                for index, item in enumerate(observation["questions"])
            ]
        },
    ).json()
    return portfolio, observation, reassessment


def test_only_admin_can_grant_reviewer_role(
    client, admin_headers, student_headers, requester_user
):
    forbidden = client.patch(
        f"/api/v1/admin/users/{requester_user.id}/role",
        headers=student_headers,
        json={"role": "reviewer"},
    )
    granted = client.patch(
        f"/api/v1/admin/users/{requester_user.id}/role",
        headers=admin_headers,
        json={"role": "reviewer"},
    )

    assert forbidden.status_code == 403
    assert granted.status_code == 200
    assert granted.json()["role"] == "reviewer"


def test_successful_reassessment_creates_pending_human_verification(
    client,
    student_headers,
    student_skill,
    tiny_png,
    tmp_path,
    monkeypatch,
    db_session,
):
    portfolio, _, reassessment = create_pending_verification(
        client,
        student_headers,
        student_skill,
        tiny_png,
        tmp_path,
        monkeypatch,
    )

    verification = db_session.query(SkillVerification).one()
    assert verification.assessment_run_id == reassessment["id"]
    assert verification.portfolio_id == portfolio["id"]
    assert verification.status == VerificationStatus.pending_human_review
    mine = client.get("/api/v1/verifications/mine", headers=student_headers)
    assert mine.status_code == 200
    assert mine.json()[0]["status"] == "pending_human_review"


def test_reviewer_assignment_exposes_evidence_defense_and_rubric(
    client,
    student_headers,
    student_skill,
    admin_headers,
    reviewer_user,
    reviewer_headers,
    tiny_png,
    tmp_path,
    monkeypatch,
    db_session,
):
    create_pending_verification(
        client,
        student_headers,
        student_skill,
        tiny_png,
        tmp_path,
        monkeypatch,
    )
    verification = db_session.query(SkillVerification).one()

    assigned = client.post(
        f"/api/v1/admin/verifications/{verification.id}/assign",
        headers=admin_headers,
        json={"reviewer_id": reviewer_user.id},
    )
    queue = client.get("/api/v1/reviewer/assignments", headers=reviewer_headers)

    assert assigned.status_code == 200
    admin_queue = client.get(
        "/api/v1/admin/verifications?status=pending_human_review",
        headers=admin_headers,
    )
    assert admin_queue.status_code == 200
    assert admin_queue.json()[0]["id"] == verification.id
    assert queue.status_code == 200
    item = queue.json()[0]
    assert item["verification"]["status"] == "pending_human_review"
    assert item["evidence"]["title"] == "迎新视觉海报"
    assert len(item["defense"]) == 3
    assert [row["criterion"] for row in item["ai_result"]["criteria"]] == CRITERIA
    file_response = client.get(item["evidence"]["file_url"], headers=reviewer_headers)
    assert file_response.status_code == 200


def test_requester_sees_only_authorized_ai_summary_with_pending_notice(
    client,
    student_headers,
    student_skill,
    requester_headers,
    admin_headers,
    tiny_png,
    tmp_path,
    monkeypatch,
):
    from tests.test_applications import approved_project

    portfolio, _, _ = create_pending_verification(
        client,
        student_headers,
        student_skill,
        tiny_png,
        tmp_path,
        monkeypatch,
    )
    project = approved_project(client, requester_headers, admin_headers)
    client.post(
        f"/api/v1/projects/{project['id']}/applications",
        headers=student_headers,
        json={"portfolio_ids": [portfolio["id"]]},
    )

    applicants = client.get(
        f"/api/v1/projects/{project['id']}/applications",
        headers=requester_headers,
    ).json()

    authorized = applicants[0]["authorized_portfolios"][0]
    assert authorized["ai_assessment"]["total_score"] == 75.0
    assert authorized["verification_status"] == "pending_human_review"
    assert authorized["result_label"] == "AI 辅助初评、待人工复核"


def test_human_score_changes_require_reason_and_save_before_after_diff(
    client,
    student_headers,
    student_skill,
    admin_headers,
    reviewer_user,
    reviewer_headers,
    tiny_png,
    tmp_path,
    monkeypatch,
    db_session,
):
    create_pending_verification(
        client,
        student_headers,
        student_skill,
        tiny_png,
        tmp_path,
        monkeypatch,
    )
    verification = db_session.query(SkillVerification).one()
    client.post(
        f"/api/v1/admin/verifications/{verification.id}/assign",
        headers=admin_headers,
        json={"reviewer_id": reviewer_user.id},
    )

    no_reason = client.post(
        f"/api/v1/reviewer/verifications/{verification.id}/decision",
        headers=reviewer_headers,
        json={
            "outcome": "verified",
            "reason": "",
            "adjusted_scores": {CRITERIA[0]: 4},
        },
    )
    accepted = client.post(
        f"/api/v1/reviewer/verifications/{verification.id}/decision",
        headers=reviewer_headers,
        json={
            "outcome": "verified",
            "reason": "答辩提供了额外受众调研证据",
            "adjusted_scores": {CRITERIA[0]: 4},
        },
    )

    assert no_reason.status_code == 422
    assert accepted.status_code == 201
    assert accepted.json()["status"] == "verified"
    assert client.get(
        "/api/v1/reviewer/assignments", headers=reviewer_headers
    ).json() == []
    decision = db_session.query(ReviewDecision).one()
    before = json.loads(decision.before_result)
    after = json.loads(decision.after_result)
    assert before["criteria"][0]["score"] == 3
    assert after["criteria"][0]["score"] == 4
    assert decision.reason == "答辩提供了额外受众调研证据"


def test_only_verified_result_gets_pilot_credential_and_public_safe_record(
    client,
    student_headers,
    student_skill,
    admin_headers,
    reviewer_user,
    reviewer_headers,
    tiny_png,
    tmp_path,
    monkeypatch,
    db_session,
):
    create_pending_verification(
        client,
        student_headers,
        student_skill,
        tiny_png,
        tmp_path,
        monkeypatch,
    )
    verification = db_session.query(SkillVerification).one()
    client.post(
        f"/api/v1/admin/verifications/{verification.id}/assign",
        headers=admin_headers,
        json={"reviewer_id": reviewer_user.id},
    )
    decided = client.post(
        f"/api/v1/reviewer/verifications/{verification.id}/decision",
        headers=reviewer_headers,
        json={"outcome": "verified", "reason": "证据与答辩内容可以相互印证"},
    ).json()

    credential = decided["credential"]
    assert credential["name"] == "SkillHub 试行技能徽章"
    assert credential["credential_number"].startswith("SH-PILOT-")
    public = client.get(
        f"/api/v1/credentials/{credential['credential_number']}"
    )
    qr = client.get(
        f"/api/v1/credentials/{credential['credential_number']}/qr"
    )

    assert public.status_code == 200
    public_text = json.dumps(public.json(), ensure_ascii=False).lower()
    assert public.json()["status"] == "active"
    assert public.json()["rubric_version"] == "visual-poster-v1"
    assert public.json()["issuer"] == reviewer_user.username
    assert "email" not in public_text
    assert "api_key" not in public_text
    assert "raw_output" not in public_text
    assert "学校官方认证" not in public_text
    assert qr.status_code == 200
    assert qr.headers["content-type"].startswith("image/png")
    public_list = client.get(
        f"/api/v1/profiles/students/{student_skill.user_id}/verified-credentials"
    )
    assert public_list.status_code == 200
    assert public_list.json()[0]["credential_number"] == credential["credential_number"]


def test_more_evidence_decision_never_issues_credential(
    client,
    student_headers,
    student_skill,
    admin_headers,
    reviewer_user,
    reviewer_headers,
    tiny_png,
    tmp_path,
    monkeypatch,
    db_session,
):
    create_pending_verification(
        client,
        student_headers,
        student_skill,
        tiny_png,
        tmp_path,
        monkeypatch,
    )
    verification = db_session.query(SkillVerification).one()
    client.post(
        f"/api/v1/admin/verifications/{verification.id}/assign",
        headers=admin_headers,
        json={"reviewer_id": reviewer_user.id},
    )

    decision = client.post(
        f"/api/v1/reviewer/verifications/{verification.id}/decision",
        headers=reviewer_headers,
        json={"outcome": "more_evidence", "reason": "需要补充目标受众验证记录"},
    )

    assert decision.status_code == 201
    assert decision.json()["status"] == "more_evidence"
    assert decision.json()["credential"] is None


def test_admin_revocation_is_public_and_audited(
    client,
    student_headers,
    student_skill,
    admin_headers,
    reviewer_user,
    reviewer_headers,
    tiny_png,
    tmp_path,
    monkeypatch,
    db_session,
):
    create_pending_verification(
        client,
        student_headers,
        student_skill,
        tiny_png,
        tmp_path,
        monkeypatch,
    )
    verification = db_session.query(SkillVerification).one()
    client.post(
        f"/api/v1/admin/verifications/{verification.id}/assign",
        headers=admin_headers,
        json={"reviewer_id": reviewer_user.id},
    )
    decided = client.post(
        f"/api/v1/reviewer/verifications/{verification.id}/decision",
        headers=reviewer_headers,
        json={"outcome": "verified", "reason": "材料充分"},
    ).json()
    number = decided["credential"]["credential_number"]

    revoked = client.post(
        f"/api/v1/admin/credentials/{number}/revoke",
        headers=admin_headers,
        json={"reason": "学生主动撤回公开授权"},
    )
    public = client.get(f"/api/v1/credentials/{number}")

    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    assert public.json()["status"] == "revoked"
