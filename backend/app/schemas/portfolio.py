from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PortfolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    skill_id: int
    title: str
    description: str | None
    file_url: str
    file_type: str
    created_at: datetime
