from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.project import AuditStatus, LifecycleStatus


class ProjectCreate(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=5, max_length=5000)
    category: str = Field(min_length=1, max_length=80)
    budget: Decimal | None = Field(default=None, ge=0)
    deadline: date
    required_skills: list[str] = Field(min_length=1, max_length=12)

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


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, min_length=5, max_length=5000)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    budget: Decimal | None = Field(default=None, ge=0)
    deadline: date | None = None
    required_skills: list[str] | None = None


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
    created_at: datetime


class ProjectPage(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
