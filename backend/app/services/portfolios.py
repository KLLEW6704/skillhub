from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.models.skill import Skill
from app.models.user import User
from app.services.uploads import remove_upload, save_upload


async def create_portfolio(
    db: Session,
    user: User,
    skill_id: int,
    title: str,
    description: str | None,
    file: UploadFile,
    upload_dir: Path,
    max_bytes: int,
) -> Portfolio:
    skill = db.scalar(
        select(Skill).where(Skill.id == skill_id, Skill.user_id == user.id)
    )
    if skill is None:
        raise HTTPException(status_code=404, detail="技能不存在")
    stored_name = await save_upload(file, upload_dir, max_bytes)
    portfolio = Portfolio(
        user_id=user.id,
        skill_id=skill.id,
        title=title,
        description=description,
        file_url=f"/uploads/{stored_name}",
        file_type=file.content_type or "application/octet-stream",
    )
    try:
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    except BaseException:
        remove_upload(upload_dir, portfolio.file_url)
        raise
    return portfolio


def delete_portfolio(
    db: Session, user: User, portfolio_id: int, upload_dir: Path
) -> None:
    portfolio = db.scalar(
        select(Portfolio).where(
            Portfolio.id == portfolio_id, Portfolio.user_id == user.id
        )
    )
    if portfolio is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    file_url = portfolio.file_url
    db.delete(portfolio)
    db.commit()
    remove_upload(upload_dir, file_url)
