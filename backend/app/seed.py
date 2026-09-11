from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

from PIL import Image, ImageDraw
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.assessment import (
    AssessmentRun,
    AssessmentRunEvent,
    AssessmentStage,
    AssessmentStatus,
    DefenseQuestion,
)
from app.models.application import Application, ApplicationStatus, InvitationStatus, ProjectInvitation
from app.models.collaboration import PositionCategory, ProjectPosition, ProjectTask, TaskStatus
from app.models.portfolio import (
    EvidenceVisibility,
    Portfolio,
    PortfolioEvidence,
    PortfolioEvidenceSkill,
)
from app.models.profile import RequesterProfile, StudentProfile
from app.models.project_validation import ProjectValidationRecord
from app.models.project import (
    AuditStatus,
    LifecycleStatus,
    Project,
    ProjectDeliveryRequirements,
    ProjectRequiredSkill,
)
from app.models.review import Review
from app.models.skill import Skill
from app.models.user import User, UserRole
from app.models.verification import (
    ReviewAssignment,
    ReviewDecision,
    SkillCredential,
    SkillVerification,
    VerificationStatus,
)
from app.services.growth import recalculate_student_skills
from app.services.rubrics import evidence_rubric, project_rubric


DEMO_PASSWORD = "Student123!"


def ensure_user(db: Session, username: str, email: str, role: UserRole, **fields) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if user:
        if user.email != email:
            user.email = email
            db.flush()
        return user
    user = User(username=username, email=email, password_hash=hash_password(DEMO_PASSWORD), role=role, **fields)
    db.add(user); db.flush()
    if role == UserRole.student:
        db.add(StudentProfile(user_id=user.id, display_name=fields.get("display_name", username)))
    elif role == UserRole.requester:
        db.add(RequesterProfile(user_id=user.id, organization_name="校园创新中心", organization_type="校园组织", description="发布真实校园实践项目"))
    db.flush()
    return user


def ensure_skill(db: Session, user: User, name: str, description: str) -> Skill:
    normalized = name.casefold()
    skill = db.scalar(select(Skill).where(Skill.user_id == user.id, Skill.normalized_name == normalized))
    if skill:
        return skill
    skill = Skill(user_id=user.id, name=name, normalized_name=normalized, description=description)
    db.add(skill); db.flush()
    return skill


def render_demo_asset(path: Path, *, title: str, accent: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1200, 800), "#f4efe5")
    draw = ImageDraw.Draw(image)
    draw.rectangle((70, 70, 1130, 730), fill="#fffaf0", outline="#222222", width=4)
    draw.rectangle((70, 70, 1130, 205), fill=accent)
    draw.text((105, 112), "SKILLHUB DEMO SAMPLE", fill="white")
    draw.text((105, 280), title, fill="#222222")
    draw.line((105, 355, 1095, 355), fill="#222222", width=3)
    draw.text((105, 405), "Evidence -> AI defense -> Human review", fill="#555555")
    draw.text((105, 650), "DEMO ONLY / NOT A REAL STUDENT WORK", fill="#a33b2b")
    image.save(path, format="PNG", optimize=True)


def ensure_demo_portfolio(
    db: Session,
    user: User,
    skill: Skill,
    *,
    title: str,
    legacy_title: str,
    filename: str,
    evidence_type: str,
) -> Portfolio:
    portfolio = db.scalar(
        select(Portfolio).where(
            Portfolio.user_id == user.id,
            Portfolio.title.in_([title, legacy_title]),
        )
    )
    if portfolio is None:
        portfolio = Portfolio(
            user_id=user.id,
            skill_id=skill.id,
            title=title,
            description="演示样本，非真实学生成果；用于验证 SkillHub 作品证据流程。",
            file_url=f"/uploads/{filename}",
            file_type="image/png",
        )
        db.add(portfolio)
        db.flush()
    else:
        portfolio.title = title
        portfolio.description = "演示样本，非真实学生成果；用于验证 SkillHub 作品证据流程。"
        portfolio.file_url = f"/uploads/{filename}"
        portfolio.file_type = "image/png"
    evidence = db.scalar(
        select(PortfolioEvidence).where(
            PortfolioEvidence.portfolio_id == portfolio.id
        )
    )
    if evidence is None:
        evidence = PortfolioEvidence(
            portfolio_id=portfolio.id,
            evidence_type=evidence_type,
            creation_context="SkillHub 功能演示场景",
            personal_role="系统演示数据，无真实学生贡献声明",
            process_description="由种子脚本生成的稳定视觉样例",
            iteration_notes="仅用于产品流程验证",
            visibility=EvidenceVisibility.public,
        )
        db.add(evidence)
        db.flush()
    else:
        evidence.evidence_type = evidence_type
        evidence.visibility = EvidenceVisibility.public
    link = db.scalar(
        select(PortfolioEvidenceSkill).where(
            PortfolioEvidenceSkill.evidence_id == evidence.id,
            PortfolioEvidenceSkill.skill_id == skill.id,
        )
    )
    if link is None:
        db.add(PortfolioEvidenceSkill(evidence_id=evidence.id, skill_id=skill.id))
    return portfolio


def ensure_project(db: Session, creator: User, title: str, audit: AuditStatus, lifecycle: LifecycleStatus, skills: list[str], days: int) -> Project:
    project = db.scalar(select(Project).where(Project.title == title))
    if project:
        if project.delivery_requirements is None:
            project.delivery_requirements = ProjectDeliveryRequirements(
                deliverables=f"{title}成果包与交付说明",
                acceptance_criteria="按约定范围完整交付，并由项目方依据成果质量与时间要求验收",
            )
        return project
    project = Project(
        creator_id=creator.id,
        title=title,
        description=f"{title}，用于 SkillHub 课程演示。",
        category="校园实践",
        budget=1000,
        deadline=date.today() + timedelta(days=days),
        audit_status=audit,
        lifecycle_status=lifecycle,
        skill_requirements=[ProjectRequiredSkill(skill_name=name) for name in skills],
        delivery_requirements=ProjectDeliveryRequirements(
            deliverables=f"{title}成果包与交付说明",
            acceptance_criteria="按约定范围完整交付，并由项目方依据成果质量与时间要求验收",
        ),
    )
    db.add(project); db.flush()
    return project


def ensure_application(db: Session, project: Project, student: User, status: ApplicationStatus) -> Application:
    application = db.scalar(select(Application).where(Application.project_id == project.id, Application.student_id == student.id))
    if application:
        return application
    application = Application(project_id=project.id, student_id=student.id, message="希望把课堂技能用于真实校园场景", status=status)
    db.add(application); db.flush()
    return application


def ensure_position(db: Session, project: Project, *, code: str, title: str, category: PositionCategory, description: str, skills: list[str], deliverables: str, headcount: int = 1) -> ProjectPosition:
    position = db.scalar(select(ProjectPosition).where(ProjectPosition.project_id == project.id, ProjectPosition.code == code))
    if position is None:
        position = ProjectPosition(project_id=project.id, code=code, title=title, category=category, description=description, headcount=headcount, required_skills_json=json.dumps(skills, ensure_ascii=False), deliverables=deliverables, sort_order=len(project.positions))
        db.add(position); db.flush()
    return position


def ensure_task(db: Session, project: Project, *, title: str, position: ProjectPosition | None, status: TaskStatus, assignee_id: int | None, order: int) -> ProjectTask:
    task = db.scalar(select(ProjectTask).where(ProjectTask.project_id == project.id, ProjectTask.title == title))
    if task is None:
        task = ProjectTask(project_id=project.id, position_id=position.id if position else None, title=title, description="演示项目链路中的协作事项", status=status, assignee_student_id=assignee_id, due_date=project.deadline, sort_order=order)
        db.add(task); db.flush()
    return task


def fold_demo_placeholder_position(db: Session, project: Project, target: ProjectPosition, *, task_title: str, task_status: TaskStatus) -> None:
    """Replace only the migration-created placeholder on documented demo projects."""
    placeholder = db.scalar(select(ProjectPosition).where(ProjectPosition.project_id == project.id, ProjectPosition.code == "general", ProjectPosition.title == "综合协作岗"))
    if placeholder is None or placeholder.id == target.id:
        return
    placeholder_task = db.scalar(select(ProjectTask).where(ProjectTask.project_id == project.id, ProjectTask.position_id == placeholder.id, ProjectTask.title.in_(["完成项目约定交付", "完成项目约定交付物"])))
    if placeholder_task:
        placeholder_task.position_id = target.id
        placeholder_task.title = task_title
        placeholder_task.status = task_status
    db.flush()
    referenced = (
        db.scalar(select(Application.id).where(Application.position_id == placeholder.id))
        or db.scalar(select(ProjectInvitation.id).where(ProjectInvitation.position_id == placeholder.id))
        or db.scalar(select(Review.id).where(Review.position_id == placeholder.id))
        or db.scalar(select(ProjectTask.id).where(ProjectTask.position_id == placeholder.id))
    )
    if referenced is None:
        db.delete(placeholder)
        db.flush()


def ensure_demo_verification(
    db: Session,
    *,
    student: User,
    portfolio: Portfolio,
    admin: User,
    reviewer: User,
    scores: list[int],
) -> SkillCredential:
    """Create a deterministic, clearly labelled end-to-end verification demo."""
    evidence = db.scalar(
        select(PortfolioEvidence).where(PortfolioEvidence.portfolio_id == portfolio.id)
    )
    rubric = evidence_rubric(evidence.evidence_type if evidence else "")
    if evidence is None or rubric is None:
        raise RuntimeError("演示作品缺少可核验的证据类型")
    rubric_version, criteria = rubric
    if len(scores) != len(criteria):
        raise RuntimeError("演示评分与量表维度数量不一致")
    evidence.ai_processing_consent_at = (
        evidence.ai_processing_consent_at or datetime.now(timezone.utc)
    )

    observation_number = f"SH-DEMO-OBS-{student.username.upper()}-001"
    observation_result = {
        "observable_facts": [
            {
                "observation": "作品文件、作品说明、过程记录与个人职责字段均已纳入证据链。",
                "evidence": {
                    "source": "work_description",
                    "reference": "演示档案中的作品说明与证据叙事",
                },
            }
        ],
        "evidence_gaps": ["演示数据不代表真实学生能力，只用于查看产品最终状态。"],
        "questions": [
            {"text": "你在这份作品中承担了哪些具体工作？", "targets_gap": "个人贡献"},
            {"text": "过程中遇到的主要问题和解决方式是什么？", "targets_gap": "过程证据"},
            {"text": "最终结果如何验证并完成交付？", "targets_gap": "结果与交付"},
        ],
    }
    observation = db.scalar(
        select(AssessmentRun).where(AssessmentRun.run_number == observation_number)
    )
    if observation is None:
        observation = AssessmentRun(
            run_number=observation_number,
            portfolio_id=portfolio.id,
            student_id=student.id,
            stage=AssessmentStage.observation,
            status=AssessmentStatus.succeeded,
            model="demo-simulated-review",
            rubric_version=rubric_version,
            input_summary=json.dumps(
                {"demo": True, "title": portfolio.title}, ensure_ascii=False
            ),
            raw_output=json.dumps(observation_result, ensure_ascii=False),
            structured_result=json.dumps(observation_result, ensure_ascii=False),
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        db.add(observation)
        db.flush()
    else:
        observation.rubric_version = rubric_version
        observation.status = AssessmentStatus.succeeded
        observation.structured_result = json.dumps(observation_result, ensure_ascii=False)

    answers = [
        "演示回答：职责、边界与交付范围已在档案中说明。",
        "演示回答：保留了问题定位、调整过程和迭代说明。",
        "演示回答：依据项目约定完成检查，并由项目方验收。",
    ]
    for position, (question_data, answer) in enumerate(
        zip(observation_result["questions"], answers), 1
    ):
        question = db.scalar(
            select(DefenseQuestion).where(
                DefenseQuestion.assessment_run_id == observation.id,
                DefenseQuestion.position == position,
            )
        )
        if question is None:
            question = DefenseQuestion(
                assessment_run_id=observation.id,
                position=position,
                text=question_data["text"],
                targets_gap=question_data["targets_gap"],
            )
            db.add(question)
        question.answer = answer
        question.answered_at = question.answered_at or datetime.now(timezone.utc)

    total_score = round(sum(scores) / (len(scores) * 4) * 100, 1)
    ai_result = {
        "criteria": [
            {
                "criterion": criterion,
                "score": score,
                "evidence": [
                    {
                        "source": "work_description",
                        "reference": f"{portfolio.title} · 演示证据记录",
                        "reason": "根据已保存的作品说明、过程记录与答辩内容形成的演示判断。",
                    }
                ],
            }
            for criterion, score in zip(criteria, scores)
        ],
        "total_score": total_score,
        "review_status": "pending_human_review",
        "result_label": "AI 辅助初评、待人工复核（演示）",
    }
    reassessment_number = f"SH-DEMO-RE-{student.username.upper()}-001"
    reassessment = db.scalar(
        select(AssessmentRun).where(AssessmentRun.run_number == reassessment_number)
    )
    if reassessment is None:
        reassessment = AssessmentRun(
            run_number=reassessment_number,
            portfolio_id=portfolio.id,
            student_id=student.id,
            stage=AssessmentStage.reassessment,
            status=AssessmentStatus.succeeded,
            model="demo-simulated-review",
            rubric_version=rubric_version,
            input_summary=json.dumps(
                {"demo": True, "source_run": observation_number}, ensure_ascii=False
            ),
            raw_output=json.dumps(ai_result, ensure_ascii=False),
            structured_result=json.dumps(ai_result, ensure_ascii=False),
            source_run_id=observation.id,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
        db.add(reassessment)
        db.flush()
    else:
        reassessment.rubric_version = rubric_version
        reassessment.status = AssessmentStatus.succeeded
        reassessment.source_run_id = observation.id
        reassessment.structured_result = json.dumps(ai_result, ensure_ascii=False)

    for run in (observation, reassessment):
        if not db.scalar(
            select(AssessmentRunEvent.id).where(
                AssessmentRunEvent.run_id == run.id,
                AssessmentRunEvent.to_status == AssessmentStatus.succeeded,
            )
        ):
            db.add(
                AssessmentRunEvent(
                    run_id=run.id,
                    from_status=AssessmentStatus.running,
                    to_status=AssessmentStatus.succeeded,
                    detail="演示流程已完成",
                )
            )

    human_result = {
        **ai_result,
        "review_status": "verified",
        "result_label": "人工复核通过（演示）",
        "human_review_reason": "评审已核对作品、过程说明和答辩记录；此结论仅用于展示完整产品流程，不代表真实学生认证。",
    }
    verification = db.scalar(
        select(SkillVerification).where(
            SkillVerification.assessment_run_id == reassessment.id
        )
    )
    if verification is None:
        verification = SkillVerification(
            assessment_run_id=reassessment.id,
            student_id=student.id,
            portfolio_id=portfolio.id,
            skill_id=portfolio.skill_id,
            status=VerificationStatus.verified,
            ai_result_snapshot=json.dumps(ai_result, ensure_ascii=False),
            human_result=json.dumps(human_result, ensure_ascii=False),
        )
        db.add(verification)
        db.flush()
    verification.status = VerificationStatus.verified
    verification.ai_result_snapshot = json.dumps(ai_result, ensure_ascii=False)
    verification.human_result = json.dumps(human_result, ensure_ascii=False)

    assignment = db.scalar(
        select(ReviewAssignment).where(
            ReviewAssignment.verification_id == verification.id
        )
    )
    if assignment is None:
        db.add(
            ReviewAssignment(
                verification_id=verification.id,
                reviewer_id=reviewer.id,
                assigned_by_id=admin.id,
            )
        )
    if not db.scalar(
        select(ReviewDecision.id).where(
            ReviewDecision.verification_id == verification.id,
            ReviewDecision.to_status == VerificationStatus.verified,
        )
    ):
        db.add(
            ReviewDecision(
                verification_id=verification.id,
                decided_by_id=reviewer.id,
                from_status=VerificationStatus.pending_human_review,
                to_status=VerificationStatus.verified,
                reason=human_result["human_review_reason"],
                before_result=json.dumps(ai_result, ensure_ascii=False),
                after_result=json.dumps(human_result, ensure_ascii=False),
            )
        )

    credential = db.scalar(
        select(SkillCredential).where(
            SkillCredential.verification_id == verification.id
        )
    )
    if credential is None:
        credential = SkillCredential(
            verification_id=verification.id,
            credential_number=f"SH-DEMO-2026-{student.username.upper()}-001",
            qr_token=sha256(
                f"skillhub-demo:{student.username}:{portfolio.id}".encode()
            ).hexdigest(),
            issued_by_id=reviewer.id,
        )
        db.add(credential)
    db.flush()
    return credential


def ensure_demo_project_review(
    db: Session,
    *,
    project: Project,
    requester: User,
    student: User,
    position: ProjectPosition,
    scores: dict[str, int],
    comment: str,
) -> Review:
    rubric_version, criteria = project_rubric(position.category)
    if set(scores) != set(criteria):
        raise RuntimeError("演示项目评价与岗位量表不匹配")
    application = ensure_application(db, project, student, ApplicationStatus.finished)
    application.position_id = position.id
    application.status = ApplicationStatus.finished
    project.lifecycle_status = LifecycleStatus.completed
    review = db.scalar(
        select(Review).where(
            Review.project_id == project.id, Review.student_id == student.id
        )
    )
    legacy_scores = list(scores.values())
    if review is None:
        review = Review(
            project_id=project.id,
            reviewer_id=requester.id,
            student_id=student.id,
            skill_score=legacy_scores[0],
            communication_score=legacy_scores[1],
            delivery_score=legacy_scores[2],
            time_management_score=legacy_scores[3],
        )
        db.add(review)
        db.flush()
    review.position_id = position.id
    review.rubric_category = position.category.value
    review.rubric_version = rubric_version
    review.criteria_scores_json = json.dumps(scores, ensure_ascii=False)
    review.skill_score = legacy_scores[0]
    review.communication_score = legacy_scores[1]
    review.delivery_score = legacy_scores[2]
    review.time_management_score = legacy_scores[3]
    review.comment = comment
    db.flush()

    validation = db.scalar(
        select(ProjectValidationRecord).where(
            ProjectValidationRecord.review_id == review.id
        )
    )
    if validation is None:
        validation = ProjectValidationRecord(
            project_id=project.id,
            student_id=student.id,
            requester_id=requester.id,
            review_id=review.id,
            project_title=project.title,
            position_title=position.title,
            position_category=position.category.value,
            rubric_version=rubric_version,
            criteria_scores_snapshot=json.dumps(scores, ensure_ascii=False),
            deliverables_snapshot=project.deliverables,
            acceptance_criteria_snapshot=project.acceptance_criteria,
            required_skills_snapshot=json.dumps(project.required_skills, ensure_ascii=False),
        )
        db.add(validation)
    else:
        validation.project_title = project.title
        validation.position_title = position.title
        validation.position_category = position.category.value
        validation.rubric_version = rubric_version
        validation.criteria_scores_snapshot = json.dumps(scores, ensure_ascii=False)
        validation.deliverables_snapshot = project.deliverables
        validation.acceptance_criteria_snapshot = project.acceptance_criteria
        validation.required_skills_snapshot = json.dumps(
            project.required_skills, ensure_ascii=False
        )
    db.flush()
    return review


def seed_database(db: Session, upload_dir: Path | None = None) -> None:
    admin = ensure_user(db, "admin", "admin@skillhub.example.com", UserRole.admin)
    reviewer = ensure_user(db, "reviewer", "reviewer@skillhub.example.com", UserRole.reviewer)
    student = ensure_user(db, "student", "student@skillhub.example.com", UserRole.student, school="SkillHub 大学", college="计算机学院", major="数据科学", grade="2025")
    designer = ensure_user(db, "designer", "designer@skillhub.example.com", UserRole.student, school="SkillHub 大学", college="设计学院", major="视觉传达", grade="2024")
    requester = ensure_user(db, "campus_org", "campus_org@skillhub.example.com", UserRole.requester)

    python_skill = ensure_skill(db, student, "Python", "数据处理、接口开发与自动化")
    ensure_skill(db, student, "数据分析", "数据清洗、指标设计与可视化表达")
    ensure_skill(db, student, "软件开发", "需求拆解、功能实现、测试与交付")
    ensure_skill(db, student, "项目协作", "任务推进、沟通协调与团队交付")
    design_skill = ensure_skill(db, designer, "视觉设计", "校园品牌与活动视觉设计")
    ensure_skill(db, designer, "UI/UX 设计", "界面设计、交互原型与可用性优化")
    ensure_skill(db, designer, "内容策划", "内容结构、文案表达与传播策划")
    ensure_skill(db, designer, "视频制作", "脚本、拍摄、剪辑与视听表达")
    student_portfolio = ensure_demo_portfolio(
        db,
        student,
        python_skill,
        title="校园数据看板（演示样本）",
        legacy_title="校园数据看板",
        filename="skillhub-demo-dashboard.png",
        evidence_type="data_visualization",
    )
    designer_portfolio = ensure_demo_portfolio(
        db,
        designer,
        design_skill,
        title="迎新视觉系统（演示样本）",
        legacy_title="迎新视觉系统",
        filename="skillhub-demo-poster.png",
        evidence_type="visual_poster",
    )
    if upload_dir is not None:
        render_demo_asset(
            upload_dir / "skillhub-demo-dashboard.png",
            title="CAMPUS DATA DASHBOARD",
            accent="#315b54",
        )
        render_demo_asset(
            upload_dir / "skillhub-demo-poster.png",
            title="WELCOME VISUAL POSTER",
            accent="#b6533c",
        )
    db.flush()

    recruiting = ensure_project(db, requester, "校园公益短片招募", AuditStatus.approved, LifecycleStatus.recruiting, ["视觉设计"], 30)
    ensure_project(db, requester, "社团数据整理", AuditStatus.pending, LifecycleStatus.recruiting, ["Python"], 25)
    active = ensure_project(db, requester, "校园活动数据平台", AuditStatus.approved, LifecycleStatus.in_progress, ["Python"], 18)
    completed = ensure_project(db, requester, "毕业季视觉设计", AuditStatus.approved, LifecycleStatus.completed, ["视觉设计"], 10)
    completed_code = ensure_project(
        db,
        requester,
        "校园活动报名系统（演示项目）",
        AuditStatus.approved,
        LifecycleStatus.completed,
        ["Python", "软件开发"],
        -12,
    )
    design_position = ensure_position(db, recruiting, code="visual-designer", title="视觉设计师", category=PositionCategory.design, description="负责公益短片的视觉基调、画面包装与宣传物料", skills=["视觉设计"], deliverables="视觉规范与宣传物料", headcount=2)
    development_position = ensure_position(db, active, code="backend-developer", title="后端开发", category=PositionCategory.development, description="负责活动数据接口、权限与服务稳定性", skills=["Python", "接口开发"], deliverables="可运行接口、测试记录与部署说明")
    ensure_position(db, active, code="data-analyst", title="数据分析", category=PositionCategory.data, description="负责数据清洗、指标设计和结果解释", skills=["Python", "数据分析"], deliverables="数据字典、分析脚本与可视化结论")
    completed_position = ensure_position(db, completed, code="visual-designer", title="视觉设计师", category=PositionCategory.design, description="负责毕业季视觉概念和系列物料", skills=["视觉设计"], deliverables="完整视觉系统")
    completed_code_position = ensure_position(
        db,
        completed_code,
        code="python-developer",
        title="Python 开发",
        category=PositionCategory.development,
        description="负责报名接口、数据校验、测试与交付说明",
        skills=["Python", "软件开发"],
        deliverables="可运行报名接口、自动化测试记录与部署说明",
    )
    active_application = ensure_application(db, active, student, ApplicationStatus.accepted)
    active_application.position_id = development_position.id
    completed_application = ensure_application(db, completed, designer, ApplicationStatus.finished)
    completed_application.position_id = completed_position.id
    fold_demo_placeholder_position(db, recruiting, design_position, task_title="完成公益短片视觉提案", task_status=TaskStatus.todo)
    fold_demo_placeholder_position(db, active, development_position, task_title="完成接口联调与阶段交付", task_status=TaskStatus.in_progress)
    ensure_task(db, active, title="确认数据字段与接口范围", position=development_position, status=TaskStatus.done, assignee_id=student.id, order=0)
    ensure_task(db, active, title="完成活动数据接口", position=development_position, status=TaskStatus.in_progress, assignee_id=student.id, order=1)
    ensure_task(db, active, title="补充异常场景测试", position=development_position, status=TaskStatus.todo, assignee_id=student.id, order=2)
    fold_demo_placeholder_position(db, completed_code, completed_code_position, task_title="完成报名系统验收交付", task_status=TaskStatus.done)
    ensure_task(db, completed_code, title="完成报名接口与数据校验", position=completed_code_position, status=TaskStatus.done, assignee_id=student.id, order=0)
    ensure_task(db, completed_code, title="补齐自动化测试与异常处理", position=completed_code_position, status=TaskStatus.done, assignee_id=student.id, order=1)
    ensure_task(db, completed_code, title="提交部署及验收说明", position=completed_code_position, status=TaskStatus.done, assignee_id=student.id, order=2)
    if not db.scalar(select(ProjectInvitation).where(ProjectInvitation.project_id == recruiting.id, ProjectInvitation.student_id == student.id)):
        db.add(ProjectInvitation(project_id=recruiting.id, student_id=student.id, inviter_id=requester.id, position_id=design_position.id, message="邀请你了解公益短片视觉设计岗位", status=InvitationStatus.pending))
    ensure_demo_project_review(
        db,
        project=completed,
        requester=requester,
        student=designer,
        position=completed_position,
        scores={"需求与方案": 5, "设计执行": 4, "协作沟通": 5, "交付规范": 4},
        comment="成果结构完整、沟通顺畅，交付文件符合约定。（演示评价）",
    )
    ensure_demo_project_review(
        db,
        project=completed_code,
        requester=requester,
        student=student,
        position=completed_code_position,
        scores={"功能正确性": 5, "代码质量": 4, "测试与可靠性": 4, "协作交付": 5},
        comment="接口功能完整，异常处理与测试记录清晰，能够按约定完成协作交付。（演示评价）",
    )
    fold_demo_placeholder_position(db, completed, completed_position, task_title="交付毕业季视觉系统", task_status=TaskStatus.done)
    ensure_demo_verification(
        db,
        student=student,
        portfolio=student_portfolio,
        admin=admin,
        reviewer=reviewer,
        scores=[4, 3, 4, 4, 3],
    )
    ensure_demo_verification(
        db,
        student=designer,
        portfolio=designer_portfolio,
        admin=admin,
        reviewer=reviewer,
        scores=[4, 4, 4, 3, 4],
    )
    db.flush()
    recalculate_student_skills(db, student.id)
    recalculate_student_skills(db, designer.id)
    db.commit()


def main() -> None:
    from app.db.migrations import run_additive_migrations

    run_additive_migrations(engine)
    with SessionLocal() as db:
        seed_database(db, get_settings().upload_dir)
    print("SkillHub demo data is ready.")


if __name__ == "__main__":
    main()
