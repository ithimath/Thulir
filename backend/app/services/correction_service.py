"""Indicator Verification & Data Correction Service (Feature 2).

Enforces Locked Decisions (Section 3):
- Teacher may PROPOSE a correction for records in their assigned classes.
- Only an administrator can APPROVE and APPLY a correction.
- Original values are never overwritten: a correction creates a superseding record.
- Affected indicators are recalculated by the existing rule engine. Old indicators remain in history and are marked superseded, not deleted.
"""
import datetime
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.models import (
    DataCorrection,
    Student,
    AttendanceRecord,
    AssessmentRecord,
    AssignmentRecord,
    WarningIndicator,
    AuditLog,
    User,
)
from backend.app.middleware.auth_middleware import AuthenticatedUser
from backend.app.schemas.corrections import CorrectionProposalCreate


def propose_record_correction(
    db: Session,
    school_id: int,
    auth: AuthenticatedUser,
    payload: CorrectionProposalCreate,
) -> DataCorrection:
    """Propose a correction for an attendance, assessment, or assignment record."""
    if payload.record_type not in ["attendance", "assessment", "assignment"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid record_type '{payload.record_type}'. Must be 'attendance', 'assessment', or 'assignment'."
        )

    student: Optional[Student] = None
    original_data: Dict[str, Any] = {}

    if payload.record_type == "attendance":
        rec = db.query(AttendanceRecord).filter(
            AttendanceRecord.id == payload.target_record_id,
            AttendanceRecord.school_id == school_id,
        ).first()
        if not rec:
            raise HTTPException(status_code=404, detail="Target attendance record not found.")
        if rec.is_superseded:
            raise HTTPException(status_code=400, detail="Cannot correct an already superseded record.")
        student = rec.student
        original_data = {
            "record_id": rec.id,
            "days_present": rec.days_present,
            "total_instructional_days": rec.total_instructional_days,
            "attendance_percentage": rec.attendance_percentage,
            "status": rec.status,
            "record_date": str(rec.record_date) if rec.record_date else None,
            "reporting_period_id": rec.reporting_period_id,
        }

    elif payload.record_type == "assessment":
        rec = db.query(AssessmentRecord).filter(
            AssessmentRecord.id == payload.target_record_id,
            AssessmentRecord.school_id == school_id,
        ).first()
        if not rec:
            raise HTTPException(status_code=404, detail="Target assessment record not found.")
        if rec.is_superseded:
            raise HTTPException(status_code=400, detail="Cannot correct an already superseded record.")
        student = rec.student
        original_data = {
            "record_id": rec.id,
            "subject": rec.subject,
            "assessment_name": rec.assessment_name,
            "marks_obtained": rec.marks_obtained,
            "max_marks": rec.max_marks,
            "percentage": rec.percentage,
            "assessment_date": str(rec.assessment_date),
            "reporting_period_id": rec.reporting_period_id,
        }

    elif payload.record_type == "assignment":
        rec = db.query(AssignmentRecord).filter(
            AssignmentRecord.id == payload.target_record_id,
            AssignmentRecord.school_id == school_id,
        ).first()
        if not rec:
            raise HTTPException(status_code=404, detail="Target assignment record not found.")
        if rec.is_superseded:
            raise HTTPException(status_code=400, detail="Cannot correct an already superseded record.")
        student = rec.student
        original_data = {
            "record_id": rec.id,
            "subject": rec.subject,
            "status": rec.status,
            "score": rec.score,
            "assignment_date": str(rec.assignment_date),
            "reporting_period_id": rec.reporting_period_id,
        }

    if not student:
        raise HTTPException(status_code=404, detail="Associated student record not found.")

    # Role enforcement: Teachers can only propose corrections for students in their assigned classes
    if auth.role_name == "teacher":
        allowed = auth.assigned_classes_list
        cs = student.class_section
        if not cs or f"{cs.grade}-{cs.section}" not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only propose corrections for students in your assigned classes."
            )

    # Check for existing pending proposal for same record
    existing_pending = db.query(DataCorrection).filter(
        DataCorrection.record_type == payload.record_type,
        DataCorrection.target_record_id == payload.target_record_id,
        DataCorrection.status == "Pending",
    ).first()
    if existing_pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A correction proposal is already pending approval for this record (Proposal #{existing_pending.id})."
        )

    correction = DataCorrection(
        school_id=school_id,
        student_id=student.id,
        record_type=payload.record_type,
        target_record_id=payload.target_record_id,
        status="Pending",
        original_data=original_data,
        proposed_data=payload.proposed_data,
        reason=payload.reason.strip(),
        proposed_by_id=auth.id,
    )
    db.add(correction)

    audit = AuditLog(
        school_id=school_id,
        user_id=auth.id,
        action="CORRECTION_PROPOSED",
        entity_type="data_correction",
        entity_id=str(payload.target_record_id),
        details={"record_type": payload.record_type, "reason": payload.reason},
    )
    db.add(audit)
    db.commit()
    db.refresh(correction)
    return correction


def decide_record_correction(
    db: Session,
    correction_id: int,
    school_id: int,
    auth: AuthenticatedUser,
    action: str,
    rejection_reason: Optional[str] = None,
) -> DataCorrection:
    """Approve or reject a correction proposal. STRICTLY ADMIN-ONLY."""
    if auth.role_name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only an administrator can approve and apply data corrections."
        )

    correction = db.query(DataCorrection).filter(
        DataCorrection.id == correction_id,
        DataCorrection.school_id == school_id,
    ).first()
    if not correction:
        raise HTTPException(status_code=404, detail="Correction proposal not found.")

    if correction.status != "Pending":
        raise HTTPException(status_code=400, detail=f"Correction proposal is already {correction.status}.")

    now = datetime.datetime.utcnow()

    if action == "reject":
        correction.status = "Rejected"
        correction.approved_by_id = auth.id
        correction.approved_at = now
        correction.rejection_reason = rejection_reason or "Rejected by administrator review."
        db.commit()
        db.refresh(correction)
        return correction

    if action != "approve":
        raise HTTPException(status_code=422, detail="Action must be 'approve' or 'reject'.")

    # APPROVED & APPLIED:
    # 1. Create a NEW superseding record
    # 2. Mark original record as is_superseded = True with link
    # 3. Mark old indicators for this student and category as superseded
    # 4. Re-run warning engine for this student
    student_id = correction.student_id
    proposed = correction.proposed_data
    orig = correction.original_data
    superseding_id = None

    if correction.record_type == "assessment":
        orig_rec = db.query(AssessmentRecord).filter(AssessmentRecord.id == correction.target_record_id).first()
        if not orig_rec:
            raise HTTPException(status_code=404, detail="Original assessment record not found.")

        obt = float(proposed.get("marks_obtained", orig_rec.marks_obtained))
        mx = float(proposed.get("max_marks", orig_rec.max_marks))
        pct = round((obt / mx) * 100.0, 2) if mx > 0 else 0.0

        new_rec = AssessmentRecord(
            student_id=orig_rec.student_id,
            school_id=orig_rec.school_id,
            reporting_period_id=orig_rec.reporting_period_id,
            assessment_name=orig_rec.assessment_name,
            subject=orig_rec.subject,
            assessment_date=orig_rec.assessment_date,
            marks_obtained=obt,
            max_marks=mx,
            percentage=pct,
            is_superseded=False,
            correction_id=correction.id,
        )
        db.add(new_rec)
        db.flush()

        orig_rec.is_superseded = True
        orig_rec.superseded_by_id = new_rec.id
        orig_rec.correction_id = correction.id
        superseding_id = new_rec.id

    elif correction.record_type == "attendance":
        orig_rec = db.query(AttendanceRecord).filter(AttendanceRecord.id == correction.target_record_id).first()
        if not orig_rec:
            raise HTTPException(status_code=404, detail="Original attendance record not found.")

        dp = float(proposed.get("days_present", orig_rec.days_present or 0))
        tot = float(proposed.get("total_instructional_days", orig_rec.total_instructional_days or 0))
        pct = round((dp / tot) * 100.0, 2) if tot > 0 else 0.0
        st = proposed.get("status", orig_rec.status)

        new_rec = AttendanceRecord(
            student_id=orig_rec.student_id,
            school_id=orig_rec.school_id,
            reporting_period_id=orig_rec.reporting_period_id,
            record_date=orig_rec.record_date,
            status=st,
            days_present=dp,
            total_instructional_days=tot,
            attendance_percentage=pct,
            is_superseded=False,
            correction_id=correction.id,
        )
        db.add(new_rec)
        db.flush()

        orig_rec.is_superseded = True
        orig_rec.superseded_by_id = new_rec.id
        orig_rec.correction_id = correction.id
        superseding_id = new_rec.id

    elif correction.record_type == "assignment":
        orig_rec = db.query(AssignmentRecord).filter(AssignmentRecord.id == correction.target_record_id).first()
        if not orig_rec:
            raise HTTPException(status_code=404, detail="Original assignment record not found.")

        new_status = proposed.get("status", orig_rec.status)
        new_score = float(proposed["score"]) if proposed.get("score") is not None else orig_rec.score

        new_rec = AssignmentRecord(
            student_id=orig_rec.student_id,
            school_id=orig_rec.school_id,
            reporting_period_id=orig_rec.reporting_period_id,
            subject=orig_rec.subject,
            assignment_date=orig_rec.assignment_date,
            status=new_status,
            score=new_score,
            is_superseded=False,
            correction_id=correction.id,
        )
        db.add(new_rec)
        db.flush()

        orig_rec.is_superseded = True
        orig_rec.superseded_by_id = new_rec.id
        orig_rec.correction_id = correction.id
        superseding_id = new_rec.id

    # Update correction proposal
    correction.status = "Approved"
    correction.superseding_record_id = superseding_id
    correction.approved_by_id = auth.id
    correction.approved_at = now

    # Mark active indicators for this category as superseded (they remain in history, not deleted!)
    category_map = {
        "attendance": "attendance",
        "assessment": "academic",
        "assignment": "assignment",
    }
    target_category = category_map.get(correction.record_type)
    if target_category:
        existing_indicators = db.query(WarningIndicator).filter(
            WarningIndicator.student_id == student_id,
            WarningIndicator.school_id == school_id,
            WarningIndicator.category == target_category,
            WarningIndicator.is_superseded == False,
        ).all()
        for ind in existing_indicators:
            ind.is_superseded = True

    # Re-run warning engine for this student
    from backend.app.services.warning_engine import run_student_indicators
    run_student_indicators(db, student_id, school_id)

    # Audit log
    audit = AuditLog(
        school_id=school_id,
        user_id=auth.id,
        action="CORRECTION_APPROVED",
        entity_type="data_correction",
        entity_id=str(correction.id),
        details={
            "record_type": correction.record_type,
            "target_record_id": correction.target_record_id,
            "superseding_record_id": superseding_id,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(correction)
    return correction

