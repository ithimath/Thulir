"""Warning Rules Configuration Router (Feature 7).

Role rules:
- Viewing rules and thresholds: all authenticated school staff.
- Modifying thresholds / creating versions: Administrator only (HTTP 403 for non-admins).
"""

from typing import Optional
import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.middleware.auth_middleware import (
    AuthenticatedUser,
    get_current_user,
    require_role,
)
from backend.app.services.rule_management_service import (
    get_all_rules,
    preview_rule_threshold_change,
    update_rule_threshold,
    revert_rule_version,
)

router = APIRouter(prefix="/api/rules", tags=["rules"])


class ThresholdUpdatePayload(BaseModel):
    new_threshold: float = Field(..., description="New numeric threshold for the rule")
    change_reason: str = Field(..., min_length=5, description="Mandatory justification for rule threshold change")
    effective_from: Optional[datetime.date] = Field(None, description="Effective from date (defaults to today)")


class RevertPayload(BaseModel):
    target_version: int = Field(..., ge=1, description="Version number to restore")
    change_reason: str = Field(..., min_length=5, description="Reason for reversion")


@router.get("", response_model=dict)
def list_rules(
    auth: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """View all warning rules, their active thresholds, and historical versions."""
    rules = get_all_rules(db)
    return {
        "total_rules": len(rules),
        "items": rules,
    }


@router.get("/preview-change", response_model=dict)
def preview_change(
    rule_code: str = Query(..., description="Rule code e.g. ATT-LOW"),
    proposed_threshold: float = Query(..., description="Simulated threshold"),
    auth: AuthenticatedUser = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """Simulates indicators raised against historical records without committing."""
    return preview_rule_threshold_change(
        db=db,
        school_id=auth.school_id,
        rule_code=rule_code,
        proposed_threshold=proposed_threshold,
    )


@router.post("/{rule_code}/threshold", response_model=dict)
def update_threshold(
    rule_code: str,
    payload: ThresholdUpdatePayload,
    auth: AuthenticatedUser = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """
    Administrator-only: Update a warning rule threshold.
    Creates version N+1 with effective date and required reason.
    Historical indicators retain their original rule version.
    """
    try:
        return update_rule_threshold(
            db=db,
            rule_code=rule_code,
            new_threshold=payload.new_threshold,
            change_reason=payload.change_reason,
            admin_user_id=auth.id,
            effective_from=payload.effective_from,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{rule_code}/revert", response_model=dict)
def revert_version(
    rule_code: str,
    payload: RevertPayload,
    auth: AuthenticatedUser = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """
    Administrator-only: Revert to a previous rule version threshold.
    Creates an audited version increment preserving full history.
    """
    try:
        return revert_rule_version(
            db=db,
            rule_code=rule_code,
            target_version=payload.target_version,
            change_reason=payload.change_reason,
            admin_user_id=auth.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

