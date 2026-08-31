from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.skill import Skill
from app.models.user import User, UserRole
from app.schemas.skill import SkillCreate, SkillResponse, SkillUpdate


router = APIRouter(prefix="/skills", tags=["skills"])
student_only = require_roles(UserRole.student)


def owned_skill(db: Session, user: User, skill_id: int) -> Skill:
    skill = db.scalar(
        select(Skill).where(Skill.id == skill_id, Skill.user_id == user.id)
    )
    if skill is None:
        raise HTTPException(status_code=404, detail="技能不存在")
    return skill


@router.get("", response_model=list[SkillResponse])
def list_skills(
    current_user: User = Depends(student_only), db: Session = Depends(get_db)
) -> list[Skill]:
    return list(db.scalars(select(Skill).where(Skill.user_id == current_user.id)))


@router.post("", response_model=SkillResponse, status_code=201)
def create_skill(
    payload: SkillCreate,
    current_user: User = Depends(student_only),
    db: Session = Depends(get_db),
) -> Skill:
    normalized_name = payload.name.casefold()
    duplicate = db.scalar(
        select(Skill).where(
            Skill.user_id == current_user.id,
            Skill.normalized_name == normalized_name,
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="技能名称已存在")
    skill = Skill(
        user_id=current_user.id,
        name=payload.name,
        normalized_name=normalized_name,
        description=payload.description,
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.patch("/{skill_id}", response_model=SkillResponse)
def update_skill(
    skill_id: int,
    payload: SkillUpdate,
    current_user: User = Depends(student_only),
    db: Session = Depends(get_db),
) -> Skill:
    skill = owned_skill(db, current_user, skill_id)
    if payload.name is not None:
        normalized_name = payload.name.casefold()
        duplicate = db.scalar(
            select(Skill).where(
                Skill.user_id == current_user.id,
                Skill.normalized_name == normalized_name,
                Skill.id != skill.id,
            )
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="技能名称已存在")
        skill.name = payload.name
        skill.normalized_name = normalized_name
    if "description" in payload.model_fields_set:
        skill.description = payload.description
    db.commit()
    db.refresh(skill)
    return skill


@router.delete("/{skill_id}", status_code=204)
def delete_skill(
    skill_id: int,
    current_user: User = Depends(student_only),
    db: Session = Depends(get_db),
) -> None:
    skill = owned_skill(db, current_user, skill_id)
    db.delete(skill)
    db.commit()
