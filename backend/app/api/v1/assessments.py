from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.assessment import (
    AssessmentRun,
    AssessmentStage,
    AssessmentStatus,
    DefenseQuestion,
)
from app.models.user import User, UserRole
from app.schemas.assessment import AssessmentRunResponse, DefenseAnswers
from app.services.assessments import (
    assessment_to_response,
    run_observation,
    run_reassessment,
)
from app.services.model_gateway import DashScopeVisionModel


router = APIRouter(tags=["assessments"])
student_only = require_roles(UserRole.student)
admin_only = require_roles(UserRole.admin)


def get_vision_model():
    return DashScopeVisionModel()


def _owned_run(db: Session, student: User, run_number: str) -> AssessmentRun:
    run = db.scalar(
        select(AssessmentRun).where(
            AssessmentRun.run_number == run_number,
            AssessmentRun.student_id == student.id,
        )
    )
    if run is None:
        raise HTTPException(status_code=404, detail="评估运行不存在")
    return run


@router.post(
    "/portfolios/{portfolio_id}/assessments",
    response_model=AssessmentRunResponse,
    status_code=201,
)
def create_assessment(
    portfolio_id: int,
    current: User = Depends(student_only),
    db: Session = Depends(get_db),
    model=Depends(get_vision_model),
):
    run = run_observation(db, current, portfolio_id, model)
    return assessment_to_response(db, run)


@router.get("/assessments/{run_number}", response_model=AssessmentRunResponse)
def get_assessment(
    run_number: str,
    current: User = Depends(student_only),
    db: Session = Depends(get_db),
):
    return assessment_to_response(db, _owned_run(db, current, run_number))


@router.get(
    "/portfolios/{portfolio_id}/assessments",
    response_model=list[AssessmentRunResponse],
)
def portfolio_assessments(
    portfolio_id: int,
    current: User = Depends(student_only),
    db: Session = Depends(get_db),
):
    runs = list(
        db.scalars(
            select(AssessmentRun)
            .where(
                AssessmentRun.portfolio_id == portfolio_id,
                AssessmentRun.student_id == current.id,
            )
            .order_by(AssessmentRun.created_at.desc())
        )
    )
    return [assessment_to_response(db, run) for run in runs]


@router.post(
    "/assessments/{run_number}/answers",
    response_model=AssessmentRunResponse,
    status_code=201,
)
def answer_defense(
    run_number: str,
    payload: DefenseAnswers,
    current: User = Depends(student_only),
    db: Session = Depends(get_db),
    model=Depends(get_vision_model),
):
    source = _owned_run(db, current, run_number)
    if source.stage != AssessmentStage.observation or source.status != AssessmentStatus.succeeded:
        raise HTTPException(status_code=409, detail="该运行不能提交动态答辩")
    questions = list(
        db.scalars(
            select(DefenseQuestion).where(
                DefenseQuestion.assessment_run_id == source.id
            )
        )
    )
    by_id = {question.id: question for question in questions}
    answer_ids = [answer.question_id for answer in payload.answers]
    if len(set(answer_ids)) != 3 or set(answer_ids) != set(by_id):
        raise HTTPException(status_code=422, detail="必须逐一回答本次运行的 3 个问题")
    now = datetime.now(timezone.utc)
    for answer in payload.answers:
        by_id[answer.question_id].answer = answer.answer
        by_id[answer.question_id].answered_at = now
    db.commit()
    run = run_reassessment(db, current, source, model)
    return assessment_to_response(db, run)


@router.post(
    "/assessments/{run_number}/retry",
    response_model=AssessmentRunResponse,
    status_code=201,
)
def retry_assessment(
    run_number: str,
    current: User = Depends(student_only),
    db: Session = Depends(get_db),
    model=Depends(get_vision_model),
):
    failed = _owned_run(db, current, run_number)
    if failed.status != AssessmentStatus.failed:
        raise HTTPException(status_code=409, detail="只有失败的运行可以重试")
    if failed.stage == AssessmentStage.observation:
        run = run_observation(
            db, current, failed.portfolio_id, model, retry_of_id=failed.id
        )
    else:
        source = db.get(AssessmentRun, failed.source_run_id)
        if source is None:
            raise HTTPException(status_code=409, detail="原始答辩运行不存在")
        run = run_reassessment(db, current, source, model, retry_of_id=failed.id)
    return assessment_to_response(db, run)


@router.get(
    "/admin/assessment-runs", response_model=list[AssessmentRunResponse]
)
def admin_assessment_runs(
    status: AssessmentStatus | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    query = select(AssessmentRun).order_by(AssessmentRun.created_at.desc()).limit(limit)
    if status is not None:
        query = query.where(AssessmentRun.status == status)
    runs = list(db.scalars(query))
    return [assessment_to_response(db, run) for run in runs]
