"""AI-Assisted Record Summarization Service (Feature 10).

Governance & Civic Safety Mandates:
- Feature Flag: AI_ENABLED=false by default. If false/unconfigured, returns 'AI summaries unavailable'.
- Anonymization: Student names replaced with reference IDs ('REF-{student_id}').
- Confidentiality: Never transmits contact details, EMIS IDs, or free-text counselling notes.
- Grounded Citations: Every claim cites the underlying record ID (e.g. [ATT-12], [ASM-45], [IND-3]).
- Draft Protocol: Output is strictly a DRAFT. Human review and explicit approval required before saving.
"""

import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models.models import (
    Student,
    AttendanceRecord,
    AssessmentRecord,
    AssignmentRecord,
    WarningIndicator,
    ReportingPeriod,
    SupportCase,
    CaseNote,
    User,
)


def generate_student_ai_summary(db: Session, student_id: int) -> Dict[str, Any]:
    """
    Generates an anonymized, grounded draft record summary for staff decision support.
    Returns unavailable status if AI_ENABLED is False or environment is unconfigured.
    """
    ai_enabled = os.getenv("AI_ENABLED", "false").lower() in ("true", "1") or settings.AI_ENABLED
    if not ai_enabled:
        return {
            "available": False,
            "status": "unavailable",
            "message": "AI summaries unavailable",
            "is_draft": False,
        }

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise ValueError(f"Student #{student_id} not found.")

    # 1. Anonymization Protocol (Strip PII)
    # Never use student.full_name, emis_id, guardian_name, guardian_phone, or address
    anonymized_id = f"REF-{student.id:04d}"
    class_label = f"Grade {student.class_section.grade}-{student.class_section.section}" if student.class_section else "Unassigned"

    # 2. Collect Concrete Grounded Records
    att_records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id == student_id, AttendanceRecord.is_superseded == False)
        .all()
    )
    asm_records = (
        db.query(AssessmentRecord)
        .filter(AssessmentRecord.student_id == student_id, AssessmentRecord.is_superseded == False)
        .all()
    )
    asg_records = (
        db.query(AssignmentRecord)
        .filter(AssignmentRecord.student_id == student_id, AssignmentRecord.is_superseded == False)
        .all()
    )
    ind_records = (
        db.query(WarningIndicator)
        .filter(WarningIndicator.student_id == student_id, WarningIndicator.is_superseded == False)
        .all()
    )

    period_map = {p.id: p.name for p in db.query(ReportingPeriod).all()}
    sources_cited: List[str] = []
    summary_points: List[str] = []

    # Ground Attendance Findings
    if att_records:
        for r in att_records:
            cite = f"[ATT-{r.id}]"
            sources_cited.append(cite)
            p_name = period_map.get(r.reporting_period_id, "Period")
            att_pct = f"{r.attendance_percentage:.1f}%" if r.attendance_percentage is not None else "N/A"
            days_pres = r.days_present if r.days_present is not None else "N/A"
            tot_days = r.total_instructional_days if r.total_instructional_days is not None else "N/A"
            summary_points.append(
                f"Attendance for {p_name} was {att_pct} ({days_pres}/{tot_days} instructional days) {cite}."
            )
    else:
        summary_points.append("No historical attendance records logged for this student.")

    # Ground Assessment Findings
    if asm_records:
        for a in asm_records:
            cite = f"[ASM-{a.id}]"
            sources_cited.append(cite)
            summary_points.append(
                f"Scored {a.percentage:.1f}% ({a.marks_obtained}/{a.max_marks}) in {a.subject} "
                f"during assessment '{a.assessment_name}' on {a.assessment_date} {cite}."
            )
    else:
        summary_points.append("No assessment records logged for this student.")

    # Ground Assignment Findings
    if asg_records:
        completed = sum(1 for asg in asg_records if asg.is_completed)
        cite_str = ", ".join(f"[ASG-{asg.id}]" for asg in asg_records[:3])
        sources_cited.extend(f"[ASG-{asg.id}]" for asg in asg_records)
        summary_points.append(
            f"Submitted {completed} of {len(asg_records)} assigned tasks {cite_str}."
        )

    # Ground Early Warning Indicators
    if ind_records:
        for ind in ind_records:
            cite = f"[IND-{ind.id}]"
            sources_cited.append(cite)
            summary_points.append(
                f"Active indicator {ind.rule_code} ({ind.priority} Priority): {ind.plain_explanation} {cite}."
            )

    # Synthesize Draft Summary with citations
    findings_prose = " ".join(summary_points)
    draft_summary_text = (
        f"DECISION-SUPPORT DRAFT FOR {anonymized_id} ({class_label}): "
        f"{findings_prose} "
        "Recommendation for staff: Review underlying records and evaluate whether individualized remedial instruction "
        "or attendance verification is warranted."
    )

    return {
        "available": True,
        "status": "DRAFT",
        "is_draft": True,
        "requires_human_approval": True,
        "student_id": student.id,
        "anonymized_reference_id": anonymized_id,
        "class_label": class_label,
        "summary_text": draft_summary_text,
        "sources_cited": sorted(list(set(sources_cited))),
        "disclaimer": (
            "DRAFT AI-generated summary for staff decision support only. "
            "Grounded strictly in verified school records. Requires explicit human review and approval before saving."
        ),
    }


def approve_and_save_ai_summary(
    db: Session,
    student_id: int,
    staff_user_id: int,
    approved_text: str,
    case_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Saves a staff-reviewed and explicitly approved summary as a permanent case note
    or support observation, recording who approved it and when.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise ValueError(f"Student #{student_id} not found.")

    staff = db.query(User).filter(User.id == staff_user_id).first()
    if not staff:
        raise ValueError(f"Staff user #{staff_user_id} not found.")

    # If no case_id specified, find or create an active case
    if not case_id:
        active_case = (
            db.query(SupportCase)
            .filter(SupportCase.student_id == student_id, SupportCase.status != "Closed")
            .first()
        )
        if not active_case:
            active_case = SupportCase(
                student_id=student_id,
                school_id=student.school_id,
                assigned_staff_id=staff_user_id,
                category="general_support",
                priority="Medium",
                status="Open",
                reason=f"Support initiated following staff-approved record review",
                observations="Approved summary appended to record history.",
            )
            db.add(active_case)
            db.flush()
        case_id = active_case.id

    note = CaseNote(
        case_id=case_id,
        author_id=staff_user_id,
        note_text=approved_text,
        is_sensitive=False,
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    return {
        "status": "APPROVED_AND_SAVED",
        "note_id": note.id,
        "case_id": case_id,
        "approved_by": staff.full_name,
        "saved_at": note.created_at.isoformat(),
        "message": "Summary approved by staff and saved to support case record.",
    }
