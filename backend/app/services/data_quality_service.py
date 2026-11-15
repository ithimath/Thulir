"""Data Quality Monitor Service (Feature 3).

Monitors data integrity, detects anomalies, and surfaces plain-language metrics:
- Missing attendance records
- Duplicate student IDs & EMIS
- Invalid marks and attendance values (out of bounds)
- Conflicting reporting periods
- Incomplete student profiles
- Invalid assignment records
- Import errors & rejected rows
Enforces: Plain counts and percentages only; never an invented composite score.
"""
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc

from backend.app.models.models import (
    Student,
    AttendanceRecord,
    AssessmentRecord,
    AssignmentRecord,
    ReportingPeriod,
    AcademicYear,
    ImportBatch,
    ImportRowResult,
    ClassSection,
    DataCorrection,
)
from backend.app.middleware.auth_middleware import AuthenticatedUser


def scan_data_quality(
    db: Session,
    school_id: int,
    auth: AuthenticatedUser,
    grade_filter: Optional[int] = None,
    section_filter: Optional[str] = None,
    period_id_filter: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute complete data quality scan for a school."""
    # 1. Base active students
    student_q = db.query(Student).filter(
        Student.school_id == school_id,
        Student.is_active == True,
    )
    if auth.role_name == "teacher":
        allowed = auth.assigned_classes_list
        if not allowed:
            student_q = student_q.filter(False)
        else:
            pairs = [p.split("-") for p in allowed if "-" in p]
            conds = [
                and_(ClassSection.grade == int(g), ClassSection.section == s)
                for g, s in pairs if g.isdigit()
            ]
            if conds:
                student_q = student_q.join(ClassSection, Student.current_class_section_id == ClassSection.id).filter(or_(*conds))
            else:
                student_q = student_q.filter(False)

    if grade_filter or section_filter:
        student_q = student_q.join(ClassSection, Student.current_class_section_id == ClassSection.id)
        if grade_filter:
            student_q = student_q.filter(ClassSection.grade == grade_filter)
        if section_filter:
            student_q = student_q.filter(ClassSection.section == section_filter)

    students = student_q.all()
    total_students = len(students)
    student_ids = [s.id for s in students]

    issues: List[Dict[str, Any]] = []

    # -------------------------------------------------------------
    # Check 1: Duplicate Student EMIS IDs or names
    # -------------------------------------------------------------
    emis_counts = db.query(Student.emis_id, func.count(Student.id))\
                    .filter(Student.school_id == school_id)\
                    .group_by(Student.emis_id)\
                    .having(func.count(Student.id) > 1)\
                    .all()

    dup_count = 0
    for emis, cnt in emis_counts:
        dup_students = db.query(Student).filter(Student.school_id == school_id, Student.emis_id == emis).all()
        for ds in dup_students:
            if not student_ids or ds.id in student_ids:
                dup_count += 1
                cs = ds.class_section
                issues.append({
                    "id": f"dup-emis-{ds.id}",
                    "category": "duplicate_students",
                    "severity": "high",
                    "title": f"Duplicate EMIS ID: {emis}",
                    "plain_explanation": f"Student '{ds.full_name}' shares EMIS ID {emis} with another record in this school.",
                    "student_id": ds.id,
                    "student_name": ds.full_name,
                    "emis_id": ds.emis_id,
                    "class_section": f"{cs.grade}-{cs.section}" if cs else None,
                    "record_type": "student",
                    "target_record_id": ds.id,
                    "can_correct": True,
                })

    # -------------------------------------------------------------
    # Check 2: Invalid Marks (marks > max_marks or marks < 0 or max_marks <= 0)
    # -------------------------------------------------------------
    asm_q = db.query(AssessmentRecord).filter(
        AssessmentRecord.school_id == school_id,
        AssessmentRecord.is_superseded == False,
    )
    if student_ids:
        asm_q = asm_q.filter(AssessmentRecord.student_id.in_(student_ids))
    if period_id_filter:
        asm_q = asm_q.filter(AssessmentRecord.reporting_period_id == period_id_filter)

    all_asms = asm_q.all()
    invalid_marks_count = 0
    for asm in all_asms:
        is_invalid = False
        reason = ""
        if asm.max_marks <= 0:
            is_invalid = True
            reason = f"Maximum marks must be strictly positive (found {asm.max_marks})."
        elif asm.marks_obtained < 0:
            is_invalid = True
            reason = f"Marks obtained cannot be negative (found {asm.marks_obtained})."
        elif asm.marks_obtained > asm.max_marks:
            is_invalid = True
            reason = f"Marks obtained ({asm.marks_obtained}) strictly exceed maximum marks ({asm.max_marks})."

        if is_invalid:
            invalid_marks_count += 1
            st = asm.student
            cs = st.class_section if st else None
            issues.append({
                "id": f"inv-mark-{asm.id}",
                "category": "invalid_marks",
                "severity": "high",
                "title": f"Invalid Assessment Marks in {asm.subject}",
                "plain_explanation": f"Assessment '{asm.assessment_name}' for {st.full_name if st else 'student'}: {reason}",
                "student_id": asm.student_id,
                "student_name": st.full_name if st else None,
                "emis_id": st.emis_id if st else None,
                "class_section": f"{cs.grade}-{cs.section}" if cs else None,
                "record_type": "assessment",
                "target_record_id": asm.id,
                "can_correct": True,
            })

    # -------------------------------------------------------------
    # Check 3: Invalid Attendance Values (att_pct > 100 or < 0 or days_present > total_days)
    # -------------------------------------------------------------
    att_q = db.query(AttendanceRecord).filter(
        AttendanceRecord.school_id == school_id,
        AttendanceRecord.is_superseded == False,
    )
    if student_ids:
        att_q = att_q.filter(AttendanceRecord.student_id.in_(student_ids))
    if period_id_filter:
        att_q = att_q.filter(AttendanceRecord.reporting_period_id == period_id_filter)

    all_atts = att_q.all()
    invalid_att_count = 0
    for att in all_atts:
        is_invalid = False
        reason = ""
        if att.attendance_percentage is not None:
            if att.attendance_percentage > 100.0 or att.attendance_percentage < 0.0:
                is_invalid = True
                reason = f"Attendance percentage ({att.attendance_percentage}%) is outside valid 0-100% range."
            elif att.total_instructional_days is not None and att.days_present is not None:
                if att.days_present > att.total_instructional_days:
                    is_invalid = True
                    reason = f"Days present ({att.days_present}) strictly exceeds total instructional days ({att.total_instructional_days})."
                elif att.total_instructional_days <= 0:
                    is_invalid = True
                    reason = f"Total instructional days must be positive (found {att.total_instructional_days})."

        if is_invalid:
            invalid_att_count += 1
            st = att.student
            cs = st.class_section if st else None
            issues.append({
                "id": f"inv-att-{att.id}",
                "category": "invalid_attendance",
                "severity": "high",
                "title": "Invalid Attendance Value",
                "plain_explanation": f"Attendance record for {st.full_name if st else 'student'}: {reason}",
                "student_id": att.student_id,
                "student_name": st.full_name if st else None,
                "emis_id": st.emis_id if st else None,
                "class_section": f"{cs.grade}-{cs.section}" if cs else None,
                "record_type": "attendance",
                "target_record_id": att.id,
                "can_correct": True,
            })

    # -------------------------------------------------------------
    # Check 4: Missing Attendance Records in Active Period
    # -------------------------------------------------------------
    active_period = db.query(ReportingPeriod).join(AcademicYear, ReportingPeriod.academic_year_id == AcademicYear.id)\
                      .filter(AcademicYear.school_id == school_id, ReportingPeriod.is_current == True)\
                      .first()

    missing_att_count = 0
    if active_period:
        students_with_att = db.query(AttendanceRecord.student_id)\
                              .filter(
                                  AttendanceRecord.school_id == school_id,
                                  AttendanceRecord.reporting_period_id == active_period.id,
                                  AttendanceRecord.is_superseded == False,
                              ).distinct().all()
        logged_ids = {r[0] for r in students_with_att}
        for st in students:
            if st.id not in logged_ids:
                missing_att_count += 1
                cs = st.class_section
                issues.append({
                    "id": f"miss-att-{st.id}",
                    "category": "missing_attendance",
                    "severity": "medium",
                    "title": f"Missing Attendance for {active_period.name}",
                    "plain_explanation": f"Student '{st.full_name}' has zero attendance entries recorded for current period '{active_period.name}'.",
                    "student_id": st.id,
                    "student_name": st.full_name,
                    "emis_id": st.emis_id,
                    "class_section": f"{cs.grade}-{cs.section}" if cs else None,
                    "record_type": "attendance",
                    "target_record_id": None,
                    "can_correct": False,
                })

    # -------------------------------------------------------------
    # Check 5: Incomplete Student Profiles
    # -------------------------------------------------------------
    incomplete_count = 0
    for st in students:
        missing_fields = []
        if not st.guardian_name or not st.guardian_name.strip():
            missing_fields.append("Guardian Name")
        if not st.guardian_phone or not st.guardian_phone.strip():
            missing_fields.append("Guardian Phone")
        if not st.current_class_section_id:
            missing_fields.append("Class/Section Assignment")

        if missing_fields:
            incomplete_count += 1
            cs = st.class_section
            issues.append({
                "id": f"inc-prof-{st.id}",
                "category": "incomplete_profiles",
                "severity": "medium",
                "title": "Incomplete Profile Information",
                "plain_explanation": f"Student '{st.full_name}' is missing required fields: {', '.join(missing_fields)}.",
                "student_id": st.id,
                "student_name": st.full_name,
                "emis_id": st.emis_id,
                "class_section": f"{cs.grade}-{cs.section}" if cs else None,
                "record_type": "student",
                "target_record_id": st.id,
                "can_correct": True,
            })

    # -------------------------------------------------------------
    # Check 6: Conflicting Reporting Periods
    # -------------------------------------------------------------
    periods = db.query(ReportingPeriod).join(AcademicYear, ReportingPeriod.academic_year_id == AcademicYear.id)\
                .filter(AcademicYear.school_id == school_id)\
                .order_by(ReportingPeriod.sequence_order)\
                .all()

    conflicting_periods_count = 0
    for i in range(len(periods)):
        for j in range(i + 1, len(periods)):
            p1, p2 = periods[i], periods[j]
            # Check overlap if both have start and end dates
            if p1.start_date and p1.end_date and p2.start_date and p2.end_date:
                if not (p1.end_date < p2.start_date or p2.end_date < p1.start_date):
                    conflicting_periods_count += 1
                    issues.append({
                        "id": f"conf-period-{p1.id}-{p2.id}",
                        "category": "conflicting_periods",
                        "severity": "high",
                        "title": f"Overlapping Periods: {p1.name} & {p2.name}",
                        "plain_explanation": f"Period '{p1.name}' ({p1.start_date} to {p1.end_date}) overlaps with '{p2.name}' ({p2.start_date} to {p2.end_date}).",
                        "student_id": None,
                        "student_name": None,
                        "emis_id": None,
                        "class_section": None,
                        "record_type": "reporting_period",
                        "target_record_id": p1.id,
                        "can_correct": False,
                    })

    # -------------------------------------------------------------
    # Check 7: Invalid Assignment Records
    # -------------------------------------------------------------
    asg_q = db.query(AssignmentRecord).filter(
        AssignmentRecord.school_id == school_id,
        AssignmentRecord.is_superseded == False,
    )
    if student_ids:
        asg_q = asg_q.filter(AssignmentRecord.student_id.in_(student_ids))
    if period_id_filter:
        asg_q = asg_q.filter(AssignmentRecord.reporting_period_id == period_id_filter)

    all_asgs = asg_q.all()
    invalid_asg_count = 0
    valid_statuses = {"submitted", "missing", "late"}
    for asg in all_asgs:
        if asg.status not in valid_statuses or (asg.score is not None and asg.score < 0):
            invalid_asg_count += 1
            st = asg.student
            cs = st.class_section if st else None
            issues.append({
                "id": f"inv-asg-{asg.id}",
                "category": "invalid_assignments",
                "severity": "medium",
                "title": f"Invalid Assignment Status/Score in {asg.subject}",
                "plain_explanation": f"Assignment record for {st.full_name if st else 'student'}: status '{asg.status}' is unrecognized.",
                "student_id": asg.student_id,
                "student_name": st.full_name if st else None,
                "emis_id": st.emis_id if st else None,
                "class_section": f"{cs.grade}-{cs.section}" if cs else None,
                "record_type": "assignment",
                "target_record_id": asg.id,
                "can_correct": True,
            })

    # -------------------------------------------------------------
    # Check 8: Import Errors and Rejected Rows (from ImportRowResult)
    # -------------------------------------------------------------
    import_rejected_count = (
        db.query(func.count(ImportRowResult.id))
        .join(ImportBatch, ImportRowResult.batch_id == ImportBatch.id)
        .filter(ImportBatch.school_id == school_id, ImportRowResult.category.in_(["rejected", "skipped_duplicate"]))
        .scalar() or 0
    )
    rejected_rows = (
        db.query(ImportRowResult)
        .join(ImportBatch, ImportRowResult.batch_id == ImportBatch.id)
        .filter(ImportBatch.school_id == school_id, ImportRowResult.category.in_(["rejected", "skipped_duplicate"]))
        .order_by(desc(ImportRowResult.created_at))
        .limit(50)
        .all()
    )

    import math
    for r in rejected_rows:
        batch = r.batch
        raw = r.raw_data or {}
        st_name = raw.get("full_name") or raw.get("name")
        if isinstance(st_name, float) and math.isnan(st_name):
            st_name = None

        emis = raw.get("emis_id")
        if isinstance(emis, float) and math.isnan(emis):
            emis_str = ""
        else:
            emis_str = str(emis or "")

        gr = raw.get("grade", "")
        sec = raw.get("section", "")
        if isinstance(gr, float) and math.isnan(gr):
            gr = ""
        if isinstance(sec, float) and math.isnan(sec):
            sec = ""

        issues.append({
            "id": f"imp-rej-{r.id}",
            "category": "import_rejected_rows",
            "severity": "medium",
            "title": f"Import File Error: Row {r.row_number}",
            "plain_explanation": f"Batch '{batch.file_name if batch else 'Upload'}': {r.message or 'Rejected due to validation error'}",
            "student_id": None,
            "student_name": st_name,
            "emis_id": emis_str,
            "class_section": f"{gr}-{sec}" if gr or sec else None,
            "record_type": "import_row",
            "target_record_id": r.id,
            "can_correct": False,
        })

    total_issues = (
        dup_count +
        invalid_marks_count +
        invalid_att_count +
        missing_att_count +
        incomplete_count +
        conflicting_periods_count +
        invalid_asg_count +
        import_rejected_count
    )

    # Plain counts and percentages
    complete_profiles_count = total_students - incomplete_count
    profile_pct = round((complete_profiles_count / total_students) * 100.0, 1) if total_students > 0 else 100.0

    students_with_valid_att = total_students - missing_att_count
    att_completeness_pct = round((students_with_valid_att / total_students) * 100.0, 1) if total_students > 0 else 100.0

    return {
        "summary": {
            "total_students": total_students,
            "total_issues_count": total_issues,
            "profile_completeness_pct": profile_pct,
            "complete_profiles_count": complete_profiles_count,
            "attendance_completeness_pct": att_completeness_pct,
            "students_with_valid_attendance_count": students_with_valid_att,
            "categories": {
                "duplicate_students": {
                    "count": dup_count,
                    "label": "Duplicate Student Identifiers",
                    "description": "Students sharing the same EMIS ID or name in the same section"
                },
                "invalid_marks": {
                    "count": invalid_marks_count,
                    "label": "Invalid Assessment Marks",
                    "description": "Scores exceeding maximum marks or negative values"
                },
                "invalid_attendance": {
                    "count": invalid_att_count,
                    "label": "Invalid Attendance Values",
                    "description": "Attendance percentage > 100% or days present > instructional days"
                },
                "missing_attendance": {
                    "count": missing_att_count,
                    "label": "Missing Attendance Records",
                    "description": "Students with zero attendance logs for the current term"
                },
                "incomplete_profiles": {
                    "count": incomplete_count,
                    "label": "Incomplete Student Profiles",
                    "description": "Students missing guardian contact or class section assignment"
                },
                "conflicting_periods": {
                    "count": conflicting_periods_count,
                    "label": "Conflicting Reporting Periods",
                    "description": "Academic periods with overlapping date ranges"
                },
                "invalid_assignments": {
                    "count": invalid_asg_count,
                    "label": "Invalid Assignment Records",
                    "description": "Assignment records with unrecognized status or corrupted scores"
                },
                "import_rejected_rows": {
                    "count": import_rejected_count,
                    "label": "Import Errors & Rejected Rows",
                    "description": "Data rows rejected during CSV/XLSX imports due to schema violations"
                },
            }
        },
        "issues": issues,
    }
