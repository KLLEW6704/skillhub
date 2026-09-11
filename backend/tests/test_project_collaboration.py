import json
from datetime import date, timedelta

from app.api.v1.projects import get_planning_model
from app.api.v1.assessments import get_vision_model


def collaboration_payload():
    return {
        "title": "校园技术节协作平台",
        "description": "为校园技术节建设报名与活动数据服务",
        "category": "技术实践",
        "deadline": (date.today() + timedelta(days=30)).isoformat(),
        "required_skills": ["Python", "数据分析"],
        "deliverables": "可运行服务、测试记录与分析报告",
        "acceptance_criteria": "全部事项完成并通过项目方验收",
        "positions": [
            {
                "code": "developer",
                "title": "后端开发",
                "category": "development",
                "description": "负责接口实现和测试",
                "headcount": 1,
                "required_skills": ["Python"],
                "deliverables": "接口代码与测试记录",
                "sort_order": 0,
            },
            {
                "code": "analyst",
                "title": "数据分析",
                "category": "data",
                "description": "负责数据清洗和指标解释",
                "headcount": 1,
                "required_skills": ["数据分析"],
                "deliverables": "分析脚本与报告",
                "sort_order": 1,
            },
        ],
        "tasks": [
            {
                "title": "实现报名接口",
                "description": "包含异常场景测试",
                "position_code": "developer",
                "sort_order": 0,
            }
        ],
    }


def test_multi_role_project_runs_shared_task_board_and_category_review(
    client, requester_headers, admin_headers, student_headers, student_user
):
    created = client.post("/api/v1/projects", headers=requester_headers, json=collaboration_payload())
    assert created.status_code == 201
    project = created.json()
    assert [position["category"] for position in project["positions"]] == ["development", "data"]
    client.post(f"/api/v1/admin/projects/{project['id']}/approve", headers=admin_headers)

    missing_position = client.post(
        f"/api/v1/projects/{project['id']}/applications",
        headers=student_headers,
        json={"message": "希望加入"},
    )
    assert missing_position.status_code == 422

    developer = project["positions"][0]
    application = client.post(
        f"/api/v1/projects/{project['id']}/applications",
        headers=student_headers,
        json={"message": "有接口开发经验", "position_id": developer["id"]},
    )
    assert application.status_code == 201
    assert application.json()["position"]["title"] == "后端开发"
    accepted = client.post(
        f"/api/v1/applications/{application.json()['id']}/accept",
        headers=requester_headers,
    )
    assert accepted.status_code == 200
    assert client.post(f"/api/v1/projects/{project['id']}/start", headers=requester_headers).status_code == 200

    student_workspace = client.get(f"/api/v1/projects/{project['id']}/workspace", headers=student_headers)
    assert student_workspace.status_code == 200
    body = student_workspace.json()
    assert body["can_manage"] is False
    assert body["members"][0]["position_title"] == "后端开发"
    task = body["tasks"][0]

    moved = client.patch(
        f"/api/v1/project-tasks/{task['id']}/status",
        headers=student_headers,
        json={"status": "in_progress", "expected_version": task["version"]},
    )
    assert moved.status_code == 200
    assert moved.json()["version"] == 2
    stale = client.patch(
        f"/api/v1/project-tasks/{task['id']}/status",
        headers=student_headers,
        json={"status": "done", "expected_version": 1},
    )
    assert stale.status_code == 409
    assert client.post(f"/api/v1/projects/{project['id']}/finish-work", headers=requester_headers).status_code == 409
    assert client.patch(
        f"/api/v1/project-tasks/{task['id']}/status",
        headers=student_headers,
        json={"status": "done", "expected_version": 2},
    ).status_code == 200
    assert client.post(f"/api/v1/projects/{project['id']}/finish-work", headers=requester_headers).status_code == 200

    criteria = {"功能正确性": 5, "代码质量": 4, "测试与可靠性": 4, "协作交付": 5}
    reviewed = client.post(
        f"/api/v1/projects/{project['id']}/reviews/{student_user.id}",
        headers=requester_headers,
        json={"criteria_scores": criteria, "comment": "接口稳定，测试记录完整"},
    )
    assert reviewed.status_code == 201
    assert reviewed.json()["rubric_category"] == "development"
    assert reviewed.json()["rubric_version"] == "development-performance-v1"
    assert reviewed.json()["criteria_scores"] == criteria
    validation = client.get(f"/api/v1/profiles/students/{student_user.id}/project-validations").json()[0]
    assert validation["position_title"] == "后端开发"
    assert validation["criteria_scores"] == criteria


class FakePlanningModel:
    model_name = "fake-planner"

    def __init__(self):
        self.calls = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        return json.dumps({"positions": collaboration_payload()["positions"], "tasks": collaboration_payload()["tasks"]}, ensure_ascii=False)


def test_ai_plan_is_an_editable_draft_and_does_not_publish(client, requester_headers):
    model = FakePlanningModel()
    client.app.dependency_overrides[get_planning_model] = lambda: model
    response = client.post(
        "/api/v1/projects/plan-draft",
        headers=requester_headers,
        json={"title": "技术节平台", "description": "完成报名和活动数据服务", "category": "技术实践", "deliverables": "可运行服务", "team_size": 4},
    )
    assert response.status_code == 200
    assert response.json()["positions"][0]["title"] == "后端开发"
    assert "不可信" in model.calls[0]["system_prompt"]
    assert "简体中文" in model.calls[0]["system_prompt"]
    assert client.get("/api/v1/projects/mine", headers=requester_headers).json() == []


class RepairingPlanningModel:
    model_name = "repairing-planner"

    def __init__(self):
        self.calls = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return json.dumps({
                "positions": [{
                    "code": "project_manager",
                    "title": "Project Manager",
                    "category": "operations",
                    "description": "Coordinate the schedule and final delivery.",
                    "headcount": 1,
                    "required_skills": ["project management"],
                    "deliverables": "Project plan and final report",
                    "sort_order": 0,
                }],
                "tasks": [{
                    "title": "Create the project schedule",
                    "description": "Define milestones and owners.",
                    "position_code": "project_manager",
                    "assignee_student_id": None,
                    "due_date": None,
                    "sort_order": 0,
                }],
            })
        return json.dumps({
            "positions": [{
                "code": "project_manager",
                "title": "项目统筹",
                "category": "operations",
                "description": "统筹活动排期、协作进度与最终交付。",
                "headcount": 1,
                "required_skills": ["项目管理"],
                "deliverables": "项目计划与结项报告",
                "sort_order": 0,
            }],
            "tasks": [{
                "title": "制定项目排期",
                "description": "明确里程碑与负责人。",
                "position_code": "project_manager",
                "assignee_student_id": None,
                "due_date": None,
                "sort_order": 0,
            }],
        }, ensure_ascii=False)


def test_ai_plan_repairs_english_user_facing_content_to_chinese(client, requester_headers):
    model = RepairingPlanningModel()
    client.app.dependency_overrides[get_planning_model] = lambda: model
    response = client.post(
        "/api/v1/projects/plan-draft",
        headers=requester_headers,
        json={"title": "迎新活动", "description": "策划并落地新生迎新活动", "category": "校园活动", "team_size": 4},
    )
    assert response.status_code == 200
    assert response.json()["positions"][0]["title"] == "项目统筹"
    assert response.json()["tasks"][0]["title"] == "制定项目排期"
    assert len(model.calls) == 2
    assert "仅把面向用户" in model.calls[1]["user_prompt"]


def test_project_draft_can_be_saved_partially_updated_and_consumed_on_publish(client, requester_headers):
    saved = client.post(
        "/api/v1/project-drafts",
        headers=requester_headers,
        json={"title": "只写了一半的活动", "description": "目前只确定了活动方向"},
    )
    assert saved.status_code == 201
    draft = saved.json()
    assert draft["payload"]["deadline"] == ""
    assert draft["payload"]["positions"] == []

    updated_payload = draft["payload"] | {
        "description": "补充了项目说明，但岗位和时间仍可稍后填写",
        "team_size": 6,
    }
    updated = client.patch(
        f"/api/v1/project-drafts/{draft['id']}",
        headers=requester_headers,
        json=updated_payload,
    )
    assert updated.status_code == 200
    assert updated.json()["payload"]["team_size"] == 6
    listed = client.get("/api/v1/project-drafts", headers=requester_headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [draft["id"]]

    publish_payload = collaboration_payload() | {"draft_id": draft["id"]}
    published = client.post("/api/v1/projects", headers=requester_headers, json=publish_payload)
    assert published.status_code == 201
    assert client.get("/api/v1/project-drafts", headers=requester_headers).json() == []


class FakeEvidenceModel:
    model_name = "fake-code-reviewer"

    def __init__(self):
        self.calls = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        return json.dumps({
            "observable_facts": [{"observation": "定义了 add 函数并返回两个参数之和", "evidence": {"source": "source_file", "reference": "solution.py 第 1–2 行"}}],
            "evidence_gaps": ["没有看到自动化测试"],
            "questions": [
                {"text": "如何验证边界输入？", "targets_gap": "测试证据"},
                {"text": "如何处理非数字输入？", "targets_gap": "异常处理"},
                {"text": "哪些代码由你完成？", "targets_gap": "个人贡献"},
            ],
        }, ensure_ascii=False)


def test_code_evidence_uses_source_file_and_code_rubric(
    client, student_headers, student_skill, tmp_path, monkeypatch
):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    portfolio = client.post(
        "/api/v1/portfolios",
        headers=student_headers,
        data={
            "skill_id": student_skill.id,
            "title": "加法接口练习",
            "description": "实现一个可复用的加法函数",
            "evidence_type": "code_project",
            "creation_context": "课程接口练习",
            "personal_role": "独立实现",
            "process_description": "先定义输入输出，再实现函数",
            "iteration_notes": "补充类型标注",
            "ai_processing_consent": "true",
        },
        files={"file": ("solution.py", b"def add(a: int, b: int):\n    return a + b\n", "text/x-python")},
    )
    assert portfolio.status_code == 201
    assert portfolio.json()["ai_supported"] is True
    model = FakeEvidenceModel()
    client.app.dependency_overrides[get_vision_model] = lambda: model
    observed = client.post(
        f"/api/v1/portfolios/{portfolio.json()['id']}/assessments",
        headers=student_headers,
    )
    assert observed.status_code == 201
    assert observed.json()["status"] == "succeeded"
    assert observed.json()["rubric_version"] == "code-v1"
    assert model.calls[0]["image_bytes"] is None
    assert "def add" in model.calls[0]["user_prompt"]
