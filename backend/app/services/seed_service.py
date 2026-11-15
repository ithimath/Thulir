import datetime
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.models.models import (
    School, User, UserSchoolRole, AcademicYear, ReportingPeriod, ClassSection,
    WarningRule, Student, AttendanceRecord, AssessmentRecord, WarningIndicator, SupportCase
)
from backend.app.services.security import hash_password

DEFAULT_WARNING_RULES = [
    {
        "rule_code": "ATT-LOW",
        "version": 1,
        "category": "attendance",
        "priority": "High",
        "threshold_value": 75.0,
        "required_records_count": 1,
        "description": "Attendance percentage in the latest period is strictly below 75% statutory floor (needs valid denominator).",
    },
    {
        "rule_code": "ATT-DECLINE",
        "version": 1,
        "category": "attendance",
        "priority": "Medium",
        "threshold_value": 10.0,
        "required_records_count": 2,
        "description": "Attendance percentage fell by 10.0 or more percentage points between consecutive reporting periods.",
    },
    {
        "rule_code": "ATT-CONSEC",
        "version": 1,
        "category": "attendance",
        "priority": "Medium",
        "threshold_value": 3.0,
        "required_records_count": 3,
        "description": "3 or more consecutive recorded unexcused absence days in dated daily registers.",
    },
    {
        "rule_code": "MARK-LOW",
        "version": 1,
        "category": "academic",
        "priority": "High",
        "threshold_value": 35.0,
        "required_records_count": 1,
        "description": "Latest assessment score is strictly below 35% of maximum marks in any subject.",
    },
    {
        "rule_code": "MARK-DECLINE",
        "version": 1,
        "category": "academic",
        "priority": "Medium",
        "threshold_value": 15.0,
        "required_records_count": 3,
        "description": "3 or more chronologically consecutive assessments, each lower than previous, with cumulative drop >= 15 points.",
    },
    {
        "rule_code": "ASG-LOW",
        "version": 1,
        "category": "assignment",
        "priority": "Medium",
        "threshold_value": 60.0,
        "required_records_count": 3,
        "description": "Assignment completion rate strictly below 60% over the latest period (needs at least 3 assignments).",
    },
    {
        "rule_code": "ASG-DECLINE",
        "version": 1,
        "category": "assignment",
        "priority": "Low",
        "threshold_value": 20.0,
        "required_records_count": 2,
        "description": "Assignment completion fell by 20.0 or more percentage points between consecutive periods.",
    },
]

def seed_warning_rules(db: Session):
    for r_data in DEFAULT_WARNING_RULES:
        existing = db.query(WarningRule).filter(
            WarningRule.rule_code == r_data["rule_code"],
            WarningRule.version == r_data["version"]
        ).first()
        if not existing:
            rule = WarningRule(**r_data)
            db.add(rule)
    db.commit()

def seed_demo_data(db: Session, force: bool = False):
    if settings.APP_ENV == "production" and not force:
        raise RuntimeError("Refusing to seed synthetic demo data in production environment!")

    seed_warning_rules(db)

    # 1. School
    school = db.query(School).filter(School.udise_code == "33280100412").first()
    if not school:
        school = School(
            udise_code="33280100412",
            name="Government Higher Secondary School Kovilpatti",
            district="Thoothukudi",
            block="Kovilpatti",
        )
        db.add(school)
        db.commit()
        db.refresh(school)

    # 2. Academic Year & Periods (2025-26)
    ay = db.query(AcademicYear).filter(AcademicYear.school_id == school.id, AcademicYear.is_current == True).first()
    if not ay:
        ay = AcademicYear(school_id=school.id, year_name="2025-26", is_current=True)
        db.add(ay)
        db.commit()
        db.refresh(ay)

    p1 = db.query(ReportingPeriod).filter(ReportingPeriod.academic_year_id == ay.id, ReportingPeriod.name == "Term I").first()
    if not p1:
        p1 = ReportingPeriod(
            academic_year_id=ay.id,
            name="Term I",
            sequence_order=1,
            start_date=datetime.date(2025, 6, 10),
            end_date=datetime.date(2025, 10, 15),
            is_current=False
        )
        db.add(p1)

    p2 = db.query(ReportingPeriod).filter(ReportingPeriod.academic_year_id == ay.id, ReportingPeriod.name == "Term II").first()
    if not p2:
        p2 = ReportingPeriod(
            academic_year_id=ay.id,
            name="Term II",
            sequence_order=2,
            start_date=datetime.date(2025, 10, 20),
            end_date=datetime.date(2026, 3, 31),
            is_current=True
        )
        db.add(p2)
    db.commit()

    # 3. Class Sections (e.g. 10-A, 10-B, 9-C, 8-D, 11-A, 12-A)
    classes_to_create = [
        (10, "A"), (10, "B"), (9, "C"), (8, "D"), (11, "A"), (12, "A"), (7, "A"), (6, "A")
    ]
    class_map = {}
    for grade, sec in classes_to_create:
        c = db.query(ClassSection).filter(
            ClassSection.school_id == school.id,
            ClassSection.academic_year_id == ay.id,
            ClassSection.grade == grade,
            ClassSection.section == sec
        ).first()
        if not c:
            c = ClassSection(school_id=school.id, academic_year_id=ay.id, grade=grade, section=sec)
            db.add(c)
            db.commit()
            db.refresh(c)
        class_map[f"{grade}-{sec}"] = c

    # 4. Users (Admin, Teacher, Counsellor)
    users_to_seed = [
        {
            "username": "admin",
            "password": "Password123!",
            "full_name": "R. Selvam (HM)",
            "designation": "Headmaster & Administrator",
            "role": "admin",
            "assigned_classes": None,
        },
        {
            "username": "teacher",
            "password": "Password123!",
            "full_name": "K. Revathi (PGT)",
            "designation": "Mathematics Teacher",
            "role": "teacher",
            "assigned_classes": "10-B,10-A",
        },
        {
            "username": "counsellor",
            "password": "Password123!",
            "full_name": "R. Meenakshi",
            "designation": "Head Counselor (M.S.W.)",
            "role": "counsellor",
            "assigned_classes": None,
        },
    ]

    user_map = {}
    for u_info in users_to_seed:
        user = db.query(User).filter(User.username == u_info["username"]).first()
        if not user:
            user = User(
                username=u_info["username"],
                hashed_password=hash_password(u_info["password"]),
                full_name=u_info["full_name"],
                designation=u_info["designation"],
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        role = db.query(UserSchoolRole).filter(
            UserSchoolRole.user_id == user.id,
            UserSchoolRole.school_id == school.id,
            UserSchoolRole.role == u_info["role"]
        ).first()
        if not role:
            role = UserSchoolRole(
                user_id=user.id,
                school_id=school.id,
                role=u_info["role"],
                assigned_classes=u_info["assigned_classes"],
            )
            db.add(role)
            db.commit()
        user_map[u_info["role"]] = user

    # 5. Seed 20 Synthetic Students (Matching the vertical slice and Stitch designs)
    sample_students_data = [
        {"emis": "3328014490", "name": "Kavitha M.", "grade": 10, "sec": "B", "gender": "Female", "guardian": "Mani K.", "phone": "9842100001"},
        {"emis": "3328011284", "name": "Vignesh S.", "grade": 9, "sec": "C", "gender": "Male", "guardian": "Subramanian P.", "phone": "9842100002"},
        {"emis": "3328019022", "name": "Priya D.", "grade": 11, "sec": "A", "gender": "Female", "guardian": "Dharmaraj R.", "phone": "9842100003"},
        {"emis": "3328017833", "name": "Sneha R.", "grade": 8, "sec": "D", "gender": "Female", "guardian": "Ramasamy S.", "phone": "9842100004"},
        {"emis": "3328015511", "name": "Anand K.", "grade": 10, "sec": "B", "gender": "Male", "guardian": "Kannan M.", "phone": "9842100005"},
        {"emis": "3328015512", "name": "Bavani T.", "grade": 10, "sec": "A", "gender": "Female", "guardian": "Thangaraj C.", "phone": "9842100006"},
        {"emis": "3328015513", "name": "Chandran G.", "grade": 10, "sec": "B", "gender": "Male", "guardian": "Ganesan P.", "phone": "9842100007"},
        {"emis": "3328015514", "name": "Deepa V.", "grade": 10, "sec": "A", "gender": "Female", "guardian": "Velu A.", "phone": "9842100008"},
        {"emis": "3328015515", "name": "Elango N.", "grade": 10, "sec": "B", "gender": "Male", "guardian": "Natarajan S.", "phone": "9842100009"},
        {"emis": "3328015516", "name": "Farhana A.", "grade": 10, "sec": "A", "gender": "Female", "guardian": "Abdul K.", "phone": "9842100010"},
        {"emis": "3328015517", "name": "Gopinath R.", "grade": 9, "sec": "C", "gender": "Male", "guardian": "Ravi K.", "phone": "9842100011"},
        {"emis": "3328015518", "name": "Harini S.", "grade": 9, "sec": "C", "gender": "Female", "guardian": "Sundaram M.", "phone": "9842100012"},
        {"emis": "3328015519", "name": "Ilavenil T.", "grade": 8, "sec": "D", "gender": "Female", "guardian": "Thirunavukkarasu", "phone": "9842100013"},
        {"emis": "3328015520", "name": "Jeeva P.", "grade": 8, "sec": "D", "gender": "Male", "guardian": "Perumal M.", "phone": "9842100014"},
        {"emis": "3328015521", "name": "Karthik B.", "grade": 12, "sec": "A", "gender": "Male", "guardian": "Balan S.", "phone": "9842100015"},
        {"emis": "3328015522", "name": "Lavanya S.", "grade": 12, "sec": "A", "gender": "Female", "guardian": "Senthil K.", "phone": "9842100016"},
        {"emis": "3328015523", "name": "Muthu M.", "grade": 7, "sec": "A", "gender": "Male", "guardian": "Muthusamy V.", "phone": "9842100017"},
        {"emis": "3328015524", "name": "Nandhini R.", "grade": 7, "sec": "A", "gender": "Female", "guardian": "Rengasamy P.", "phone": "9842100018"},
        {"emis": "3328015525", "name": "Praveen C.", "grade": 6, "sec": "A", "gender": "Male", "guardian": "Chandran S.", "phone": "9842100019"},
        {"emis": "3328015526", "name": "Raghavi K.", "grade": 6, "sec": "A", "gender": "Female", "guardian": "Kumar S.", "phone": "9842100020"},
    ]

    student_records = []
    for s_info in sample_students_data:
        st = db.query(Student).filter(Student.school_id == school.id, Student.emis_id == s_info["emis"]).first()
        cs = class_map.get(f"{s_info['grade']}-{s_info['sec']}")
        if not st:
            st = Student(
                school_id=school.id,
                emis_id=s_info["emis"],
                full_name=s_info["name"],
                gender=s_info["gender"],
                current_class_section_id=cs.id if cs else None,
                guardian_name=s_info["guardian"],
                guardian_phone=s_info["phone"],
                is_active=True,
            )
            db.add(st)
            db.commit()
            db.refresh(st)
        student_records.append(st)

    # 6. Seed Realistic Records for Key Students
    # Kavitha M (EMIS: 3328014490): ATT drop from 91% in Term I to 71% in Term II + Mark drop to 24% in CAT Math
    kavitha = db.query(Student).filter(Student.school_id == school.id, Student.emis_id == "3328014490").first()
    if kavitha:
        # Attendance Term I: 91 / 100 days (91%)
        att1 = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == kavitha.id,
            AttendanceRecord.reporting_period_id == p1.id
        ).first()
        if not att1:
            db.add(AttendanceRecord(
                student_id=kavitha.id,
                school_id=school.id,
                reporting_period_id=p1.id,
                days_present=91.0,
                total_instructional_days=100.0,
                attendance_percentage=91.0,
            ))
        # Attendance Term II: 54 / 76 days (71.05%) -> Triggers ATT-LOW & ATT-DECLINE
        att2 = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == kavitha.id,
            AttendanceRecord.reporting_period_id == p2.id
        ).first()
        if not att2:
            db.add(AttendanceRecord(
                student_id=kavitha.id,
                school_id=school.id,
                reporting_period_id=p2.id,
                days_present=54.0,
                total_instructional_days=76.0,
                attendance_percentage=71.05,
            ))
        # Assessment records
        # CAT 1 Math: 78 / 100 (78%)
        # CAT 2 Math: 56 / 100 (56%)
        # CAT 3 Math: 24 / 100 (24%) -> Triggers MARK-LOW and MARK-DECLINE
        marks_data = [
            ("CAT 1", "Mathematics", datetime.date(2024, 8, 14), 78.0, 100.0, 78.0, p1.id),
            ("CAT 2", "Mathematics", datetime.date(2024, 11, 20), 56.0, 100.0, 56.0, p2.id),
            ("CAT 3", "Mathematics", datetime.date(2025, 1, 18), 24.0, 100.0, 24.0, p2.id),
        ]
        for name, subj, dt, obt, mx, pct, pid in marks_data:
            existing_m = db.query(AssessmentRecord).filter(
                AssessmentRecord.student_id == kavitha.id,
                AssessmentRecord.assessment_name == name,
                AssessmentRecord.subject == subj,
            ).first()
            if not existing_m:
                db.add(AssessmentRecord(
                    student_id=kavitha.id,
                    school_id=school.id,
                    reporting_period_id=pid,
                    assessment_name=name,
                    subject=subj,
                    assessment_date=dt,
                    marks_obtained=obt,
                    max_marks=mx,
                    percentage=pct,
                ))

    # Vignesh S (EMIS: 3328011284): Consecutive absences (5 days)
    vignesh = db.query(Student).filter(Student.school_id == school.id, Student.emis_id == "3328011284").first()
    if vignesh:
        for day_offset in range(5):
            d = datetime.date(2025, 2, 10) + datetime.timedelta(days=day_offset)
            ex_daily = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == vignesh.id,
                AttendanceRecord.record_date == d
            ).first()
            if not ex_daily:
                db.add(AttendanceRecord(
                    student_id=vignesh.id,
                    school_id=school.id,
                    record_date=d,
                    status="absent",
                    days_present=0.0,
                    total_instructional_days=1.0,
                    attendance_percentage=0.0,
                ))

    db.commit()
    print("Seed complete: School, Users, Classes, Warning Rules, and 20 Synthetic Students created.")

