from io import BytesIO

import qrcode
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.verification import (
    PublicCredentialResponse,
    ReviewAssignmentCreate,
    ReviewDecisionCreate,
    ReviewerAssignmentResponse,
    RevocationCreate,
    VerificationResponse,
)
from app.services.verifications import (
    assign_reviewer,
    decide_verification,
    public_credential,
    reviewer_assignments,
    revoke_credential,
)


router = APIRouter(tags=["verifications"])
admin_only = require_roles(UserRole.admin)
reviewer_only = require_roles(UserRole.reviewer)


@router.post(
    "/admin/verifications/{verification_id}/assign",
    response_model=ReviewerAssignmentResponse,
)
def assign(
    verification_id: int,
    payload: ReviewAssignmentCreate,
    admin: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    return assign_reviewer(db, admin, verification_id, payload.reviewer_id)


@router.get(
    "/reviewer/assignments", response_model=list[ReviewerAssignmentResponse]
)
def assignments(
    reviewer: User = Depends(reviewer_only), db: Session = Depends(get_db)
):
    return reviewer_assignments(db, reviewer)


@router.post(
    "/reviewer/verifications/{verification_id}/decision",
    response_model=VerificationResponse,
    status_code=201,
)
def decision(
    verification_id: int,
    payload: ReviewDecisionCreate,
    reviewer: User = Depends(reviewer_only),
    db: Session = Depends(get_db),
):
    return decide_verification(db, reviewer, verification_id, payload)


@router.post(
    "/admin/credentials/{credential_number}/revoke",
    response_model=VerificationResponse,
)
def revoke(
    credential_number: str,
    payload: RevocationCreate,
    admin: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    return revoke_credential(db, admin, credential_number, payload.reason)


@router.get(
    "/credentials/{credential_number}", response_model=PublicCredentialResponse
)
def verify_credential(credential_number: str, db: Session = Depends(get_db)):
    _, response = public_credential(db, credential_number)
    return response


@router.get("/credentials/{credential_number}/qr")
def credential_qr(credential_number: str, db: Session = Depends(get_db)):
    credential, _ = public_credential(db, credential_number)
    payload = f"/api/v1/credentials/{credential.credential_number}?token={credential.qr_token}"
    image = qrcode.make(payload)
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return StreamingResponse(output, media_type="image/png")
