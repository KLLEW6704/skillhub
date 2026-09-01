from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.application import ApplicationStatus


class ApplicationCreate(BaseModel):
    message: str | None = Field(default=None, max_length=2000)


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    student_id: int
    message: str | None
    status: ApplicationStatus
    created_at: datetime
