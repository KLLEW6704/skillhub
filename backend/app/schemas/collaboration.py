from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.collaboration import PositionCategory, TaskStatus
from app.models.project import LifecycleStatus


class ProjectPositionCreate(BaseModel):
    code: str = Field(min_length=1, max_length=60, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(min_length=1, max_length=100)
    category: PositionCategory = PositionCategory.general
    description: str = Field(min_length=2, max_length=2000)
    headcount: int = Field(default=1, ge=1, le=20)
    required_skills: list[str] = Field(min_length=1, max_length=12)
    deliverables: str = Field(min_length=2, max_length=2000)
    sort_order: int = Field(default=0, ge=0, le=1000)


class ProjectPositionResponse(ProjectPositionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int


class ProjectTaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    position_code: str | None = Field(default=None, max_length=60)
    assignee_student_id: int | None = Field(default=None, gt=0)
    due_date: date | None = None
    sort_order: int = Field(default=0, ge=0, le=2000)


class ProjectTaskStatusUpdate(BaseModel):
    status: TaskStatus
    expected_version: int = Field(ge=1)


class ProjectTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    position_id: int | None
    title: str
    description: str | None
    status: TaskStatus
    assignee_student_id: int | None
    due_date: date | None
    sort_order: int
    version: int
    updated_by_id: int | None
    created_at: datetime
    updated_at: datetime
    position: ProjectPositionResponse | None


class WorkspaceMember(BaseModel):
    student_id: int
    display_name: str
    position_id: int | None
    position_title: str | None


class WorkspaceProgress(BaseModel):
    total: int
    todo: int
    in_progress: int
    done: int
    completion_percent: int


class WorkspaceProjectSummary(BaseModel):
    id: int
    title: str
    lifecycle_status: LifecycleStatus


class ProjectWorkspaceResponse(BaseModel):
    project: WorkspaceProjectSummary
    positions: list[ProjectPositionResponse]
    members: list[WorkspaceMember]
    tasks: list[ProjectTaskResponse]
    progress: WorkspaceProgress
    can_manage: bool


class ProjectPlanBrief(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=5, max_length=5000)
    category: str = Field(min_length=1, max_length=80)
    deliverables: str | None = Field(default=None, max_length=4000)
    team_size: int = Field(default=4, ge=1, le=30)


class ProjectPlanDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    positions: list[ProjectPositionCreate] = Field(min_length=1, max_length=10)
    tasks: list[ProjectTaskCreate] = Field(min_length=1, max_length=30)


class ProjectPositionDraft(BaseModel):
    code: str = Field(default="", max_length=60)
    title: str = Field(default="", max_length=100)
    category: PositionCategory = PositionCategory.general
    description: str = Field(default="", max_length=2000)
    headcount: int = Field(default=1, ge=1, le=20)
    required_skills: list[str] = Field(default_factory=list, max_length=12)
    deliverables: str = Field(default="", max_length=2000)
    sort_order: int = Field(default=0, ge=0, le=1000)


class ProjectTaskDraft(BaseModel):
    title: str = Field(default="", max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    position_code: str | None = Field(default=None, max_length=60)
    assignee_student_id: int | None = Field(default=None, gt=0)
    due_date: date | None = None
    sort_order: int = Field(default=0, ge=0, le=2000)


class ProjectDraftPayload(BaseModel):
    title: str = Field(default="", max_length=150)
    description: str = Field(default="", max_length=5000)
    category: str = Field(default="", max_length=80)
    deliverables: str = Field(default="", max_length=4000)
    team_size: int = Field(default=4, ge=1, le=30)
    deadline: str = Field(default="", max_length=10)
    budget: str = Field(default="", max_length=30)
    additional_skills: str = Field(default="", max_length=1000)
    acceptance_criteria: str = Field(default="", max_length=4000)
    positions: list[ProjectPositionDraft] = Field(default_factory=list, max_length=10)
    tasks: list[ProjectTaskDraft] = Field(default_factory=list, max_length=30)


class ProjectDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    creator_id: int
    payload: ProjectDraftPayload
    created_at: datetime
    updated_at: datetime


class RubricDefinitionResponse(BaseModel):
    category: PositionCategory
    label: str
    version: str
    criteria: list[str]
    scale_min: int = 1
    scale_max: int = 5
