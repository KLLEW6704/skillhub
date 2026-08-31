from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.config import Settings
from app.models.portfolio import Portfolio
from app.models.user import User, UserRole
from app.schemas.portfolio import PortfolioResponse
from app.services.portfolios import create_portfolio, delete_portfolio


router = APIRouter(prefix="/portfolios", tags=["portfolios"])
student_only = require_roles(UserRole.student)


@router.get("", response_model=list[PortfolioResponse])
def list_portfolios(
    current_user: User = Depends(student_only), db: Session = Depends(get_db)
) -> list[Portfolio]:
    return list(
        db.scalars(select(Portfolio).where(Portfolio.user_id == current_user.id))
    )


@router.post("", response_model=PortfolioResponse, status_code=201)
async def upload_portfolio(
    skill_id: int = Form(),
    title: str = Form(min_length=1, max_length=150),
    description: str | None = Form(default=None, max_length=2000),
    file: UploadFile = File(),
    current_user: User = Depends(student_only),
    db: Session = Depends(get_db),
) -> Portfolio:
    settings = Settings()
    return await create_portfolio(
        db,
        current_user,
        skill_id,
        title,
        description,
        file,
        settings.upload_dir,
        settings.max_upload_mb * 1024 * 1024,
    )


@router.delete("/{portfolio_id}", status_code=204)
def remove_portfolio(
    portfolio_id: int,
    current_user: User = Depends(student_only),
    db: Session = Depends(get_db),
) -> None:
    delete_portfolio(db, current_user, portfolio_id, Settings().upload_dir)
