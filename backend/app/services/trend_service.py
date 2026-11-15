"""Historical Trend Comparison Service (Feature 8).

Civic Data Integrity Rule:
Never interpolate or fabricate missing historical records.
Missing periods are surfaced as explicit gaps with explanations.
All trajectories are derived strictly from concrete database records.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import asc

from backend.app.models.models import (
    Student,
    AttendanceRecord,
    AssessmentRecord,
    AssignmentRecord,
    WarningIndicator,
    ReportingPeriod,
    AcademicYear,
    ClassSection,
)


def get_student_historical_trends(db: Session, student_id: int) -> Dict[str, Any]:
    """
    Assembles chronological longitudinal trajectories for attendance, marks by subject,
    and assignments, with explicit gap identification for missing reporting periods.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise ValueError(f"Student #{student_id} not found.")

    # 1. Load all active reporting periods in sequence order
    periods = (
        db.query(ReportingPeriod)
        .join(AcademicYear, ReportingPeriod.academic_year_id == AcademicYear.id)
        .filter(AcademicYear.school_id == student.school_id)
        .order_by(asc(ReportingPeriod.sequence_order))
        .all()
    )

    # 2. Attendance history
    att_records = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.record_date == None,
            AttendanceRecord.is_superseded == False,
        )
        .all()
    )
    att_by_period_id = {r.reporting_period_id: r for r in att_records}

    attendance_trend = []
    cumulative_days_present = 0.0
    cumulative_total_days = 0.0

    for p in periods:
        rec = att_by_period_id.get(p.id)
        if rec and rec.total_instructional_days and rec.total_instructional_days > 0:
            cumulative_days_present += rec.days_present or 0.0
            cumulative_total_days += rec.total_instructional_days
            attendance_trend.append({
                "period_id": p.id,
                "period_name": p.name,
                "academic_year": p.academic_year.year_name if p.academic_year else "Current",
                "days_present": rec.days_present,
                "total_days": rec.total_instructional_days,
                "attendance_percentage": round(rec.attendance_percentage, 1) if rec.attendance_percentage else None,
                "has_data": True,
            })
        else:
            # Explicit gap marker — never fabricate or interpolate
            attendance_trend.append({
                "period_id": p.id,
                "period_name": p.name,
                "academic_year": p.academic_year.year_name if p.academic_year else "Current",
                "days_present": None,
                "total_days": None,
                "attendance_percentage": None,
                "has_data": False,
                "gap_reason": "No attendance records registered for this reporting period",
            })

    historical_attendance_baseline = (
        round((cumulative_days_present / cumulative_total_days) * 100.0, 1)
        if cumulative_total_days > 0 else None
    )

    # 3. Assessment trajectories by subject
    assessments = (
        db.query(AssessmentRecord)
        .filter(
            AssessmentRecord.student_id == student_id,
            AssessmentRecord.is_superseded == False,
        )
        .order_by(asc(AssessmentRecord.assessment_date))
        .all()
    )

    subjects_trend = defaultdict(list)
    for a in assessments:
        subjects_trend[a.subject].append({
            "assessment_name": a.assessment_name,
            "date": str(a.assessment_date),
            "marks_obtained": a.marks_obtained,
            "max_marks": a.max_marks,
            "percentage": round(a.percentage, 1) if a.percentage else None,
        })

    # 4. Indicators trajectory over time (resolved vs persisted vs escalated)
    indicators = (
        db.query(WarningIndicator)
        .filter(
            WarningIndicator.student_id == student_id,
            WarningIndicator.is_superseded == False,
        )
        .order_by(asc(WarningIndicator.detected_at))
        .all()
    )

    indicators_by_period = defaultdict(list)
    for ind in indicators:
        ev = ind.supporting_evidence if isinstance(ind.supporting_evidence, dict) else {}
        p_name = ev.get("period") or ev.get("current_period") or "General"
        indicators_by_period[p_name].append({
            "id": ind.id,
            "rule_code": ind.rule_code,
            "category": ind.category,
            "priority": ind.priority,
            "status": ind.status,
            "detected_at": ind.detected_at.isoformat() if ind.detected_at else None,
        })

    return {
        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "emis_id": student.emis_id,
        },
        "attendance_trend": attendance_trend,
        "historical_attendance_baseline": historical_attendance_baseline,
        "academic_subject_trends": dict(subjects_trend),
        "indicators_by_period": dict(indicators_by_period),
        "disclaimer": "Longitudinal trajectories reflect concrete records. Gaps indicate missing data, not zero attendance.",
    }


def get_class_aggregate_trends(
    db: Session,
    school_id: int,
    grade: int,
    section: str,
) -> Dict[str, Any]:
    """
    Computes class-level aggregate attendance, average assessment scores,
    and active indicator counts across reporting periods.
    """
    cs = (
        db.query(ClassSection)
        .filter(
            ClassSection.school_id == school_id,
            ClassSection.grade == grade,
            ClassSection.section == section,
        )
        .first()
    )
    if not cs:
        raise ValueError(f"Class {grade}-{section} not found.")

    student_ids = [s.id for s in cs.students if s.is_active]
    if not student_ids:
        return {
            "class_section": f"{grade}-{section}",
            "enrolled_students": 0,
            "period_aggregates": [],
        }

    periods = (
        db.query(ReportingPeriod)
        .join(AcademicYear, ReportingPeriod.academic_year_id == AcademicYear.id)
        .filter(AcademicYear.school_id == school_id)
        .order_by(asc(ReportingPeriod.sequence_order))
        .all()
    )

    period_aggregates = []
    for p in periods:
        records = (
            db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.student_id.in_(student_ids),
                AttendanceRecord.reporting_period_id == p.id,
                AttendanceRecord.is_superseded == False,
                AttendanceRecord.total_instructional_days > 0,
            )
            .all()
        )

        if records:
            total_pres = sum(r.days_present or 0.0 for r in records)
            total_inst = sum(r.total_instructional_days for r in records)
            avg_att = round((total_pres / total_inst) * 100.0, 1) if total_inst > 0 else None
            period_aggregates.append({
                "period_id": p.id,
                "period_name": p.name,
                "students_reported": len(records),
                "total_enrolled": len(student_ids),
                "average_attendance_pct": avg_att,
                "has_data": True,
            })
        else:
            period_aggregates.append({
                "period_id": p.id,
                "period_name": p.name,
                "students_reported": 0,
                "total_enrolled": len(student_ids),
                "average_attendance_pct": None,
                "has_data": False,
                "gap_reason": "No periodic records logged for this class in this reporting period.",
            })

    return {
        "class_section": f"{grade}-{section}",
        "enrolled_students": len(student_ids),
        "period_aggregates": period_aggregates,
    }
