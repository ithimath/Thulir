"""
Deterministic rule-based early-warning engine for THULIR.

Rules implemented:
  ATT-LOW    : Latest period attendance_pct < 75.0 (strictly less than)
  ATT-DECLINE: Attendance dropped >= 10.0 pp between consecutive periods
  ATT-CONSEC : 3+ consecutive daily 'absent' records
  MARK-LOW   : Any latest assessment percentage < 35.0 (strictly less than)
  MARK-DECLINE: 3+ consecutive assessments each lower than previous, cumulative drop >= 15 pp
  ASG-LOW    : Completion rate < 60.0% with >= 3 assignments in latest period
  ASG-DECLINE: Completion rate dropped >= 20.0 pp between consecutive periods (each with >= 3 assignments)

Boundary behaviour:
  - Exactly 75% does NOT trigger ATT-LOW.
  - Exactly 10pp drop DOES trigger ATT-DECLINE.
  - Exactly 35% does NOT trigger MARK-LOW.
  - Exactly 60% does NOT trigger ASG-LOW.
  - Exactly 20pp drop DOES trigger ASG-DECLINE.

Each indicator is idempotent: a (student_id, rule_code, evidence_key) tuple is unique.
"""
from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.models import (
    AttendanceRecord,
    AssessmentRecord,
    AssignmentRecord,
    Student,
    WarningIndicator,
    WarningRule,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class IndicatorResult:
    rule_code: str
    priority: str
    category: str
    plain_explanation: str
    supporting_evidence: dict
    threshold_applied: float
    data_quality_limitations: Optional[str]
    # Deduplication key — deterministic fingerprint of the evidence so the same
    # logical finding is not stored twice across engine runs.
    evidence_key: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _evidence_key(*parts: object) -> str:
    """Stable SHA-256 fingerprint from arbitrary hashable parts."""
    raw = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


# ---------------------------------------------------------------------------
# ATT-LOW
# ---------------------------------------------------------------------------

def check_att_low(
    attendance_by_period: list[tuple[str, float, float, float]]
) -> Optional[IndicatorResult]:
    """
    attendance_by_period: [(period_name, days_present, total_days, att_pct), ...]
                          sorted ascending by period sequence.
    Returns IndicatorResult if latest period att_pct < 75.0, else None.
    """
    periodic = [(n, dp, td, p) for n, dp, td, p in attendance_by_period
                if td is not None and td > 0]
    if not periodic:
        return None

    name, days_present, total_days, att_pct = periodic[-1]

    if att_pct >= 75.0:
        return None

    explanation = (
        f"Attendance in {name} is {att_pct:.1f}% "
        f"({int(days_present)} of {int(total_days)} days) — "
        f"below the 75% statutory floor."
    )
    evidence = {
        "period": name,
        "days_present": days_present,
        "total_days": total_days,
        "attendance_pct": att_pct,
    }
    return IndicatorResult(
        rule_code="ATT-LOW",
        priority="High",
        category="attendance",
        plain_explanation=explanation,
        supporting_evidence=evidence,
        threshold_applied=75.0,
        data_quality_limitations=None,
        evidence_key=_evidence_key("ATT-LOW", name, att_pct),
    )


# ---------------------------------------------------------------------------
# ATT-DECLINE
# ---------------------------------------------------------------------------

def check_att_decline(
    attendance_by_period: list[tuple[str, float, float, float]]
) -> Optional[IndicatorResult]:
    """Drop >= 10.0 pp between the two most recent periods with valid data."""
    periodic = [(n, dp, td, p) for n, dp, td, p in attendance_by_period
                if td is not None and td > 0]
    if len(periodic) < 2:
        return None

    prev_name, _, _, prev_pct = periodic[-2]
    curr_name, days_present, total_days, curr_pct = periodic[-1]
    drop = prev_pct - curr_pct

    if drop < 10.0:
        return None

    explanation = (
        f"Attendance fell from {prev_pct:.1f}% in {prev_name} "
        f"to {curr_pct:.1f}% in {curr_name} "
        f"(a drop of {drop:.1f} percentage points)."
    )
    evidence = {
        "previous_period": prev_name,
        "previous_pct": prev_pct,
        "current_period": curr_name,
        "current_pct": curr_pct,
        "drop_pp": round(drop, 2),
    }
    return IndicatorResult(
        rule_code="ATT-DECLINE",
        priority="Medium",
        category="attendance",
        plain_explanation=explanation,
        supporting_evidence=evidence,
        threshold_applied=10.0,
        data_quality_limitations=None,
        evidence_key=_evidence_key("ATT-DECLINE", prev_name, curr_name, round(drop, 2)),
    )


# ---------------------------------------------------------------------------
# ATT-CONSEC
# ---------------------------------------------------------------------------

def check_att_consec(
    daily_records: list[tuple[datetime.date, str]]
) -> Optional[IndicatorResult]:
    """
    daily_records: [(date, status), ...] sorted ascending by date.
    status one of 'present', 'absent', 'excused'.
    Triggers if 3+ consecutive 'absent' records exist (excused breaks the run).
    """
    if not daily_records:
        return None

    best_run_start: Optional[datetime.date] = None
    best_run_dates: list[datetime.date] = []
    current_run: list[datetime.date] = []

    for rec_date, status in daily_records:
        if status == "absent":
            current_run.append(rec_date)
            if len(current_run) > len(best_run_dates):
                best_run_dates = list(current_run)
                best_run_start = current_run[0]
        else:
            current_run = []

    if len(best_run_dates) < 3:
        return None

    dates_str = [str(d) for d in best_run_dates]
    explanation = (
        f"{len(best_run_dates)} consecutive absent days recorded "
        f"from {best_run_dates[0]} to {best_run_dates[-1]}."
    )
    evidence = {
        "consecutive_absent_days": len(best_run_dates),
        "start_date": str(best_run_dates[0]),
        "end_date": str(best_run_dates[-1]),
        "dates": dates_str,
    }
    return IndicatorResult(
        rule_code="ATT-CONSEC",
        priority="Medium",
        category="attendance",
        plain_explanation=explanation,
        supporting_evidence=evidence,
        threshold_applied=3.0,
        data_quality_limitations=None,
        evidence_key=_evidence_key("ATT-CONSEC", str(best_run_dates[0]), str(best_run_dates[-1]), len(best_run_dates)),
    )


# ---------------------------------------------------------------------------
# MARK-LOW
# ---------------------------------------------------------------------------

def check_mark_low(
    assessments: list[tuple[str, str, datetime.date, float, float, float]]
) -> Optional[IndicatorResult]:
    """
    assessments: [(name, subject, date, obtained, max_marks, pct), ...] sorted by date ascending.
    Triggers if the LATEST assessment for ANY subject is strictly < 35%.
    Returns the worst (lowest percentage) finding.
    """
    if not assessments:
        return None

    # Group by subject and take the latest assessment per subject
    subject_latest: dict[str, tuple] = {}
    for a_name, subject, a_date, obtained, max_marks, pct in assessments:
        if subject not in subject_latest or a_date > subject_latest[subject][2]:
            subject_latest[subject] = (a_name, subject, a_date, obtained, max_marks, pct)

    findings = [(a_name, subj, a_date, obt, mx, pct)
                for a_name, subj, a_date, obt, mx, pct in subject_latest.values()
                if pct < 35.0]
    if not findings:
        return None

    # Report the worst
    worst = min(findings, key=lambda x: x[5])
    a_name, subj, a_date, obt, mx, pct = worst
    explanation = (
        f"Latest {subj} assessment ({a_name} on {a_date}) scored {pct:.1f}% "
        f"({obt:.0f} / {mx:.0f} marks) — below the 35% pass threshold."
    )
    evidence = {
        "assessment_name": a_name,
        "subject": subj,
        "date": str(a_date),
        "marks_obtained": obt,
        "max_marks": mx,
        "percentage": pct,
        "other_low_subjects": [
            {"assessment": f[0], "subject": f[1], "pct": f[5]}
            for f in findings if f[1] != subj
        ],
    }
    return IndicatorResult(
        rule_code="MARK-LOW",
        priority="High",
        category="academic",
        plain_explanation=explanation,
        supporting_evidence=evidence,
        threshold_applied=35.0,
        data_quality_limitations=None,
        evidence_key=_evidence_key("MARK-LOW", subj, str(a_date), pct),
    )


# ---------------------------------------------------------------------------
# MARK-DECLINE
# ---------------------------------------------------------------------------

def check_mark_decline(
    assessments: list[tuple[str, str, datetime.date, float, float, float]]
) -> Optional[IndicatorResult]:
    """
    Triggers for each subject where there are 3+ consecutive assessments
    (sorted by date) each lower than the previous AND the cumulative drop >= 15 pp.
    Returns the worst subject finding.
    """
    if not assessments:
        return None

    # Group by subject
    by_subject: dict[str, list[tuple]] = {}
    for row in assessments:
        _, subj, _, _, _, _ = row
        by_subject.setdefault(subj, []).append(row)

    findings = []
    for subj, rows in by_subject.items():
        sorted_rows = sorted(rows, key=lambda x: x[2])  # sort by date
        # Find longest strictly declining consecutive sequence
        best: list[tuple] = []
        current: list[tuple] = [sorted_rows[0]]
        for i in range(1, len(sorted_rows)):
            if sorted_rows[i][5] < current[-1][5]:
                current.append(sorted_rows[i])
            else:
                if len(current) > len(best):
                    best = list(current)
                current = [sorted_rows[i]]
        if len(current) > len(best):
            best = list(current)

        if len(best) < 3:
            continue

        cumulative_drop = best[0][5] - best[-1][5]
        if cumulative_drop < 15.0:
            continue

        findings.append((subj, best, cumulative_drop))

    if not findings:
        return None

    # Report the subject with largest cumulative drop
    subj, best, cumulative_drop = max(findings, key=lambda x: x[2])
    first_pct = best[0][5]
    last_pct = best[-1][5]
    explanation = (
        f"{subj} scores declined across {len(best)} consecutive assessments "
        f"from {first_pct:.1f}% to {last_pct:.1f}% (drop of {cumulative_drop:.1f} pp)."
    )
    evidence = {
        "subject": subj,
        "consecutive_count": len(best),
        "cumulative_drop_pp": round(cumulative_drop, 2),
        "assessments": [
            {"name": r[0], "date": str(r[2]), "pct": r[5]} for r in best
        ],
    }
    return IndicatorResult(
        rule_code="MARK-DECLINE",
        priority="Medium",
        category="academic",
        plain_explanation=explanation,
        supporting_evidence=evidence,
        threshold_applied=15.0,
        data_quality_limitations=None,
        evidence_key=_evidence_key("MARK-DECLINE", subj, str(best[0][2]), str(best[-1][2])),
    )


# ---------------------------------------------------------------------------
# ASG-LOW
# ---------------------------------------------------------------------------

def check_asg_low(
    assignments_by_period: list[tuple[str, list[str]]]
) -> Optional[IndicatorResult]:
    """
    assignments_by_period: [(period_name, [status_list]), ...] sorted ascending.
    Each status is 'submitted', 'missing', or 'late'.
    Requires >= 3 assignments in the latest period.
    Triggers if completion rate (submitted + late) / total < 60%.
    """
    if not assignments_by_period:
        return None

    period_name, statuses = assignments_by_period[-1]
    total = len(statuses)
    if total < 3:
        return None

    completed = sum(1 for s in statuses if s in ("submitted", "late"))
    completion_rate = (completed / total) * 100.0

    if completion_rate >= 60.0:
        return None

    explanation = (
        f"Assignment completion in {period_name} is {completion_rate:.1f}% "
        f"({completed} of {total} assignments submitted) — below 60%."
    )
    evidence = {
        "period": period_name,
        "total_assignments": total,
        "completed": completed,
        "missing": total - completed,
        "completion_rate": round(completion_rate, 2),
    }
    return IndicatorResult(
        rule_code="ASG-LOW",
        priority="Medium",
        category="assignment",
        plain_explanation=explanation,
        supporting_evidence=evidence,
        threshold_applied=60.0,
        data_quality_limitations=None,
        evidence_key=_evidence_key("ASG-LOW", period_name, round(completion_rate, 2), total),
    )


# ---------------------------------------------------------------------------
# ASG-DECLINE
# ---------------------------------------------------------------------------

def check_asg_decline(
    assignments_by_period: list[tuple[str, list[str]]]
) -> Optional[IndicatorResult]:
    """
    Triggers if completion rate dropped >= 20 pp between the two most recent
    periods, each with >= 3 assignments.
    """
    valid = []
    for period_name, statuses in assignments_by_period:
        total = len(statuses)
        if total < 3:
            continue
        completed = sum(1 for s in statuses if s in ("submitted", "late"))
        rate = (completed / total) * 100.0
        valid.append((period_name, total, completed, rate))

    if len(valid) < 2:
        return None

    prev_name, prev_total, prev_completed, prev_rate = valid[-2]
    curr_name, curr_total, curr_completed, curr_rate = valid[-1]
    drop = prev_rate - curr_rate

    if drop < 20.0:
        return None

    explanation = (
        f"Assignment completion fell from {prev_rate:.1f}% in {prev_name} "
        f"to {curr_rate:.1f}% in {curr_name} "
        f"(drop of {drop:.1f} percentage points)."
    )
    evidence = {
        "previous_period": prev_name,
        "previous_rate": round(prev_rate, 2),
        "current_period": curr_name,
        "current_rate": round(curr_rate, 2),
        "drop_pp": round(drop, 2),
    }
    return IndicatorResult(
        rule_code="ASG-DECLINE",
        priority="Low",
        category="assignment",
        plain_explanation=explanation,
        supporting_evidence=evidence,
        threshold_applied=20.0,
        data_quality_limitations=None,
        evidence_key=_evidence_key("ASG-DECLINE", prev_name, curr_name, round(drop, 2)),
    )


# ---------------------------------------------------------------------------
# DB persistence layer
# ---------------------------------------------------------------------------

def _get_rule(db: Session, rule_code: str) -> Optional[WarningRule]:
    return db.query(WarningRule).filter(
        WarningRule.rule_code == rule_code,
        WarningRule.is_active == True,
    ).first()


def _indicator_exists(db: Session, student_id: int, rule_code: str, evidence_key: str) -> bool:
    """Check by evidence_key stored in supporting_evidence JSON field."""
    existing = db.query(WarningIndicator).filter(
        WarningIndicator.student_id == student_id,
        WarningIndicator.rule_code == rule_code,
        WarningIndicator.status.notin_(["Closed", "Reviewed - No Action"]),
    ).all()
    for ind in existing:
        if isinstance(ind.supporting_evidence, dict):
            if ind.supporting_evidence.get("_evidence_key") == evidence_key:
                return True
    return False


def _persist_indicator(
    db: Session,
    student: Student,
    result: IndicatorResult,
) -> Optional[WarningIndicator]:
    """
    Persist an IndicatorResult to DB if it doesn't already exist (idempotent).
    Returns the new WarningIndicator or None if already present.
    """
    rule = _get_rule(db, result.rule_code)
    if not rule:
        return None  # Rule not active / not in DB — skip silently

    if _indicator_exists(db, student.id, result.rule_code, result.evidence_key):
        return None  # Already recorded

    evidence_with_key = dict(result.supporting_evidence)
    evidence_with_key["_evidence_key"] = result.evidence_key

    indicator = WarningIndicator(
        school_id=student.school_id,
        student_id=student.id,
        rule_id=rule.id,
        rule_code=result.rule_code,
        rule_version=rule.version,
        category=result.category,
        priority=result.priority,
        status="Needs Review",
        plain_explanation=result.plain_explanation,
        supporting_evidence=evidence_with_key,
        threshold_applied=result.threshold_applied,
        data_quality_limitations=result.data_quality_limitations,
        detected_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(indicator)
    db.flush()  # get .id without committing full transaction
    return indicator


# ---------------------------------------------------------------------------
# Main engine entry point
# ---------------------------------------------------------------------------

def run_engine_for_student(db: Session, student: Student) -> list[WarningIndicator]:
    """
    Run all 7 rules for a single student. Returns list of newly created indicators.
    Safe to call repeatedly — idempotent via evidence_key.
    """
    new_indicators: list[WarningIndicator] = []

    # --- Load data ---

    # Attendance records (periodic aggregates sorted by sequence order)
    from sqlalchemy import asc
    from backend.app.models.models import ReportingPeriod

    att_periodic_rows = (
        db.query(
            ReportingPeriod.name,
            ReportingPeriod.sequence_order,
            AttendanceRecord.days_present,
            AttendanceRecord.total_instructional_days,
            AttendanceRecord.attendance_percentage,
        )
        .join(AttendanceRecord, AttendanceRecord.reporting_period_id == ReportingPeriod.id)
        .filter(
            AttendanceRecord.student_id == student.id,
            AttendanceRecord.record_date == None,  # noqa: E711
        )
        .order_by(asc(ReportingPeriod.sequence_order))
        .all()
    )
    attendance_by_period = [
        (row.name, row.days_present or 0.0, row.total_instructional_days or 0.0, row.attendance_percentage or 0.0)
        for row in att_periodic_rows
    ]

    # Daily attendance records (for ATT-CONSEC)
    daily_rows = (
        db.query(AttendanceRecord.record_date, AttendanceRecord.status)
        .filter(
            AttendanceRecord.student_id == student.id,
            AttendanceRecord.record_date != None,  # noqa: E711
            AttendanceRecord.status != None,  # noqa: E711
        )
        .order_by(asc(AttendanceRecord.record_date))
        .all()
    )
    daily_records = [(row.record_date, row.status) for row in daily_rows]

    # Assessment records
    assessment_rows = (
        db.query(
            AssessmentRecord.assessment_name,
            AssessmentRecord.subject,
            AssessmentRecord.assessment_date,
            AssessmentRecord.marks_obtained,
            AssessmentRecord.max_marks,
            AssessmentRecord.percentage,
        )
        .filter(AssessmentRecord.student_id == student.id)
        .order_by(asc(AssessmentRecord.assessment_date))
        .all()
    )
    assessments = [
        (row.assessment_name, row.subject, row.assessment_date,
         row.marks_obtained, row.max_marks, row.percentage)
        for row in assessment_rows
    ]

    # Assignment records (grouped by period)
    from backend.app.models.models import ReportingPeriod as RP
    asg_period_rows = (
        db.query(
            RP.name,
            RP.sequence_order,
            AssignmentRecord.status,
        )
        .join(AssignmentRecord, AssignmentRecord.reporting_period_id == RP.id)
        .filter(AssignmentRecord.student_id == student.id)
        .order_by(asc(RP.sequence_order))
        .all()
    )
    asg_by_period_dict: dict[tuple, list[str]] = {}
    for row in asg_period_rows:
        key = (row.sequence_order, row.name)
        asg_by_period_dict.setdefault(key, []).append(row.status)
    assignments_by_period = [
        (name, statuses)
        for (_, name), statuses in sorted(asg_by_period_dict.items())
    ]

    # --- Run rules ---
    checks = [
        check_att_low(attendance_by_period),
        check_att_decline(attendance_by_period),
        check_att_consec(daily_records),
        check_mark_low(assessments),
        check_mark_decline(assessments),
        check_asg_low(assignments_by_period),
        check_asg_decline(assignments_by_period),
    ]

    for result in checks:
        if result is not None:
            ind = _persist_indicator(db, student, result)
            if ind is not None:
                new_indicators.append(ind)

    if new_indicators:
        db.commit()

    return new_indicators


def run_engine_for_school(db: Session, school_id: int) -> dict[str, int]:
    """
    Run the engine for all active students in a school.
    Returns summary: {"students_checked": N, "new_indicators": M}
    """
    students = (
        db.query(Student)
        .filter(Student.school_id == school_id, Student.is_active == True)
        .all()
    )
    total_new = 0
    for student in students:
        new = run_engine_for_student(db, student)
        total_new += len(new)

    return {"students_checked": len(students), "new_indicators": total_new}

