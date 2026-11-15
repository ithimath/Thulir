"""Router for Data Quality Monitor (Feature 3)."""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.middleware.auth_middleware import (
    AuthenticatedUser,
    get_current_user,
    require_role,
)
from backend.app.services.data_quality_service import scan_data_quality

router = APIRouter(prefix="/api/data-quality", tags=["Data Quality"])


@router.get("/summary")
def get_data_quality_summary(
    grade: Optional[int] = Query(None),
    section: Optional[str] = Query(None),
    period_id: Optional[int] = Query(None),
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    """Retrieve high-level summary counts and completeness percentages."""
    scan = scan_data_quality(
        db=db,
        school_id=auth.school_id,
        auth=auth,
        grade_filter=grade,
        section_filter=section,
        period_id_filter=period_id,
    )
    return scan["summary"]


@router.get("/issues")
def get_data_quality_issues(
    category: Optional[str] = Query(None),
    grade: Optional[int] = Query(None),
    section: Optional[str] = Query(None),
    period_id: Optional[int] = Query(None),
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    """Retrieve filtered list of anomalous records with plain-language explanations."""
    scan = scan_data_quality(
        db=db,
        school_id=auth.school_id,
        auth=auth,
        grade_filter=grade,
        section_filter=section,
        period_id_filter=period_id,
    )
    issues = scan["issues"]
    if category:
        issues = [i for i in issues if i["category"] == category]

    return {
        "summary": scan["summary"],
        "issues": issues,
        "total_filtered": len(issues),
    }

