"""Idempotent Mock Data Seeder for THULIR.

Generates mock operational data for what the cleaned reference datasets do not contain:
1. Daily & periodic attendance matching dataset absences and absence bands.
2. Extra assessments for LMS engagement students consistent with performance_class.
3. Assignment records & submissions correlated with performance class.
4. Operational users (admin, teachers, counsellors) with documented credentials.
5. Sample support cases, interventions, follow-ups, and student support requests.
6. Execution of deterministic warning engine to generate indicators.

All mock rows are tagged with data_origin='mock' and source_ref='mock:...'.
Supports --reset-mock to purge only mock data without touching dataset or user records.
Reproducible with fixed SEED=42.
"""

import os
import sys
import random
import datetime
import argparse
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func

# Ensure backend root is on path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.database import SessionLocal, engine
from backend.app.models.models import (
    School,
    AcademicYear,
    ReportingPeriod,
    ClassSection,
    User,
    UserSchoolRole,
    Student,
    StudentProfile,
    StudentEngagementMetric,
    AttendanceRecord,
    AssessmentRecord,
    AssignmentRecord,
    WarningRule,
    WarningIndicator,
    SupportCase,
    Intervention,
    FollowUp,
    CaseNote,
    StudentSupportRequest,
    RefStudentPerformance,
    RefLmsEngagement,
)
from backend.app.services.security import hash_password
from backend.app.services.warning_engine import run_engine_for_school

TN_HOLIDAYS_2024_2025 = {
    datetime.date(2024, 6, 17),  # Bakrid
    datetime.date(2024, 7, 17),  # Muharram
    datetime.date(2024, 8, 15),  # Independence Day
    datetime.date(2024, 8, 26),  # Krishna Jayanthi
    datetime.date(2024, 9, 7),   # Vinayakar Chaturthi
    datetime.date(2024, 9, 16),  # Milad-un-Nabi
    datetime.date(2024, 10, 2),  # Gandhi Jayanti
    datetime.date(2024, 10, 11), # Ayudha Puja
    datetime.date(2024, 10, 12), # Vijaya Dasami
    datetime.date(2024, 10, 31), # Diwali
    datetime.date(2024, 12, 25), # Christmas
    datetime.date(2025, 1, 14),  # Pongal
    datetime.date(2025, 1, 15),  # Thiruvalluvar Day
    datetime.date(2025, 1, 16),  # Uzhavar Thirunal
    datetime.date(2025, 1, 26),  # Republic Day
}


def get_working_days(start_date: datetime.date, end_date: datetime.date) -> list[datetime.date]:
    """Return all working days between start and end (excluding weekends & TN holidays)."""
    cur = start_date
    working_days = []
    while cur <= end_date:
        if cur.weekday() < 5 and cur not in TN_HOLIDAYS_2024_2025:
            working_days.append(cur)
        cur += datetime.timedelta(days=1)
    return working_days


def reset_mock_data(db: Session):
    """Deletes ONLY rows with data_origin == 'mock'. Preserves all 'dataset' and 'user' rows."""
    print("--- Purging existing mock records (data_origin == 'mock') ---")

    # Order of deletion respecting foreign keys
    deleted_counts = {}

    # 1. Workflow children
    d_fn = db.query(CaseNote).filter(CaseNote.case_id.in_(
        db.query(SupportCase.id).filter(SupportCase.data_origin == "mock")
    )).delete(synchronize_session=False)

    d_fu = db.query(FollowUp).filter(FollowUp.case_id.in_(
        db.query(SupportCase.id).filter(SupportCase.data_origin == "mock")
    )).delete(synchronize_session=False)

    d_inv = db.query(Intervention).filter(Intervention.data_origin == "mock").delete(synchronize_session=False)
    deleted_counts["interventions"] = d_inv

    # 2. Support requests
    d_ssr = db.query(StudentSupportRequest).filter(StudentSupportRequest.data_origin == "mock").delete(synchronize_session=False)
    deleted_counts["support_requests"] = d_ssr

    # 3. Support cases
    d_sc = db.query(SupportCase).filter(SupportCase.data_origin == "mock").delete(synchronize_session=False)
    deleted_counts["support_cases"] = d_sc

    # 4. Warning indicators (only mock origin)
    d_wi = db.query(WarningIndicator).filter(WarningIndicator.data_origin == "mock").delete(synchronize_session=False)
    deleted_counts["warning_indicators"] = d_wi

    # 5. Assignments
    d_asg = db.query(AssignmentRecord).filter(AssignmentRecord.data_origin == "mock").delete(synchronize_session=False)
    deleted_counts["assignments"] = d_asg

    # 6. Assessments
    d_asm = db.query(AssessmentRecord).filter(AssessmentRecord.data_origin == "mock").delete(synchronize_session=False)
    deleted_counts["assessments"] = d_asm

    # 7. Attendance
    d_att = db.query(AttendanceRecord).filter(AttendanceRecord.data_origin == "mock").delete(synchronize_session=False)
    deleted_counts["attendance"] = d_att

    # 8. Mock users (if any)
    mock_user_ids = [u.id for u in db.query(User).filter(User.data_origin == "mock").all()]
    if mock_user_ids:
        db.query(UserSchoolRole).filter(UserSchoolRole.user_id.in_(mock_user_ids)).delete(synchronize_session=False)
        d_usr = db.query(User).filter(User.data_origin == "mock").delete(synchronize_session=False)
        deleted_counts["users"] = d_usr

    db.commit()
    for k, v in deleted_counts.items():
        if v > 0:
            print(f"  Deleted {v} mock {k}")
    print("Mock reset complete.")


def seed_users(db: Session, school: School) -> dict[str, User]:
    """Ensure standard staff accounts exist with documented dev credentials."""
    print("--- Seeding Staff Users ---")
    users_data = [
        {
            "username": "admin",
            "full_name": "R. Selvam (HM)",
            "designation": "Headmaster & Administrator",
            "role": "admin",
            "assigned_classes": None,
        },
        {
            "username": "teacher",
            "full_name": "K. Revathi (PGT)",
            "designation": "Mathematics Teacher",
            "role": "teacher",
            "assigned_classes": "10-A,10-B",
        },
        {
            "username": "teacher2",
            "full_name": "M. Senthil Kumar",
            "designation": "Physics Teacher",
            "role": "teacher",
            "assigned_classes": "11-A,11-B",
        },
        {
            "username": "teacher3",
            "full_name": "S. Malarvizhi",
            "designation": "Chemistry Teacher",
            "role": "teacher",
            "assigned_classes": "12-A,12-B",
        },
        {
            "username": "teacher4",
            "full_name": "A. Anbarasan",
            "designation": "Middle School Science Teacher",
            "role": "teacher",
            "assigned_classes": "7-A,8-A,9-A",
        },
        {
            "username": "counsellor",
            "full_name": "R. Meenakshi",
            "designation": "Head Counselor (M.S.W.)",
            "role": "counsellor",
            "assigned_classes": None,
        },
        {
            "username": "counsellor2",
            "full_name": "K. Balaji",
            "designation": "Student Wellbeing Officer",
            "role": "counsellor",
            "assigned_classes": None,
        },
    ]

    dev_password_hash = hash_password("Password123!")
    user_map = {}

    for u_info in users_data:
        user = db.query(User).filter(User.username == u_info["username"]).first()
        if not user:
            user = User(
                username=u_info["username"],
                hashed_password=dev_password_hash,
                full_name=u_info["full_name"],
                designation=u_info["designation"],
                is_active=True,
                data_origin="mock",
                source_ref=f"mock:user:{u_info['username']}",
            )
            db.add(user)
            db.flush()

        role = db.query(UserSchoolRole).filter(
            UserSchoolRole.user_id == user.id,
            UserSchoolRole.school_id == school.id,
            UserSchoolRole.role == u_info["role"],
        ).first()
        if not role:
            role = UserSchoolRole(
                user_id=user.id,
                school_id=school.id,
                role=u_info["role"],
                assigned_classes=u_info["assigned_classes"],
            )
            db.add(role)
            db.flush()

        user_map[u_info["username"]] = user

    db.commit()
    print(f"Ensured {len(user_map)} staff users in school.")
    return user_map


def seed_mock_attendance(
    db: Session,
    school: School,
    academic_year: AcademicYear,
    periods: dict[int, ReportingPeriod],
    students: list[Student],
):
    """
    Generate daily and periodic attendance consistent with dataset constraints.
    - Matches student_performance.absences
    - Matches engagement_lms.absence_band (<=7 / >7)
    - Engineers runs of >=3 consecutive absences (triggers ATT-CONSEC)
    - Engineers attendance drops >=10pp (triggers ATT-DECLINE and ATT-LOW)
    """
    print(f"--- Generating Attendance for {len(students)} students ---")

    # Working days per term
    term1_days = get_working_days(periods[1].start_date, periods[1].end_date)
    term2_days = get_working_days(periods[2].start_date, periods[2].end_date)
    term3_days = get_working_days(periods[3].start_date, periods[3].end_date)

    t1_count = len(term1_days)
    t2_count = len(term2_days)
    t3_count = len(term3_days)

    total_days = t1_count + t2_count + t3_count
    print(f"Instructional working days: Term 1 = {t1_count}, Term 2 = {t2_count}, Term 3 = {t3_count} (Total: {total_days})")

    # Cache profile / engagement data for fast lookup
    profile_map = {p.student_id: p for p in db.query(StudentProfile).all()}
    eng_map = {e.student_id: e for e in db.query(StudentEngagementMetric).all()}

    periodic_records = []
    daily_records = []

    # Keep track of students selected for consecutive absence registers
    # (recent 25 working days from Term 2)
    recent_term2_days = term2_days[-25:]

    for idx, student in enumerate(students):
        # 1. Determine target absences from real dataset
        prof = profile_map.get(student.id)
        eng = eng_map.get(student.id)

        target_absences = 0
        if prof and prof.raw_profile_data and "absences" in prof.raw_profile_data:
            target_absences = int(prof.raw_profile_data.get("absences", 0))
        elif eng:
            if eng.absence_band == "<=7 days":
                target_absences = random.randint(1, 6)
            else:
                target_absences = random.randint(8, 22)
        else:
            target_absences = random.randint(2, 10)

        # Cap absences to avoid impossible values
        target_absences = min(target_absences, total_days - 10)

        # 2. Partition absences between Term 1, Term 2
        # Signal engineering for rules:
        # Rule ATT-CONSEC: ~12% of students get a run of 3 to 5 consecutive absent days
        has_consec = (idx % 8 == 0) and (target_absences >= 3)

        # Rule ATT-DECLINE & ATT-LOW: ~15% of students have high attendance in Term 1 and sharp drop in Term 2
        has_decline = (idx % 7 == 0) and (target_absences >= 6)

        if has_decline:
            # Term 1: very high attendance (1 or 2 absences -> >97%)
            t1_abs = min(2, target_absences)
            # Term 2: heavy absences (15 to 22 absences -> <72% attendance, drop >= 20pp)
            t2_abs = max(15, min(target_absences - t1_abs, int(t2_count * 0.40)))
        else:
            # Proportionally distributed
            t1_abs = min(int(target_absences * 0.6), t1_count - 2)
            t2_abs = min(max(0, target_absences - t1_abs), t2_count - 2)

        # Bound checks
        t1_abs = min(t1_abs, t1_count - 1)
        t2_abs = min(t2_abs, t2_count - 1)

        # 3. Create Periodic Attendance Records for Term 1 and Term 2
        # (Term 3 is upcoming / in progress, so Term 2 is the latest evaluated period)
        # Term 1
        p1_present = float(t1_count - t1_abs)
        p1_pct = round((p1_present / t1_count) * 100.0, 1)
        periodic_records.append(AttendanceRecord(
            student_id=student.id,
            school_id=school.id,
            reporting_period_id=periods[1].id,
            record_date=None,
            status=None,
            days_present=p1_present,
            total_instructional_days=float(t1_count),
            attendance_percentage=p1_pct,
            data_origin="mock",
            source_ref=f"mock:attendance_periodic:p1:{student.id}",
        ))

        # Term 2
        p2_present = float(t2_count - t2_abs)
        p2_pct = round((p2_present / t2_count) * 100.0, 1)
        periodic_records.append(AttendanceRecord(
            student_id=student.id,
            school_id=school.id,
            reporting_period_id=periods[2].id,
            record_date=None,
            status=None,
            days_present=p2_present,
            total_instructional_days=float(t2_count),
            attendance_percentage=p2_pct,
            data_origin="mock",
            source_ref=f"mock:attendance_periodic:p2:{student.id}",
        ))

        # 4. Generate daily records for consecutive absence verification (ATT-CONSEC)
        if has_consec and len(recent_term2_days) >= 5:
            # Pick a consecutive run of 3 to 5 days in recent Term 2
            run_len = min(random.randint(3, 5), t2_abs)
            start_offset = random.randint(0, len(recent_term2_days) - run_len - 1)
            consec_days = set(recent_term2_days[start_offset:start_offset + run_len])

            for d in recent_term2_days:
                status = "absent" if d in consec_days else "present"
                daily_records.append(AttendanceRecord(
                    student_id=student.id,
                    school_id=school.id,
                    reporting_period_id=periods[2].id,
                    record_date=d,
                    status=status,
                    days_present=1.0 if status == "present" else 0.0,
                    total_instructional_days=1.0,
                    attendance_percentage=100.0 if status == "present" else 0.0,
                    data_origin="mock",
                    source_ref=f"mock:attendance_daily:{student.id}:{d}",
                ))

    # Bulk insert
    db.bulk_save_objects(periodic_records)
    if daily_records:
        db.bulk_save_objects(daily_records)
    db.commit()
    print(f"-> Inserted {len(periodic_records)} periodic attendance records and {len(daily_records)} daily attendance records.")


def seed_mock_extra_assessments(
    db: Session,
    school: School,
    periods: dict[int, ReportingPeriod],
    students: list[Student],
):
    """
    Generate mock assessments for LMS engagement students who lack marks in dataset.
    Follows their performance_class:
    - Low: 20-34% (triggers MARK-LOW) or descending (triggers MARK-DECLINE)
    - Medium: 45-65%
    - High: 75-95%
    """
    print("--- Seeding Assessments for LMS Students lacking dataset marks ---")
    eng_students = [s for s in students if s.source_ref and s.source_ref.startswith("ref_lms_engagement:")]
    eng_map = {e.student_id: e for e in db.query(StudentEngagementMetric).all()}

    asm_records = []
    for idx, student in enumerate(eng_students):
        eng = eng_map.get(student.id)
        p_class = eng.performance_class if eng else "Medium"
        subj = "Mathematics" if idx % 2 == 0 else "Science"

        # Signal engineering for MARK-LOW and MARK-DECLINE
        if p_class == "Low":
            if idx % 3 == 0:
                # Descending assessments with >=15pp cumulative drop -> MARK-DECLINE
                m1 = 48.0
                m2 = 36.0
                m3 = 24.0  # Also <35 -> MARK-LOW
            else:
                m1 = round(random.uniform(22.0, 33.0), 1)
                m2 = round(random.uniform(20.0, 34.0), 1)
                m3 = round(random.uniform(20.0, 34.0), 1)
        elif p_class == "Medium":
            m1 = round(random.uniform(50.0, 68.0), 1)
            m2 = round(random.uniform(48.0, 66.0), 1)
            m3 = round(random.uniform(52.0, 70.0), 1)
        else:  # High
            m1 = round(random.uniform(78.0, 95.0), 1)
            m2 = round(random.uniform(76.0, 94.0), 1)
            m3 = round(random.uniform(80.0, 98.0), 1)

        dates_and_marks = [
            ("Term 1 Continuous Assessment", datetime.date(2024, 9, 18), periods[1].id, m1),
            ("Term 2 Continuous Assessment", datetime.date(2024, 12, 10), periods[2].id, m2),
            ("Term 3 Final Assessment", datetime.date(2025, 3, 18), periods[3].id, m3),
        ]

        for a_name, a_date, p_id, marks in dates_and_marks:
            asm_records.append(AssessmentRecord(
                student_id=student.id,
                school_id=school.id,
                reporting_period_id=p_id,
                assessment_name=a_name,
                subject=subj,
                assessment_date=a_date,
                marks_obtained=marks,
                max_marks=100.0,
                percentage=marks,
                data_origin="mock",
                source_ref=f"mock:assessment:lms:{student.id}:{a_name}",
            ))

    db.bulk_save_objects(asm_records)
    db.commit()
    print(f"-> Inserted {len(asm_records)} assessment records for LMS students.")


def seed_mock_assignments(
    db: Session,
    school: School,
    periods: dict[int, ReportingPeriod],
    students: list[Student],
):
    """
    Generate assignments & submissions correlated with performance class / passed status.
    - Low performance: completion ~40-65% (some trigger ASG-LOW < 60%)
    - Some students show a >=20pp drop between periods (triggers ASG-DECLINE)
    - High performance: completion ~85-100%
    """
    print(f"--- Generating Assignments for {len(students)} students ---")

    profile_map = {p.student_id: p for p in db.query(StudentProfile).all()}
    eng_map = {e.student_id: e for e in db.query(StudentEngagementMetric).all()}

    subjects = ["Mathematics", "Science", "English", "Social Science"]
    t1_dates = [
        datetime.date(2024, 7, 5),
        datetime.date(2024, 8, 2),
        datetime.date(2024, 8, 30),
        datetime.date(2024, 9, 20),
    ]
    t2_dates = [
        datetime.date(2024, 10, 25),
        datetime.date(2024, 11, 15),
        datetime.date(2024, 11, 29),
        datetime.date(2024, 12, 13),
    ]

    assignments_to_insert = []

    for idx, student in enumerate(students):
        prof = profile_map.get(student.id)
        eng = eng_map.get(student.id)

        is_low = False
        if prof and prof.raw_profile_data:
            is_low = prof.raw_profile_data.get("passed", 1) == 0
        elif eng:
            is_low = eng.performance_class == "Low"
        else:
            is_low = (idx % 6 == 0)

        # Engineering rules:
        # ASG-DECLINE: high completion in Term 1 (100%), drop to 25-50% in Term 2
        triggers_decline = (idx % 9 == 0)
        # ASG-LOW: completion < 60% in Term 2 (e.g. 1 or 2 submitted out of 4)
        triggers_low = is_low or (idx % 7 == 0)

        # Term 1: 4 assignments
        for a_idx, a_date in enumerate(t1_dates):
            subj = subjects[a_idx % len(subjects)]
            if triggers_decline:
                status = "submitted"
            elif is_low:
                status = "submitted" if random.random() < 0.65 else "missing"
            else:
                status = "submitted" if random.random() < 0.92 else "missing"

            assignments_to_insert.append(AssignmentRecord(
                student_id=student.id,
                school_id=school.id,
                reporting_period_id=periods[1].id,
                subject=subj,
                assignment_date=a_date,
                status=status,
                score=80.0 if status == "submitted" else 0.0,
                data_origin="mock",
                source_ref=f"mock:asg:{student.id}:t1:{a_idx}",
            ))

        # Term 2: 4 assignments
        for a_idx, a_date in enumerate(t2_dates):
            subj = subjects[a_idx % len(subjects)]
            if triggers_decline:
                # 1 submitted out of 4 -> 25% (drop is 100 - 25 = 75pp >= 20pp)
                status = "submitted" if a_idx == 0 else "missing"
            elif triggers_low:
                # 1 or 2 submitted out of 4 -> 25% to 50% (< 60%)
                status = "submitted" if a_idx < 2 else "missing"
            else:
                status = "submitted" if random.random() < 0.90 else "missing"

            assignments_to_insert.append(AssignmentRecord(
                student_id=student.id,
                school_id=school.id,
                reporting_period_id=periods[2].id,
                subject=subj,
                assignment_date=a_date,
                status=status,
                score=75.0 if status == "submitted" else 0.0,
                data_origin="mock",
                source_ref=f"mock:asg:{student.id}:t2:{a_idx}",
            ))

    db.bulk_save_objects(assignments_to_insert)
    db.commit()
    print(f"-> Inserted {len(assignments_to_insert)} assignment records.")


def seed_mock_workflow_records(
    db: Session,
    school: School,
    users: dict[str, User],
    students: list[Student],
):
    """
    Seed realistic sample support cases, interventions, follow-ups,
    and student support requests across statuses to ensure workflow screens are populated.
    """
    print("--- Seeding Workflow Cases, Interventions, and Support Requests ---")

    admin = users.get("admin")
    teacher = users.get("teacher")
    counsellor = users.get("counsellor")
    counsellor2 = users.get("counsellor2")

    cases_data = [
        {
            "category": "academic",
            "priority": "High",
            "status": "In Progress",
            "reason": "Cumulative score drop in Mathematics and low assignment completion.",
            "observations": "Student struggles with algebra foundations; expresses anxiety during tests.",
            "intervention": {
                "type": "remedial_support",
                "title": "Mathematics Peer Tutoring & Concept Clinic",
                "description": "Daily 30-min remedial practice on basic algebraic simplification and problem sets.",
                "status": "Active",
            },
        },
        {
            "category": "attendance",
            "priority": "High",
            "status": "Open",
            "reason": "Consecutive absences for 4 days following transport disruption.",
            "observations": "Bus route from rural hamlet cancelled; parent contacted via village head.",
            "intervention": {
                "type": "attendance_followup",
                "title": "Transport Subsidy & Cycle Scheme Liaison",
                "description": "Coordinate with District Education Office for free student bus pass endorsement.",
                "status": "Planned",
            },
        },
        {
            "category": "socio_welfare",
            "priority": "Medium",
            "status": "Under Observation",
            "reason": "Family financial hardship and lack of learning materials.",
            "observations": "Guardian is single earner; student needs textbooks and geometry instruments.",
            "intervention": {
                "type": "academic_guidance",
                "title": "Alumni Textbook Bank & Material Assistance",
                "description": "Provide complete set of Tamil Nadu SCERT textbooks and study aids.",
                "status": "Completed",
            },
        },
        {
            "category": "behavioral",
            "priority": "Medium",
            "status": "Resolved",
            "reason": "Classroom disengagement and peer isolation during group projects.",
            "observations": "Showed remarkable improvement after peer pairing and counsellor mentoring.",
            "intervention": {
                "type": "counsellor_referral",
                "title": "Weekly Social & Emotional Learning Mentoring",
                "description": "Four structured sessions on active listening, confidence building and teamwork.",
                "status": "Completed",
            },
        },
        {
            "category": "academic",
            "priority": "Medium",
            "status": "Closed",
            "reason": "Initial term assessment shortfall in Science.",
            "observations": "Completed all remedial modules; scored 68% in Term 2 assessment.",
            "intervention": {
                "type": "remedial_support",
                "title": "Science Lab Hands-on Practical Revision",
                "description": "After-school practical sessions covering physics and biology diagrams.",
                "status": "Completed",
            },
        },
    ]

    for c_idx, c_info in enumerate(cases_data):
        target_student = students[c_idx % len(students)]
        case_num = f"CAS-2024-{1000 + c_idx + 1}"

        # Create Support Case
        case = SupportCase(
            case_number=case_num,
            school_id=school.id,
            student_id=target_student.id,
            created_by_id=teacher.id if teacher else admin.id,
            assigned_staff_id=counsellor.id if counsellor else admin.id,
            category=c_info["category"],
            status=c_info["status"],
            priority=c_info["priority"],
            reason=c_info["reason"],
            observations=c_info["observations"],
            review_date=datetime.date(2025, 1, 15),
            data_origin="mock",
            source_ref=f"mock:case:{case_num}",
        )
        db.add(case)
        db.flush()

        # Create Intervention
        inv_data = c_info["intervention"]
        inv = Intervention(
            case_id=case.id,
            intervention_type=inv_data["type"],
            title=inv_data["title"],
            description=inv_data["description"],
            status=inv_data["status"],
            assigned_staff_id=counsellor.id if counsellor else admin.id,
            start_date=datetime.date(2024, 11, 1),
            target_date=datetime.date(2024, 12, 20),
            completion_date=datetime.date(2024, 12, 18) if inv_data["status"] == "Completed" else None,
            outcome_notes="Significant progress observed by subject teacher." if inv_data["status"] == "Completed" else None,
            data_origin="mock",
            source_ref=f"mock:intervention:{case.id}",
        )
        db.add(inv)
        db.flush()

        # Create Follow-up
        db.add(FollowUp(
            case_id=case.id,
            intervention_id=inv.id,
            assigned_staff_id=teacher.id if teacher else admin.id,
            due_date=datetime.date(2024, 12, 1),
            completion_date=datetime.date(2024, 11, 28) if inv_data["status"] == "Completed" else None,
            status="Completed" if inv_data["status"] == "Completed" else "Pending",
            notes="Followed up with student during weekly zero period.",
        ))

        # Create Case Note
        db.add(CaseNote(
            case_id=case.id,
            author_id=counsellor.id if counsellor else admin.id,
            note_text="Initial case review conducted with student and class teacher. Plan established.",
            is_sensitive=False,
        ))

        # Create Student Support Request
        db.add(StudentSupportRequest(
            tracking_number=f"REQ-2024-{2000 + c_idx + 1}",
            school_id=school.id,
            student_id=target_student.id,
            intake_staff_id=teacher.id if teacher else admin.id,
            assigned_staff_id=counsellor.id if counsellor else admin.id,
            case_id=case.id if c_idx % 2 == 0 else None,
            requester_type="teacher",
            support_domain=c_info["category"],
            urgency_level=c_info["priority"],
            status="Reviewed" if c_idx % 2 == 0 else "Pending",
            description=c_info["reason"],
            intake_notes="Identified during monthly class progress committee review.",
            data_origin="mock",
            source_ref=f"mock:request:{c_idx + 1}",
        ))

    db.commit()
    print(f"-> Seeded {len(cases_data)} sample support cases, interventions, and support requests.")


def main(args_list=None):
    parser = argparse.ArgumentParser(description="THULIR Mock Data Seeder")
    parser.add_argument("--reset-mock", action="store_true", help="Delete only mock records and exit")
    parser.add_argument("--seed", type=int, default=int(os.getenv("SEED", 42)), help="RNG seed (default 42)")
    args = parser.parse_args(args_list)

    # Fixed seed for reproducibility
    seed_value = args.seed
    random.seed(seed_value)
    print(f"=== THULIR Mock Data Seeder (SEED={seed_value}) ===")

    db = SessionLocal()
    try:
        # Check school
        school = db.query(School).filter(School.udise_code == "33280100412").first()
        if not school:
            print("Error: Operational school not found. Please run import_datasets.py first!")
            return

        # 1. Reset mock if requested
        if args.reset_mock:
            reset_mock_data(db)
            print("Mock reset finished.")
            return

        # Ensure warning rules exist
        from backend.app.services.seed_service import seed_warning_rules
        seed_warning_rules(db)

        # Always clean out old mock rows before reseeding with fixed seed to ensure exact idempotency
        reset_mock_data(db)

        # 2. Staff Users
        users = seed_users(db, school)

        # 3. Academic Year & Periods (Current operational period)
        ay = db.query(AcademicYear).filter(AcademicYear.school_id == school.id, AcademicYear.is_current == True).first()
        if not ay:
            ay = db.query(AcademicYear).filter(AcademicYear.school_id == school.id).order_by(AcademicYear.id.desc()).first()
        if not ay:
            print("Error: Current Academic Year not found. Please run import_datasets.py first!")
            return

        periods = {
            rp.sequence_order: rp
            for rp in db.query(ReportingPeriod).filter(ReportingPeriod.academic_year_id == ay.id).all()
        }

        # 4. Load operational dataset students
        students = db.query(Student).filter(
            Student.school_id == school.id,
            Student.data_origin == "dataset",
        ).order_by(Student.id).all()
        print(f"Found {len(students)} operational dataset students.")

        # 5. Generate Attendance
        seed_mock_attendance(db, school, ay, periods, students)

        # 6. Generate Extra Assessments for LMS students
        seed_mock_extra_assessments(db, school, periods, students)

        # 7. Generate Assignments
        seed_mock_assignments(db, school, periods, students)

        # 8. Generate Workflow records
        seed_mock_workflow_records(db, school, users, students)

        # 9. Execute Deterministic Warning Engine
        print("--- Executing Deterministic Early-Warning Engine ---")
        new_indicators = run_engine_for_school(db, school.id)
        db.commit()
        print(f"Warning engine completed: Generated {len(new_indicators)} indicators.")

        # Report indicator breakdown
        rule_counts = (
            db.query(WarningIndicator.rule_code, func.count(WarningIndicator.id))
            .filter(WarningIndicator.school_id == school.id)
            .group_by(WarningIndicator.rule_code)
            .all()
        )
        print("\n--- Warning Indicators Summary ---")
        for r_code, count in rule_counts:
            print(f"  {r_code:15}: {count} indicators")

        print("\nAll mock seeding steps completed successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    main()
