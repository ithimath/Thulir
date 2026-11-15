"""Router for Indicator Verification & Data Correction Centre (Feature 2)."""
import math
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.middleware.auth_middleware import (
    AuthenticatedUser,
    get_current_user,
    require_role,
)
from backend.app.models.models import (
    DataCorrection,
    Student,
    ClassSection,
    User,
)
from backend.app.schemas.corrections import (
    CorrectionProposalCreate,
    CorrectionDecisionRequest,
    CorrectionItemOut,
    CorrectionListOut,
)
from backend.app.services.correction_service import (
    propose_record_correction,
    decide_record_correction,
)

router = APIRouter(prefix="/api/corrections", tags=["Data Corrections"])


def _to_item_out(c: DataCorrection, db: Session) -> CorrectionItemOut:
    student = c.student
    cs = student.class_section if student else None
    proposer = c.proposer
    approver = c.approver

    return CorrectionItemOut(
        id=c.id,
        school_id=c.school_id,
        student_id=c.student_id,
        student_name=student.full_name if student else "Unknown",
        emis_id=student.emis_id if student else "",
        grade=cs.grade if cs else None,
        section=cs.section if cs else None,
        record_type=c.record_type,
        target_record_id=c.target_record_id,
        superseding_record_id=c.superseding_record_id,
        status=c.status,
        original_data=c.original_data,
        proposed_data=c.proposed_data,
        reason=c.reason,
        proposer_id=c.proposed_by_id,
        proposer_name=proposer.full_name if proposer else "Staff",
        proposer_designation=proposer.designation if proposer else "Staff",
        approver_id=c.approved_by_id,
        approver_name=approver.full_name if approver else None,
        approved_at=c.approved_at,
        rejection_reason=c.rejection_reason,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


# ---------------------------------------------------------------------------
# 1. LIST CORRECTIONS (GET /api/corrections)
# ---------------------------------------------------------------------------
@router.get("", response_model=CorrectionListOut)
def list_corrections(
    status_filter: Optional[str] = Query(None, alias="status"),
    record_type: Optional[str] = Query(None),
    student_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    query = db.query(DataCorrection).filter(DataCorrection.school_id == auth.school_id)

    # Scoping for teachers: only their assigned classes
    if auth.role_name == "teacher":
        allowed = auth.assigned_classes_list
        if not allowed:
            return CorrectionListOut(items=[], total=0, pending_count=0, approved_count=0, rejected_count=0)
        from sqlalchemy import or_, and_
        pairs = [p.split("-") for p in allowed if "-" in p]
        conditions = [
            and_(ClassSection.grade == int(g), ClassSection.section == s)
            for g, s in pairs if g.isdigit()
        ]
        if conditions:
            query = query.join(Student, DataCorrection.student_id == Student.id)\
                         .join(ClassSection, Student.current_class_section_id == ClassSection.id)\
                         .filter(or_(*conditions))
        else:
            return CorrectionListOut(items=[], total=0, pending_count=0, approved_count=0, rejected_count=0)

    # Count by status for badge metrics
    base_school_q = db.query(DataCorrection).filter(DataCorrection.school_id == auth.school_id)
    pending_count = base_school_q.filter(DataCorrection.status == "Pending").count()
    approved_count = base_school_q.filter(DataCorrection.status == "Approved").count()
    rejected_count = base_school_q.filter(DataCorrection.status == "Rejected").count()

    if status_filter:
        query = query.filter(DataCorrection.status == status_filter)
    if record_type:
        query = query.filter(DataCorrection.record_type == record_type)
    if student_id:
        query = query.filter(DataCorrection.student_id == student_id)

    total = query.count()
    corrections = query.order_by(desc(DataCorrection.created_at))\
                       .offset((page - 1) * page_size)\
                       .limit(page_size)\
                       .all()

    items = [_to_item_out(c, db) for c in corrections]
    return CorrectionListOut(
        items=items,
        total=total,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
    )


# ---------------------------------------------------------------------------
# 2. GET CORRECTION DETAIL (GET /api/corrections/{id})
# ---------------------------------------------------------------------------
@router.get("/{correction_id}", response_model=CorrectionItemOut)
def get_correction_detail(
    correction_id: int,
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    corr = db.query(DataCorrection).filter(
        DataCorrection.id == correction_id,
        DataCorrection.school_id == auth.school_id,
    ).first()
    if not corr:
        raise HTTPException(status_code=404, detail="Correction proposal not found.")

    return _to_item_out(corr, db)


# ---------------------------------------------------------------------------
# 3. PROPOSE CORRECTION (POST /api/corrections)
# ---------------------------------------------------------------------------
@router.post("", response_model=CorrectionItemOut, status_code=status.HTTP_201_CREATED)
def propose_correction(
    payload: CorrectionProposalCreate,
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    corr = propose_record_correction(db, auth.school_id, auth, payload)
    return _to_item_out(corr, db)


# ---------------------------------------------------------------------------
# 4. DECIDE / APPLY CORRECTION (POST /api/corrections/{id}/decide)
# ---------------------------------------------------------------------------
@router.post("/{correction_id}/decide", response_model=CorrectionItemOut)
def decide_correction(
    correction_id: int,
    payload: CorrectionDecisionRequest,
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    # Only Admin can decide/apply corrections (rejection if non-admin is handled in service)
    corr = decide_record_correction(
        db=db,
        correction_id=correction_id,
        school_id=auth.school_id,
        auth=auth,
        action=payload.action,
        rejection_reason=payload.rejection_reason,
    )
    return _to_item_out(corr, db)

