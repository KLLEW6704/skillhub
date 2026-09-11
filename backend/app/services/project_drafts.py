import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.collaboration import ProjectDraft
from app.models.user import User
from app.schemas.collaboration import ProjectDraftPayload


def list_project_drafts(db: Session, owner: User) -> list[ProjectDraft]:
    return list(db.scalars(select(ProjectDraft).where(ProjectDraft.creator_id == owner.id).order_by(ProjectDraft.updated_at.desc())))


def save_project_draft(db: Session, owner: User, payload: ProjectDraftPayload, draft_id: int | None = None) -> ProjectDraft:
    draft = None
    if draft_id is not None:
        draft = db.scalar(select(ProjectDraft).where(ProjectDraft.id == draft_id, ProjectDraft.creator_id == owner.id))
        if draft is None:
            raise HTTPException(status_code=404, detail="项目草稿不存在")
    if draft is None:
        draft = ProjectDraft(creator_id=owner.id)
        db.add(draft)
    draft.payload_json = json.dumps(payload.model_dump(mode="json"), ensure_ascii=False)
    db.commit()
    db.refresh(draft)
    return draft


def delete_project_draft(db: Session, owner: User, draft_id: int) -> None:
    draft = db.scalar(select(ProjectDraft).where(ProjectDraft.id == draft_id, ProjectDraft.creator_id == owner.id))
    if draft is None:
        raise HTTPException(status_code=404, detail="项目草稿不存在")
    db.delete(draft)
    db.commit()
