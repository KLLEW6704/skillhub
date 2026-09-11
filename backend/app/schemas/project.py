from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.project import AuditStatus, LifecycleStatus
from app.schemas.collaboration import ProjectPositionCreate, ProjectPositionResponse, ProjectTaskCreate


class ProjectCreate(BaseModel):
    draft_id: int | None = Field(default=None, gt=0)
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=5, max_length=5000)
    category: str = Field(min_length=1, max_length=80)
    budget: Decimal | None = Field(default=None, ge=0)
    deadline: date
    required_skills: list[str] = Field(min_length=1, max_length=12)
    deliverables: str | None = Field(default=None, max_length=4000)
    acceptance_criteria: str | None = Field(default=None, max_length=4000)
    positions: list[ProjectPositionCreate] = Field(default_factory=list, max_length=10)
    tasks: list[ProjectTaskCreate] = Field(default_factory=list, max_length=30)

    @field_validator("required_skills")
    @classmethod
    def normalize_skills(cls, values: list[str]) -> list[str]:
        result = []
        for value in values:
            name = value.strip()
            if name and name.casefold() not in {x.casefold() for x in result}:
                result.append(name)
        if not result:
            raise ValueError("至少需要一项技能")
        return result

    @model_validator(mode="after")
    def validate_collaboration_draft(self):
        codes = [position.code for position in self.positions]
        if len(codes) != len(set(codes)):
            raise ValueError("岗位代码不能重复")
        if any(task.assignee_student_id is not None for task in self.tasks):
            raise ValueError("发布项目时不能预先指定学生负责人")
        return self


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, min_length=5, max_length=5000)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    budget: Decimal | None = Field(default=None, ge=0)
    deadline: date | None = None
    required_skills: list[str] | None = None
    deliverables: str | None = Field(default=None, max_length=4000)
    acceptance_criteria: str | None = Field(default=None, max_length=4000)


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    creator_id: int
    title: str
    description: str
    category: str
    budget: Decimal | None
    deadline: date
    audit_status: AuditStatus
    lifecycle_status: LifecycleStatus
    required_skills: list[str]
    deliverables: str | None
    acceptance_criteria: str | None
    positions: list[ProjectPositionResponse] = Field(default_factory=list)
    created_at: datetime


class ProjectPage(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
