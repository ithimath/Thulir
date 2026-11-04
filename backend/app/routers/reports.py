"""Router for Reports, Dashboard Aggregations, and Analytics (Phase 8)."""
import io
import csv
import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.middleware.auth_middleware import AuthenticatedUser, get_current_user
from backend.app.models.models import (
    Student,
    AttendanceRecord,
    AssessmentRecord,
    WarningIndicator,
    SupportCase,
    Intervention,
    FollowUp,
    ReportingPeriod,
    AcademicYear,
)

router = APIRouter(prefix="/api/reports", tags=["Reports & Analytics"])

# ---------------------------------------------------------------------------
# 1. OVERVIEW AGGREGATIONS (GET /api/reports/dashboard-stats)
# ---------------------------------------------------------------------------
@router.get("/dashboard-stats")
def get_dashboard_stats(
    auth: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    school_id = auth.school_id
    today = datetime.date.today()

    # Total enrolled cohort
    total_students = db.query(func.count(Student.id)).filter(
        Student.school_id == school_id,
        Student.is_active == True,
    ).scalar() or 0

    # Requiring review (Needs Review or Under Review)
    requiring_review = db.query(func.count(WarningIndicator.id)).filter(
        WarningIndicator.school_id == school_id,
        WarningIndicator.status.in_(["Needs Review", "Under Review"]),
    ).scalar() or 0

    high_priority_review = db.query(func.count(WarningIndicator.id)).filter(
        WarningIndicator.school_id == school_id,
        WarningIndicator.status.in_(["Needs Review", "Under Review"]),
        WarningIndicator.priority == "High",
    ).scalar() or 0

    # Active support cases
    active_cases = db.query(func.count(SupportCase.id)).filter(
        SupportCase.school_id == school_id,
        SupportCase.status.in_(["Open", "In Progress", "Under Observation"]),
    ).scalar() or 0

    # Overdue follow-ups
    overdue_follow_ups = db.query(func.count(FollowUp.id)).join(
        SupportCase, FollowUp.case_id == SupportCase.id
    ).filter(
        SupportCase.school_id == school_id,
        FollowUp.status == "Pending",
        FollowUp.due_date < today,
    ).scalar() or 0

    # Categories breakdown
    categories_raw = db.query(
        WarningIndicator.category,
        func.count(WarningIndicator.id),
    ).filter(
        WarningIndicator.school_id == school_id,
        WarningIndicator.status.notin_(["Closed", "Reviewed - No Action"]),
    ).group_by(WarningIndicator.category).all()

    categories_breakdown = {cat: count for cat, count in categories_raw}

    # Interventions breakdown
    interventions_raw = db.query(
        Intervention.intervention_type,
        func.count(Intervention.id),
    ).join(SupportCase, Intervention.case_id == SupportCase.id).filter(
        SupportCase.school_id == school_id,
    ).group_by(Intervention.intervention_type).all()

    interventions_breakdown = {itype: count for itype, count in interventions_raw}

    return {
        "total_enrolled": total_students,
        "requiring_review": requiring_review,
        "high_priority_review": high_priority_review,
        "active_cases": active_cases,
        "overdue_follow_ups": overdue_follow_ups,
        "indicators_by_category": categories_breakdown,
        "interventions_by_type": interventions_breakdown,
    }

# ---------------------------------------------------------------------------
# 2. TRAJECTORY & ANALYTICS (GET /api/reports/trajectory)
# ---------------------------------------------------------------------------
@router.get("/trajectory")
def get_trajectory_data(
    auth: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    school_id = auth.school_id

    # Periodic attendance averages
    periods = db.query(ReportingPeriod).join(
        AcademicYear, ReportingPeriod.academic_year_id == AcademicYear.id
    ).filter(
        AcademicYear.school_id == school_id
    ).order_by(ReportingPeriod.sequence_order).all()

    trajectory = []
    for p in periods:
        avg_att = db.query(func.avg(AttendanceRecord.attendance_percentage)).filter(
            AttendanceRecord.school_id == school_id,
            AttendanceRecord.reporting_period_id == p.id,
            AttendanceRecord.record_date == None, # aggregate
        ).scalar()

        avg_marks = db.query(func.avg(AssessmentRecord.percentage)).filter(
            AssessmentRecord.school_id == school_id,
            AssessmentRecord.reporting_period_id == p.id,
        ).scalar()

        trajectory.append({
            "period": p.name,
            "avg_attendance": round(float(avg_att), 1) if avg_att else None,
            "avg_assessment": round(float(avg_marks), 1) if avg_marks else None,
        })

    return {"trajectory": trajectory}

# ---------------------------------------------------------------------------
# 3. EXPORT CSV REPORT (GET /api/reports/export)
# ---------------------------------------------------------------------------
@router.get("/export")
def export_report_csv(
    report_type: str = Query("students_review", description="students_review | cases_summary"),
    auth: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    school_id = auth.school_id
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "students_review":
        writer.writerow(["EMIS_ID", "Student_Name", "Grade", "Section", "Rule_Code", "Priority", "Status", "Explanation"])
        indicators = db.query(WarningIndicator).filter(
            WarningIndicator.school_id == school_id,
        ).order_by(desc(WarningIndicator.detected_at)).all()

        for ind in indicators:
            s = ind.student
            cs = s.class_section if s else None
            grade = cs.grade if cs else ""
            sec = cs.section if cs else ""
            writer.writerow([
                s.emis_id if s else "",
                s.full_name if s else "",
                grade,
                sec,
                ind.rule_code,
                ind.priority,
                ind.status,
                ind.plain_explanation,
            ])
        filename = f"thulir_review_indicators_{datetime.date.today()}.csv"

    elif report_type == "cases_summary":
        writer.writerow(["Case_Number", "EMIS_ID", "Student_Name", "Category", "Status", "Priority", "Assigned_Staff", "Created_Date"])
        cases = db.query(SupportCase).filter(SupportCase.school_id == school_id).order_by(desc(SupportCase.created_at)).all()
        for c in cases:
            writer.writerow([
                c.case_number,
                c.student.emis_id if c.student else "",
                c.student.full_name if c.student else "",
                c.category,
                c.status,
                c.priority,
                c.assigned_staff.full_name if c.assigned_staff else "",
                str(c.created_at.date()),
            ])
        filename = f"thulir_support_cases_{datetime.date.today()}.csv"

    elif report_type == "interventions_log":
        writer.writerow(["Case_Number", "EMIS_ID", "Student_Name", "Intervention_Type", "Title", "Start_Date", "Target_Date", "Outcome", "Status"])
        interventions = db.query(Intervention).join(
            SupportCase, Intervention.case_id == SupportCase.id
        ).filter(SupportCase.school_id == school_id).order_by(desc(Intervention.created_at)).all()
        for i in interventions:
            sc = i.case
            writer.writerow([
                sc.case_number if sc else "",
                sc.student.emis_id if sc and sc.student else "",
                sc.student.full_name if sc and sc.student else "",
                i.intervention_type,
                i.title,
                str(i.start_date) if i.start_date else "",
                str(i.target_date) if i.target_date else "",
                i.outcome_notes or "",
                i.status,
            ])
        filename = f"thulir_interventions_log_{datetime.date.today()}.csv"

    elif report_type == "attendance_summary":
        writer.writerow(["EMIS_ID", "Student_Name", "Grade", "Section", "Total_Days", "Attended_Days", "Attendance_Pct", "Below_75_Flag"])
        attendances = db.query(AttendanceRecord).join(
            Student, AttendanceRecord.student_id == Student.id
        ).filter(Student.school_id == school_id).all()
        for a in attendances:
            s = a.student
            cs = s.class_section if s else None
            total_days = a.total_instructional_days or 0
            present_days = a.days_present or 0
            pct = a.attendance_percentage if a.attendance_percentage is not None else (
                (present_days / total_days * 100) if total_days > 0 else 0.0
            )
            writer.writerow([
                s.emis_id if s else "",
                s.full_name if s else "",
                cs.grade if cs else "",
                cs.section if cs else "",
                total_days,
                present_days,
                f"{pct:.1f}%",
                "YES" if pct < 75.0 else "NO",
            ])
        filename = f"thulir_attendance_summary_{datetime.date.today()}.csv"

    else:
        raise HTTPException(status_code=400, detail="Invalid report_type requested. Supported: students_review, cases_summary, interventions_log, attendance_summary.")

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

