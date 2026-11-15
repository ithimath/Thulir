"""Intervention Effectiveness Tracker Service (Feature 4).

Captures baseline snapshots upon intervention inception, and performs
factual before-and-after comparisons with later records.
Enforces the mandatory disclaimer: 'observed change, not proof that the intervention caused it'.
"""
import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.models import (
    Student,
    AttendanceRecord,
    AssessmentRecord,
    AssignmentRecord,
    Intervention,
    ReportingPeriod,
)

DISCLAIMER_LABEL = "observed change, not proof that the intervention caused it"


def capture_baseline_snapshot(db: Session, student_id: int, school_id: int) -> Dict[str, Any]:
    """Capture snapshot of attendance, assessments, and assignments at intervention start."""
    snapshot: Dict[str, Any] = {
        "snapshot_date": datetime.date.today().isoformat(),
        "disclaimer": DISCLAIMER_LABEL,
        "attendance": None,
        "assessments": [],
        "assignments": None,
    }

    # 1. Latest non-superseded attendance record
    latest_att = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student_id,
        AttendanceRecord.school_id == school_id,
        AttendanceRecord.is_superseded == False,
        AttendanceRecord.attendance_percentage != None,
    ).order_by(desc(AttendanceRecord.created_at)).first()

    if latest_att:
        period_name = None
        if latest_att.reporting_period_id:
            period = db.query(ReportingPeriod).filter(ReportingPeriod.id == latest_att.reporting_period_id).first()
            period_name = period.name if period else None

        snapshot["attendance"] = {
            "record_id": latest_att.id,
            "period_name": period_name,
            "attendance_percentage": round(latest_att.attendance_percentage, 2),
            "days_present": latest_att.days_present,
            "total_days": latest_att.total_instructional_days,
            "record_date": str(latest_att.record_date) if latest_att.record_date else None,
        }

    # 2. Latest assessment records per subject
    assessments = db.query(AssessmentRecord).filter(
        AssessmentRecord.student_id == student_id,
        AssessmentRecord.school_id == school_id,
        AssessmentRecord.is_superseded == False,
    ).order_by(desc(AssessmentRecord.assessment_date)).all()

    seen_subjects = set()
    latest_assessments = []
    for asm in assessments:
        if asm.subject not in seen_subjects:
            seen_subjects.add(asm.subject)
            period_name = None
            if asm.reporting_period_id:
                period = db.query(ReportingPeriod).filter(ReportingPeriod.id == asm.reporting_period_id).first()
                period_name = period.name if period else None
            latest_assessments.append({
                "record_id": asm.id,
                "subject": asm.subject,
                "assessment_name": asm.assessment_name,
                "period_name": period_name,
                "marks_obtained": asm.marks_obtained,
                "max_marks": asm.max_marks,
                "percentage": round(asm.percentage, 2),
                "date": str(asm.assessment_date),
            })
    snapshot["assessments"] = latest_assessments

    # 3. Latest assignment completion rate
    assignments = db.query(AssignmentRecord).filter(
        AssignmentRecord.student_id == student_id,
        AssignmentRecord.school_id == school_id,
        AssignmentRecord.is_superseded == False,
    ).order_by(desc(AssignmentRecord.assignment_date)).all()

    if assignments:
        total = len(assignments)
        completed = sum(1 for a in assignments if a.status in ["submitted", "late"])
        pct = round((completed / total) * 100.0, 2) if total > 0 else 0.0
        snapshot["assignments"] = {
            "total_count": total,
            "completed_count": completed,
            "completion_rate": pct,
        }

    return snapshot


def compute_intervention_comparison(
    db: Session,
    intervention: Intervention,
) -> Dict[str, Any]:
    """Compare later records against the baseline snapshot.

    Returns actual values and differences only. Shows 'insufficient data' if too few later records.
    """
    case = intervention.case
    student_id = case.student_id
    school_id = case.school_id
    start_date = intervention.start_date
    baseline = intervention.baseline_snapshot or {}

    result = {
        "intervention_id": intervention.id,
        "title": intervention.title,
        "status": intervention.status,
        "start_date": str(intervention.start_date),
        "target_date": str(intervention.target_date) if intervention.target_date else None,
        "completion_date": str(intervention.completion_date) if intervention.completion_date else None,
        "disclaimer": DISCLAIMER_LABEL,
        "has_baseline": bool(baseline),
        "baseline_snapshot": baseline,
        "attendance_comparison": None,
        "academic_comparison": [],
        "assignment_comparison": None,
        "has_sufficient_later_data": False,
    }

    if not baseline:
        return result

    # 1. Check later attendance (records created/dated after intervention start)
    later_att = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student_id,
        AttendanceRecord.school_id == school_id,
        AttendanceRecord.is_superseded == False,
        AttendanceRecord.attendance_percentage != None,
    ).all()

    # Filter to records occurring strictly after baseline record
    baseline_att = baseline.get("attendance")
    baseline_att_id = baseline_att.get("record_id") if baseline_att else None
    valid_later_att = [a for a in later_att if a.id != baseline_att_id and (
        (a.record_date and a.record_date > start_date) or
        (a.created_at.date() > start_date)
    )]

    if baseline_att and valid_later_att:
        latest_after = sorted(valid_later_att, key=lambda a: a.record_date or a.created_at.date(), reverse=True)[0]
        base_pct = baseline_att["attendance_percentage"]
        curr_pct = round(latest_after.attendance_percentage, 2)
        diff = round(curr_pct - base_pct, 2)
        result["attendance_comparison"] = {
            "status": "sufficient_data",
            "baseline_value": base_pct,
            "current_value": curr_pct,
            "absolute_difference": diff,
            "period_name": baseline_att.get("period_name"),
            "later_record_date": str(latest_after.record_date or latest_after.created_at.date()),
            "direction": "improved" if diff > 0 else ("declined" if diff < 0 else "unchanged"),
        }
        result["has_sufficient_later_data"] = True
    else:
        result["attendance_comparison"] = {
            "status": "insufficient_data",
            "message": "insufficient data",
            "baseline_value": baseline_att["attendance_percentage"] if baseline_att else None,
            "current_value": None,
            "absolute_difference": None,
        }

    # 2. Check later assessment marks per subject
    baseline_asms = {a["subject"]: a for a in baseline.get("assessments", [])}
    later_asms = db.query(AssessmentRecord).filter(
        AssessmentRecord.student_id == student_id,
        AssessmentRecord.school_id == school_id,
        AssessmentRecord.is_superseded == False,
        AssessmentRecord.assessment_date > start_date,
    ).order_by(desc(AssessmentRecord.assessment_date)).all()

    seen_subj_later = set()
    for l_asm in later_asms:
        if l_asm.subject not in seen_subj_later and l_asm.subject in baseline_asms:
            seen_subj_later.add(l_asm.subject)
            base_info = baseline_asms[l_asm.subject]
            base_score = base_info["percentage"]
            curr_score = round(l_asm.percentage, 2)
            diff = round(curr_score - base_score, 2)
            result["academic_comparison"].append({
                "subject": l_asm.subject,
                "status": "sufficient_data",
                "baseline_assessment": base_info["assessment_name"],
                "baseline_value": base_score,
                "current_assessment": l_asm.assessment_name,
                "current_value": curr_score,
                "absolute_difference": diff,
                "direction": "improved" if diff > 0 else ("declined" if diff < 0 else "unchanged"),
                "date": str(l_asm.assessment_date),
            })
            result["has_sufficient_later_data"] = True

    # Check for subjects that have no later data
    for subj, base_info in baseline_asms.items():
        if subj not in seen_subj_later:
            result["academic_comparison"].append({
                "subject": subj,
                "status": "insufficient_data",
                "message": "insufficient data",
                "baseline_assessment": base_info["assessment_name"],
                "baseline_value": base_info["percentage"],
                "current_assessment": None,
                "current_value": None,
                "absolute_difference": None,
            })

    # 3. Check later assignment completion
    baseline_asg = baseline.get("assignments")
    later_asgs = db.query(AssignmentRecord).filter(
        AssignmentRecord.student_id == student_id,
        AssignmentRecord.school_id == school_id,
        AssignmentRecord.is_superseded == False,
        AssignmentRecord.assignment_date > start_date,
    ).all()

    if baseline_asg and len(later_asgs) >= 2:
        tot = len(later_asgs)
        comp = sum(1 for a in later_asgs if a.status in ["submitted", "late"])
        curr_rate = round((comp / tot) * 100.0, 2)
        base_rate = baseline_asg["completion_rate"]
        diff = round(curr_rate - base_rate, 2)
        result["assignment_comparison"] = {
            "status": "sufficient_data",
            "baseline_value": base_rate,
            "current_value": curr_rate,
            "absolute_difference": diff,
            "later_records_count": tot,
            "direction": "improved" if diff > 0 else ("declined" if diff < 0 else "unchanged"),
        }
        result["has_sufficient_later_data"] = True
    else:
        result["assignment_comparison"] = {
            "status": "insufficient_data",
            "message": "insufficient data",
            "baseline_value": baseline_asg["completion_rate"] if baseline_asg else None,
            "current_value": None,
            "absolute_difference": None,
        }

    # Overall outcome category: improving | declining | no_significant_change | insufficient_data
    if not result["has_sufficient_later_data"]:
        result["outcome_category"] = "insufficient_data"
        result["baseline_value"] = baseline.get("attendance", {}).get("attendance_percentage")
        result["current_value"] = None
        result["change_delta"] = None
    else:
        # Determine from attendance or academic
        att_comp = result["attendance_comparison"]
        if att_comp and att_comp.get("status") == "sufficient_data":
            diff = att_comp["absolute_difference"]
            result["baseline_value"] = att_comp["baseline_value"]
            result["current_value"] = att_comp["current_value"]
            result["change_delta"] = diff
            if diff >= 2.0:
                result["outcome_category"] = "improving"
            elif diff <= -2.0:
                result["outcome_category"] = "declining"
            else:
                result["outcome_category"] = "no_significant_change"
        elif result["academic_comparison"]:
            diffs = [a["absolute_difference"] for a in result["academic_comparison"] if a.get("status") == "sufficient_data" and a.get("absolute_difference") is not None]
            if diffs:
                avg_diff = sum(diffs) / len(diffs)
                first_acad = [a for a in result["academic_comparison"] if a.get("status") == "sufficient_data"][0]
                result["baseline_value"] = first_acad["baseline_value"]
                result["current_value"] = first_acad["current_value"]
                result["change_delta"] = round(avg_diff, 2)
                if avg_diff >= 3.0:
                    result["outcome_category"] = "improving"
                elif avg_diff <= -3.0:
                    result["outcome_category"] = "declining"
                else:
                    result["outcome_category"] = "no_significant_change"
            else:
                result["outcome_category"] = "insufficient_data"
                result["baseline_value"] = None
                result["current_value"] = None
                result["change_delta"] = None
        else:
            result["outcome_category"] = "insufficient_data"
            result["baseline_value"] = None
            result["current_value"] = None
            result["change_delta"] = None

    return result
