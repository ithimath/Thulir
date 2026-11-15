"""Shared Event-Timeline Service (Locked Decision Section 3).

Provides a single unified chronological timeline of student support events:
- Indicators detected & rule thresholds applied
- Review decisions recorded by staff
- Data corrections proposed and approved
- Support cases opened and updated
- Interventions assigned and started
- Follow-ups scheduled and completed
- Qualitative staff observations & case notes (with strict role-based confidentiality)
"""
import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.models import (
    Student,
    WarningIndicator,
    IndicatorReview,
    SupportCase,
    Intervention,
    FollowUp,
    CaseNote,
    DataCorrection,
    User,
)
from backend.app.middleware.auth_middleware import AuthenticatedUser


def _format_dt(dt: Optional[datetime.datetime]) -> str:
    if not dt:
        return datetime.datetime.utcnow().isoformat()
    return dt.isoformat()


def _format_date(d: Optional[datetime.date]) -> str:
    if not d:
        return datetime.datetime.utcnow().isoformat()
    # Convert date to midday UTC datetime string for chronological placement
    return datetime.datetime.combine(d, datetime.time(12, 0)).isoformat()


def build_student_timeline(
    db: Session,
    student_id: int,
    school_id: int,
    auth: AuthenticatedUser,
    case_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Build a unified, sorted chronological list of events for a student or specific case."""
    events: List[Dict[str, Any]] = []

    # 1. Warning Indicators & Reviews
    ind_query = db.query(WarningIndicator).filter(
        WarningIndicator.student_id == student_id,
        WarningIndicator.school_id == school_id,
    )
    indicators = ind_query.all()
    for ind in indicators:
        # If filtering by case_id, only include if linked to this case
        if case_id:
            linked_case = db.query(SupportCase).filter(
                SupportCase.id == case_id,
                SupportCase.indicator_id == ind.id,
            ).first()
            if not linked_case:
                continue

        events.append({
            "id": f"ind-{ind.id}",
            "event_type": "indicator_detected",
            "category": "indicator",
            "timestamp": _format_dt(ind.detected_at or ind.created_at),
            "title": f"Indicator Flagged: {ind.rule_code} ({ind.priority} Priority)",
            "description": ind.plain_explanation,
            "status": ind.status,
            "priority": ind.priority,
            "actor": "THULIR Rule Engine",
            "actor_role": "Automated Early-Warning Engine",
            "is_confidential": False,
            "metadata": {
                "indicator_id": ind.id,
                "rule_code": ind.rule_code,
                "rule_version": ind.rule_version,
                "indicator_category": ind.category,
                "threshold_applied": ind.threshold_applied,
                "is_superseded": ind.is_superseded,
                "supporting_evidence": ind.supporting_evidence,
            },
        })

        # Indicator Reviews
        for rev in ind.reviews:
            reviewer_name = rev.reviewer.full_name if rev.reviewer else "Staff"
            reviewer_desig = rev.reviewer.designation if rev.reviewer else "Reviewer"
            events.append({
                "id": f"rev-{rev.id}",
                "event_type": "indicator_reviewed",
                "category": "review",
                "timestamp": _format_dt(rev.created_at),
                "title": f"Human Review: Status changed to '{rev.new_status}'",
                "description": rev.review_notes,
                "status": rev.new_status,
                "priority": ind.priority,
                "actor": reviewer_name,
                "actor_role": reviewer_desig,
                "is_confidential": False,
                "metadata": {
                    "review_id": rev.id,
                    "indicator_id": ind.id,
                    "previous_status": rev.previous_status,
                    "new_status": rev.new_status,
                },
            })

    # 2. Support Cases
    case_query = db.query(SupportCase).filter(
        SupportCase.student_id == student_id,
        SupportCase.school_id == school_id,
    )
    if case_id:
        case_query = case_query.filter(SupportCase.id == case_id)

    cases = case_query.all()
    for sc in cases:
        creator_name = sc.creator.full_name if sc.creator else "Staff"
        creator_desig = sc.creator.designation if sc.creator else "Staff"
        assigned_name = sc.assigned_staff.full_name if sc.assigned_staff else "Unassigned"

        events.append({
            "id": f"case-{sc.id}",
            "event_type": "case_created",
            "category": "case",
            "timestamp": _format_dt(sc.created_at),
            "title": f"Support Case Opened: {sc.case_number}",
            "description": sc.reason + (f" Observations: {sc.observations}" if sc.observations else ""),
            "status": sc.status,
            "priority": sc.priority,
            "actor": creator_name,
            "actor_role": creator_desig,
            "is_confidential": False,
            "metadata": {
                "case_id": sc.id,
                "case_number": sc.case_number,
                "case_category": sc.category,
                "assigned_to": assigned_name,
                "indicator_id": sc.indicator_id,
                "review_date": str(sc.review_date) if sc.review_date else None,
            },
        })

        # Interventions
        for inv in sc.interventions:
            staff_name = inv.assigned_staff.full_name if inv.assigned_staff else "Staff"
            staff_desig = inv.assigned_staff.designation if inv.assigned_staff else "Staff"
            events.append({
                "id": f"inv-{inv.id}",
                "event_type": "intervention_started",
                "category": "intervention",
                "timestamp": _format_date(inv.start_date),
                "title": f"Intervention: {inv.title} ({inv.status})",
                "description": inv.description + (f" Outcome: {inv.outcome_notes}" if inv.outcome_notes else ""),
                "status": inv.status,
                "priority": sc.priority,
                "actor": staff_name,
                "actor_role": staff_desig,
                "is_confidential": False,
                "metadata": {
                    "intervention_id": inv.id,
                    "case_id": sc.id,
                    "case_number": sc.case_number,
                    "intervention_type": inv.intervention_type,
                    "start_date": str(inv.start_date),
                    "target_date": str(inv.target_date) if inv.target_date else None,
                    "completion_date": str(inv.completion_date) if inv.completion_date else None,
                    "has_baseline": bool(inv.baseline_snapshot),
                },
            })

        # Follow-ups
        for fu in sc.follow_ups:
            fu_staff = fu.assigned_staff.full_name if fu.assigned_staff else "Staff"
            fu_desig = fu.assigned_staff.designation if fu.assigned_staff else "Staff"
            fu_timestamp = _format_date(fu.completion_date if fu.status == "Completed" and fu.completion_date else fu.due_date)
            events.append({
                "id": f"fu-{fu.id}",
                "event_type": "follow_up_completed" if fu.status == "Completed" else "follow_up_scheduled",
                "category": "follow_up",
                "timestamp": fu_timestamp,
                "title": f"Follow-up: {fu.status} (Due: {fu.due_date})",
                "description": fu.notes or "Scheduled review check-in.",
                "status": fu.status,
                "priority": "Medium",
                "actor": fu_staff,
                "actor_role": fu_desig,
                "is_confidential": False,
                "metadata": {
                    "follow_up_id": fu.id,
                    "case_id": sc.id,
                    "case_number": sc.case_number,
                    "intervention_id": fu.intervention_id,
                    "due_date": str(fu.due_date),
                    "completion_date": str(fu.completion_date) if fu.completion_date else None,
                },
            })

        # Case Notes with strict RBAC scoping
        # Only designated counsellors or assigned staff can see sensitive notes
        can_view_sensitive = (
            auth.role_name == "counsellor" or
            (auth.id == sc.assigned_staff_id and auth.role_name != "teacher")
        )
        for note in sc.case_notes:
            if note.is_sensitive and not can_view_sensitive:
                # Omit completely for teachers and unauthorized staff
                continue

            note_author = note.author.full_name if note.author else "Staff"
            note_desig = note.author.designation if note.author else "Staff"
            events.append({
                "id": f"note-{note.id}",
                "event_type": "case_note",
                "category": "note",
                "timestamp": _format_dt(note.created_at),
                "title": "Confidential Counselling Note" if note.is_sensitive else "Case Progress Observation",
                "description": note.note_text,
                "status": "Recorded",
                "priority": "High" if note.is_sensitive else "Routine",
                "actor": note_author,
                "actor_role": note_desig,
                "is_confidential": note.is_sensitive,
                "metadata": {
                    "note_id": note.id,
                    "case_id": sc.id,
                    "case_number": sc.case_number,
                    "is_sensitive": note.is_sensitive,
                },
            })

    # 3. Data Corrections (Feature 2)
    corr_query = db.query(DataCorrection).filter(
        DataCorrection.student_id == student_id,
        DataCorrection.school_id == school_id,
    )
    corrections = corr_query.all()
    for corr in corrections:
        proposer_name = corr.proposer.full_name if corr.proposer else "Teacher"
        proposer_desig = corr.proposer.designation if corr.proposer else "Staff"
        approver_name = corr.approver.full_name if corr.approver else "Admin"

        events.append({
            "id": f"corr-{corr.id}",
            "event_type": "correction_approved" if corr.status == "Approved" else "correction_proposed",
            "category": "correction",
            "timestamp": _format_dt(corr.approved_at if corr.status == "Approved" and corr.approved_at else corr.created_at),
            "title": f"Data Verification: {corr.record_type.capitalize()} Record ({corr.status})",
            "description": f"Reason: {corr.reason}. Proposed by {proposer_name}" + (f", approved by {approver_name}" if corr.status == "Approved" else ""),
            "status": corr.status,
            "priority": "Medium",
            "actor": approver_name if corr.status == "Approved" else proposer_name,
            "actor_role": "Administrator" if corr.status == "Approved" else proposer_desig,
            "is_confidential": False,
            "metadata": {
                "correction_id": corr.id,
                "record_type": corr.record_type,
                "target_record_id": corr.target_record_id,
                "superseding_record_id": corr.superseding_record_id,
                "status": corr.status,
                "original_data": corr.original_data,
                "proposed_data": corr.proposed_data,
            },
        })

    # Sort all events chronologically (earliest to latest)
    events.sort(key=lambda e: e["timestamp"])
    return events

