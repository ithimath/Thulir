"""Idempotent Dataset Importer for THULIR.

Imports the cleaned reference CSV datasets:
- student_performance.csv (1044 rows) -> ref_student_performance
- engagement_lms.csv (478 rows) -> ref_lms_engagement
- higher_ed_dropout.csv (4424 rows) -> ref_higher_ed_dropout

Maps student_performance and engagement_lms into THULIR operational tables
with data_origin='dataset' and source_ref='ref_...:id'.
"""

import sys
import os
import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session

# Ensure backend is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.database import SessionLocal, engine
from backend.app.models.models import (
    Base,
    School,
    AcademicYear,
    ReportingPeriod,
    ClassSection,
    Student,
    StudentProfile,
    StudentEngagementMetric,
    AssessmentRecord,
    RefStudentPerformance,
    RefLmsEngagement,
    RefHigherEdDropout,
)

CLEANED_DIR = BASE_DIR / "backend" / "data" / "cleaned"

# Realistic Tamil Nadu Names (English + Tamil script)
TN_MALE_FIRST = [
    ("Mugilan", "முகிலன்"), ("Vignesh", "விக்னேஷ்"), ("Karthik", "கார்த்திக்"),
    ("Dinesh", "தினேஷ்"), ("Saravanan", "சரவணன்"), ("Anbarasan", "அன்பரசன்"),
    ("Selvam", "செல்வம்"), ("Kavin", "கவின்"), ("Prakash", "பிரகாஷ்"),
    ("Madhavan", "மாதவன்"), ("Iniyan", "இனியன்"), ("Arivazhagan", "அறிவழகன்"),
    ("Vijay", "விஜய்"), ("Senthil", "செந்தில்"), ("Manikandan", "மணிகண்டன்"),
    ("Aravind", "அரவிந்த்"), ("Gokul", "கோகுல்"), ("Elango", "இளங்கோ"),
    ("Thangavel", "தங்கவேல்"), ("Balaji", "பாலாஜி"), ("Suresh", "சுரேஷ்"),
    ("Murugan", "முருகன்"), ("Kishore", "கிஷோர்"), ("Ganesh", "கணேஷ்"),
]

TN_FEMALE_FIRST = [
    ("Kavitha", "கவிதா"), ("Ananya", "அனன்யா"), ("Priya", "பிரியா"),
    ("Deepa", "தீபா"), ("Nithya", "நித்யா"), ("Meenakshi", "மீனாட்சி"),
    ("Kayalvizhi", "கயல்விழி"), ("Yazhini", "யாழினி"), ("Divya", "திவ்யா"),
    ("Malarvizhi", "மலர்விழி"), ("Pavithra", "பவித்ரா"), ("Abirami", "அபிராமி"),
    ("Keerthana", "கீர்த்தனா"), ("Subhasri", "சுபஸ்ரீ"), ("Thamizhselvi", "தமிழ்ச்செல்வி"),
    ("Lavanya", "லாவண்யா"), ("Poonguzhali", "பூங்குழலி"), ("Revathi", "ரேவதி"),
    ("Soundarya", "சௌந்தர்யா"), ("Uma", "உமா"), ("Geetha", "கீதா"),
    ("Shalini", "ஷாலினி"), ("Bhavani", "பவானி"), ("Janani", "ஜனனி"),
]

TN_INITIALS = [
    ("R", "ஆர்"), ("S", "எஸ்"), ("K", "கே"), ("M", "எம்"),
    ("P", "பி"), ("T", "டி"), ("V", "வி"), ("A", "ஏ"),
    ("N", "என்"), ("G", "ஜி"), ("C", "சி"), ("D", "டி")
]

TN_GUARDIAN_NAMES = [
    ("Ramesh K", "ரமேஷ் கே"), ("Selvi M", "செல்வி எம்"), ("Sundaram P", "சுந்தரம் பி"),
    ("Lakshmi T", "லட்சுமி டி"), ("Murugesan S", "முருகேசன் எஸ்"), ("Radha V", "ராதா வி"),
    ("Karuppasamy A", "கருப்பசாமி ஏ"), ("Kalaivani R", "கலைவாணி ஆர்"), ("Velu M", "வேலு எம்"),
    ("Parvathi K", "பார்வதி கே"), ("Madasamy N", "மாடசாமி என்"), ("Chitra G", "சித்ரா ஜி"),
]


def generate_tn_name(index: int, gender: str) -> str:
    initial_en, initial_ta = TN_INITIALS[index % len(TN_INITIALS)]
    if gender and str(gender).lower().startswith("f"):
        first_en, first_ta = TN_FEMALE_FIRST[index % len(TN_FEMALE_FIRST)]
    else:
        first_en, first_ta = TN_MALE_FIRST[index % len(TN_MALE_FIRST)]
    return f"{first_en} {initial_en} / {first_ta} {initial_ta}"


def generate_guardian_name(index: int) -> str:
    g_en, g_ta = TN_GUARDIAN_NAMES[index % len(TN_GUARDIAN_NAMES)]
    return f"{g_en} / {g_ta}"


def import_reference_datasets(db: Session):
    print("--- 1. Importing Reference Datasets ---")

    # 1. student_performance.csv (1044 rows)
    sp_file = CLEANED_DIR / "student_performance.csv"
    if not sp_file.exists():
        raise FileNotFoundError(f"Missing {sp_file}")
    df_sp = pd.read_csv(sp_file)
    print(f"Loaded {sp_file.name}: {len(df_sp)} rows")

    # Idempotent sync
    existing_sp_count = db.query(RefStudentPerformance).count()
    if existing_sp_count != len(df_sp):
        db.query(RefStudentPerformance).delete()
        db.flush()
        records_to_insert = []
        now = datetime.datetime.utcnow()
        for _, row in df_sp.iterrows():
            rec = RefStudentPerformance(
                record_id=int(row.get("record_id", _ + 1)),
                subject=str(row.get("subject", "Math")),
                school=str(row.get("school", "GP")),
                gender=str(row.get("gender", "Female")),
                age=int(row["age"]) if pd.notna(row.get("age")) else None,
                address=str(row.get("address", "Urban")),
                family_size=str(row.get("family_size", ">3")),
                parents_status=str(row.get("parents_status", "Together")),
                mother_edu=int(row["mother_edu"]) if pd.notna(row.get("mother_edu")) else None,
                father_edu=int(row["father_edu"]) if pd.notna(row.get("father_edu")) else None,
                mother_job=str(row.get("mother_job", "other")),
                father_job=str(row.get("father_job", "other")),
                reason=str(row.get("reason", "course")),
                guardian=str(row.get("guardian", "mother")),
                travel_time=int(row["travel_time"]) if pd.notna(row.get("travel_time")) else None,
                study_time=int(row["study_time"]) if pd.notna(row.get("study_time")) else None,
                failures=int(row["failures"]) if pd.notna(row.get("failures")) else None,
                school_support=int(row["school_support"]) if pd.notna(row.get("school_support")) else None,
                family_support=int(row["family_support"]) if pd.notna(row.get("family_support")) else None,
                paid_classes=int(row["paid_classes"]) if pd.notna(row.get("paid_classes")) else None,
                activities=int(row["activities"]) if pd.notna(row.get("activities")) else None,
                nursery=int(row["nursery"]) if pd.notna(row.get("nursery")) else None,
                wants_higher_edu=int(row["wants_higher_edu"]) if pd.notna(row.get("wants_higher_edu")) else None,
                internet=int(row["internet"]) if pd.notna(row.get("internet")) else None,
                romantic=int(row["romantic"]) if pd.notna(row.get("romantic")) else None,
                family_relationship=int(row["family_relationship"]) if pd.notna(row.get("family_relationship")) else None,
                free_time=int(row["free_time"]) if pd.notna(row.get("free_time")) else None,
                go_out=int(row["go_out"]) if pd.notna(row.get("go_out")) else None,
                workday_alcohol=int(row["workday_alcohol"]) if pd.notna(row.get("workday_alcohol")) else None,
                weekend_alcohol=int(row["weekend_alcohol"]) if pd.notna(row.get("weekend_alcohol")) else None,
                health=int(row["health"]) if pd.notna(row.get("health")) else None,
                absences=int(row["absences"]) if pd.notna(row.get("absences")) else 0,
                grade_p1=float(row["grade_p1"]) if pd.notna(row.get("grade_p1")) else None,
                grade_p2=float(row["grade_p2"]) if pd.notna(row.get("grade_p2")) else None,
                grade_final=float(row["grade_final"]) if pd.notna(row.get("grade_final")) else None,
                passed=int(row["passed"]) if pd.notna(row.get("passed")) else 0,
                grade_final_pct=float(row["grade_final_pct"]) if pd.notna(row.get("grade_final_pct")) else None,
                zero_final_flag=int(row["zero_final_flag"]) if pd.notna(row.get("zero_final_flag")) else 0,
                grade_trend=int(row["grade_trend"]) if pd.notna(row.get("grade_trend")) else 0,
                source_file="student_performance.csv",
                imported_at=now,
            )
            records_to_insert.append(rec)
        db.bulk_save_objects(records_to_insert)
        db.commit()
        print(f"-> Inserted {len(records_to_insert)} rows into ref_student_performance")
    else:
        print(f"-> ref_student_performance already up-to-date ({existing_sp_count} rows)")

    # 2. engagement_lms.csv (478 rows)
    lms_file = CLEANED_DIR / "engagement_lms.csv"
    if not lms_file.exists():
        raise FileNotFoundError(f"Missing {lms_file}")
    df_lms = pd.read_csv(lms_file)
    print(f"Loaded {lms_file.name}: {len(df_lms)} rows")

    existing_lms_count = db.query(RefLmsEngagement).count()
    if existing_lms_count != len(df_lms):
        db.query(RefLmsEngagement).delete()
        db.flush()
        records_to_insert = []
        now = datetime.datetime.utcnow()
        for _, row in df_lms.iterrows():
            rec = RefLmsEngagement(
                record_id=int(row.get("record_id", _ + 1)),
                gender=str(row.get("gender", "Male")),
                nationality=str(row.get("nationality", "Unknown")),
                place_of_birth=str(row.get("place_of_birth", "Unknown")),
                stage=str(row.get("stage", "Middle")),
                grade=str(row.get("grade", "7")),
                section=str(row.get("section", "A")),
                topic=str(row.get("topic", "IT")),
                semester=str(row.get("semester", "First")),
                relation=str(row.get("relation", "Father")),
                raised_hands=int(row["raised_hands"]) if pd.notna(row.get("raised_hands")) else 0,
                visited_resources=int(row["visited_resources"]) if pd.notna(row.get("visited_resources")) else 0,
                announcements_view=int(row["announcements_view"]) if pd.notna(row.get("announcements_view")) else 0,
                discussion=int(row["discussion"]) if pd.notna(row.get("discussion")) else 0,
                parent_answered_survey=str(row.get("parent_answered_survey", "No")),
                parent_school_satisfaction=str(row.get("parent_school_satisfaction", "Bad")),
                absence_band=str(row.get("absence_band", "<=7 days")),
                performance_class=str(row.get("performance_class", "Medium")),
                source_file="engagement_lms.csv",
                imported_at=now,
            )
            records_to_insert.append(rec)
        db.bulk_save_objects(records_to_insert)
        db.commit()
        print(f"-> Inserted {len(records_to_insert)} rows into ref_lms_engagement")
    else:
        print(f"-> ref_lms_engagement already up-to-date ({existing_lms_count} rows)")

    # 3. higher_ed_dropout.csv (4424 rows)
    he_file = CLEANED_DIR / "higher_ed_dropout.csv"
    if not he_file.exists():
        raise FileNotFoundError(f"Missing {he_file}")
    df_he = pd.read_csv(he_file)
    print(f"Loaded {he_file.name}: {len(df_he)} rows")

    existing_he_count = db.query(RefHigherEdDropout).count()
    if existing_he_count != len(df_he):
        db.query(RefHigherEdDropout).delete()
        db.flush()
        records_to_insert = []
        now = datetime.datetime.utcnow()
        for _, row in df_he.iterrows():
            rec = RefHigherEdDropout(
                record_id=int(row.get("record_id", _ + 1)),
                marital_status=str(row.get("marital_status", "Single")),
                application_mode=int(row["application_mode"]) if pd.notna(row.get("application_mode")) else None,
                application_order=int(row["application_order"]) if pd.notna(row.get("application_order")) else None,
                course=int(row["course"]) if pd.notna(row.get("course")) else None,
                daytime_attendance=str(row.get("daytime_attendance", "Daytime")),
                previous_qualification=int(row["previous_qualification"]) if pd.notna(row.get("previous_qualification")) else None,
                nationality=int(row["nationality"]) if pd.notna(row.get("nationality")) else None,
                mother_qualification=int(row["mother_qualification"]) if pd.notna(row.get("mother_qualification")) else None,
                father_qualification=int(row["father_qualification"]) if pd.notna(row.get("father_qualification")) else None,
                mother_occupation=int(row["mother_occupation"]) if pd.notna(row.get("mother_occupation")) else None,
                father_occupation=int(row["father_occupation"]) if pd.notna(row.get("father_occupation")) else None,
                displaced=int(row["displaced"]) if pd.notna(row.get("displaced")) else 0,
                educational_special_needs=int(row["educational_special_needs"]) if pd.notna(row.get("educational_special_needs")) else 0,
                debtor=int(row["debtor"]) if pd.notna(row.get("debtor")) else 0,
                tuition_fees_up_to_date=int(row["tuition_fees_up_to_date"]) if pd.notna(row.get("tuition_fees_up_to_date")) else 1,
                gender=str(row.get("gender", "Male")),
                scholarship_holder=int(row["scholarship_holder"]) if pd.notna(row.get("scholarship_holder")) else 0,
                age_at_enrollment=int(row["age_at_enrollment"]) if pd.notna(row.get("age_at_enrollment")) else 18,
                international=int(row["international"]) if pd.notna(row.get("international")) else 0,
                sem1_credited=float(row["sem1_credited"]) if pd.notna(row.get("sem1_credited")) else 0.0,
                sem1_enrolled=float(row["sem1_enrolled"]) if pd.notna(row.get("sem1_enrolled")) else 0.0,
                sem1_evaluations=float(row["sem1_evaluations"]) if pd.notna(row.get("sem1_evaluations")) else 0.0,
                sem1_approved=float(row["sem1_approved"]) if pd.notna(row.get("sem1_approved")) else 0.0,
                sem1_grade=float(row["sem1_grade"]) if pd.notna(row.get("sem1_grade")) else 0.0,
                sem1_without_eval=float(row["sem1_without_eval"]) if pd.notna(row.get("sem1_without_eval")) else 0.0,
                sem2_credited=float(row["sem2_credited"]) if pd.notna(row.get("sem2_credited")) else 0.0,
                sem2_enrolled=float(row["sem2_enrolled"]) if pd.notna(row.get("sem2_enrolled")) else 0.0,
                sem2_evaluations=float(row["sem2_evaluations"]) if pd.notna(row.get("sem2_evaluations")) else 0.0,
                sem2_approved=float(row["sem2_approved"]) if pd.notna(row.get("sem2_approved")) else 0.0,
                sem2_grade=float(row["sem2_grade"]) if pd.notna(row.get("sem2_grade")) else 0.0,
                sem2_without_eval=float(row["sem2_without_eval"]) if pd.notna(row.get("sem2_without_eval")) else 0.0,
                unemployment_rate=float(row["unemployment_rate"]) if pd.notna(row.get("unemployment_rate")) else 0.0,
                inflation_rate=float(row["inflation_rate"]) if pd.notna(row.get("inflation_rate")) else 0.0,
                gdp=float(row["gdp"]) if pd.notna(row.get("gdp")) else 0.0,
                outcome=str(row.get("outcome", "Enrolled")),
                sem1_pass_rate=float(row["sem1_pass_rate"]) if pd.notna(row.get("sem1_pass_rate")) else None,
                sem2_pass_rate=float(row["sem2_pass_rate"]) if pd.notna(row.get("sem2_pass_rate")) else None,
                pass_rate_change=float(row["pass_rate_change"]) if pd.notna(row.get("pass_rate_change")) else None,
                grade_change=float(row["grade_change"]) if pd.notna(row.get("grade_change")) else None,
                dropout_flag=int(row["dropout_flag"]) if pd.notna(row.get("dropout_flag")) else 0,
                source_file="higher_ed_dropout.csv",
                imported_at=now,
            )
            records_to_insert.append(rec)
        db.bulk_save_objects(records_to_insert)
        db.commit()
        print(f"-> Inserted {len(records_to_insert)} rows into ref_higher_ed_dropout")
    else:
        print(f"-> ref_higher_ed_dropout already up-to-date ({existing_he_count} rows)")


def populate_operational_tables(db: Session):
    print("--- 2. Populating Operational Tables from Reference Data (data_origin='dataset') ---")

    # 1. School setup
    school = db.query(School).filter(School.udise_code == "33280100412").first()
    if not school:
        school = School(
            udise_code="33280100412",
            name="Government Higher Secondary School Kovilpatti",
            district="Thoothukudi",
            block="Kovilpatti",
            data_origin="dataset",
            source_ref="official:udise_33280100412",
        )
        db.add(school)
        db.flush()
    print(f"Operational School ID: {school.id} ({school.name})")

    # 2. Academic Year (Current operational period)
    ay = db.query(AcademicYear).filter(AcademicYear.school_id == school.id, AcademicYear.is_current == True).first()
    if not ay:
        ay = AcademicYear(school_id=school.id, year_name="2025-26", is_current=True)
        db.add(ay)
        db.flush()

    # 3. Reporting Periods (Term 1, Term 2, Term 3)
    p_names = [
        ("Term 1", datetime.date(2024, 6, 3), datetime.date(2024, 9, 27), 1),
        ("Term 2", datetime.date(2024, 10, 7), datetime.date(2024, 12, 23), 2),
        ("Term 3", datetime.date(2025, 1, 2), datetime.date(2025, 4, 15), 3),
    ]
    periods = {}
    for p_name, s_date, e_date, seq in p_names:
        rp = db.query(ReportingPeriod).filter(ReportingPeriod.academic_year_id == ay.id, ReportingPeriod.name == p_name).first()
        if not rp:
            rp = ReportingPeriod(
                academic_year_id=ay.id,
                name=p_name,
                start_date=s_date,
                end_date=e_date,
                sequence_order=seq,
                is_current=(seq == 2),
            )
            db.add(rp)
            db.flush()
        periods[seq] = rp

    # 4. Class Sections
    # High school classes: 10-A, 10-B, 11-A, 11-B, 12-A, 12-B
    # Middle school classes: 7-A, 8-A, 9-A
    class_map = {}
    class_specs = [
        (10, "A"), (10, "B"), (11, "A"), (11, "B"), (12, "A"), (12, "B"),
        (7, "A"), (8, "A"), (9, "A")
    ]
    for gr, sec in class_specs:
        cs = db.query(ClassSection).filter(
            ClassSection.school_id == school.id,
            ClassSection.academic_year_id == ay.id,
            ClassSection.grade == gr,
            ClassSection.section == sec
        ).first()
        if not cs:
            cs = ClassSection(
                school_id=school.id,
                academic_year_id=ay.id,
                grade=gr,
                section=sec,
                data_origin="dataset",
                source_ref=f"class:{gr}-{sec}",
            )
            db.add(cs)
            db.flush()
        class_map[(gr, sec)] = cs

    # 5. Populate Students from ref_student_performance (1044 students)
    ref_sp_all = db.query(RefStudentPerformance).order_by(RefStudentPerformance.id).all()
    print(f"Mapping {len(ref_sp_all)} students from ref_student_performance...")

    hs_classes = [(10, "A"), (10, "B"), (11, "A"), (11, "B"), (12, "A"), (12, "B")]
    student_count_sp = 0

    for idx, ref in enumerate(ref_sp_all):
        source_ref_val = f"ref_student_performance:{ref.id}"
        existing_stu = db.query(Student).filter(Student.source_ref == source_ref_val).first()

        # Class section distribution based on age & index
        if ref.age and ref.age <= 16:
            gr, sec = hs_classes[idx % 2]  # 10-A or 10-B
        elif ref.age and ref.age == 17:
            gr, sec = hs_classes[2 + (idx % 2)]  # 11-A or 11-B
        else:
            gr, sec = hs_classes[4 + (idx % 2)]  # 12-A or 12-B

        target_cs = class_map.get((gr, sec))
        emis_id_val = f"33280100412{idx + 1:05d}"

        if not existing_stu:
            full_name = generate_tn_name(idx, ref.gender)
            g_name = generate_guardian_name(idx)
            g_phone = f"984210{idx % 10000:04d}"

            student = Student(
                school_id=school.id,
                emis_id=emis_id_val,
                full_name=full_name,
                gender=ref.gender or "Male",
                current_class_section_id=target_cs.id if target_cs else None,
                guardian_name=g_name,
                guardian_phone=g_phone,
                address="Kovilpatti, Thoothukudi Dist, Tamil Nadu",
                is_active=True,
                data_origin="dataset",
                source_ref=source_ref_val,
            )
            db.add(student)
            db.flush()
            student_count_sp += 1
        else:
            student = existing_stu

        # Student Profile
        existing_prof = db.query(StudentProfile).filter(StudentProfile.student_id == student.id).first()
        if not existing_prof:
            prof = StudentProfile(
                student_id=student.id,
                age=ref.age,
                address=ref.address,
                family_size=ref.family_size,
                parents_status=ref.parents_status,
                mother_edu=ref.mother_edu,
                father_edu=ref.father_edu,
                mother_job=ref.mother_job,
                father_job=ref.father_job,
                reason=ref.reason,
                guardian=ref.guardian,
                travel_time=ref.travel_time,
                study_time=ref.study_time,
                failures=ref.failures,
                school_support=ref.school_support,
                family_support=ref.family_support,
                paid_classes=ref.paid_classes,
                activities=ref.activities,
                nursery=ref.nursery,
                wants_higher_edu=ref.wants_higher_edu,
                internet=ref.internet,
                romantic=ref.romantic,
                family_relationship=ref.family_relationship,
                free_time=ref.free_time,
                go_out=ref.go_out,
                workday_alcohol=ref.workday_alcohol,
                weekend_alcohol=ref.weekend_alcohol,
                health=ref.health,
                raw_profile_data={
                    "absences": ref.absences,
                    "passed": ref.passed,
                    "grade_trend": ref.grade_trend,
                    "grade_final_pct": ref.grade_final_pct,
                },
            )
            db.add(prof)

        # Assessments: P1, P2, Final
        existing_asms = db.query(AssessmentRecord).filter(AssessmentRecord.student_id == student.id, AssessmentRecord.data_origin == "dataset").count()
        if existing_asms < 3:
            subj_name = "Mathematics" if ref.subject == "Math" else "Language Arts"
            # Term 1
            if ref.grade_p1 is not None:
                m_p1 = round((float(ref.grade_p1) / 20.0) * 100.0, 1)
                db.add(AssessmentRecord(
                    student_id=student.id,
                    school_id=school.id,
                    reporting_period_id=periods[1].id,
                    assessment_name="Term 1 Continuous Assessment",
                    subject=subj_name,
                    assessment_date=datetime.date(2024, 9, 20),
                    marks_obtained=m_p1,
                    max_marks=100.0,
                    percentage=m_p1,
                    data_origin="dataset",
                    source_ref=source_ref_val,
                ))
            # Term 2
            if ref.grade_p2 is not None:
                m_p2 = round((float(ref.grade_p2) / 20.0) * 100.0, 1)
                db.add(AssessmentRecord(
                    student_id=student.id,
                    school_id=school.id,
                    reporting_period_id=periods[2].id,
                    assessment_name="Term 2 Continuous Assessment",
                    subject=subj_name,
                    assessment_date=datetime.date(2024, 12, 12),
                    marks_obtained=m_p2,
                    max_marks=100.0,
                    percentage=m_p2,
                    data_origin="dataset",
                    source_ref=source_ref_val,
                ))
            # Term 3
            if ref.grade_final is not None:
                m_fin = round((float(ref.grade_final) / 20.0) * 100.0, 1)
                db.add(AssessmentRecord(
                    student_id=student.id,
                    school_id=school.id,
                    reporting_period_id=periods[3].id,
                    assessment_name="Term 3 Final Assessment",
                    subject=subj_name,
                    assessment_date=datetime.date(2025, 3, 20),
                    marks_obtained=m_fin,
                    max_marks=100.0,
                    percentage=m_fin,
                    data_origin="dataset",
                    source_ref=source_ref_val,
                ))

    db.commit()
    print(f"-> Created/Updated {len(ref_sp_all)} students from student_performance")

    # 6. Populate Students from ref_lms_engagement (478 students)
    ref_lms_all = db.query(RefLmsEngagement).order_by(RefLmsEngagement.id).all()
    print(f"Mapping {len(ref_lms_all)} students from ref_lms_engagement...")

    lms_classes = [(7, "A"), (8, "A"), (9, "A"), (10, "A")]

    for idx, ref in enumerate(ref_lms_all):
        source_ref_val = f"ref_lms_engagement:{ref.id}"
        existing_stu = db.query(Student).filter(Student.source_ref == source_ref_val).first()

        gr_num = 8
        try:
            gr_num = int(str(ref.grade).replace("G-", "").replace("g-", ""))
        except Exception:
            gr_num = 7 + (idx % 3)

        if gr_num not in [7, 8, 9, 10]:
            gr_num = 7 + (idx % 3)

        target_cs = class_map.get((gr_num, "A")) or class_map.get((10, "A"))
        emis_id_val = f"33280100412{1044 + idx + 1:05d}"

        if not existing_stu:
            full_name = generate_tn_name(1044 + idx, ref.gender)
            g_name = generate_guardian_name(1044 + idx)
            g_phone = f"984210{(1044 + idx) % 10000:04d}"

            student = Student(
                school_id=school.id,
                emis_id=emis_id_val,
                full_name=full_name,
                gender=ref.gender or "Male",
                current_class_section_id=target_cs.id if target_cs else None,
                guardian_name=g_name,
                guardian_phone=g_phone,
                address="Kovilpatti, Thoothukudi Dist, Tamil Nadu",
                is_active=True,
                data_origin="dataset",
                source_ref=source_ref_val,
            )
            db.add(student)
            db.flush()
        else:
            student = existing_stu

        # Engagement metrics
        existing_eng = db.query(StudentEngagementMetric).filter(StudentEngagementMetric.student_id == student.id).first()
        if not existing_eng:
            eng = StudentEngagementMetric(
                student_id=student.id,
                stage=ref.stage,
                topic=ref.topic,
                semester=ref.semester,
                relation=ref.relation,
                raised_hands=ref.raised_hands,
                visited_resources=ref.visited_resources,
                announcements_view=ref.announcements_view,
                discussion=ref.discussion,
                parent_answered_survey=ref.parent_answered_survey,
                parent_school_satisfaction=ref.parent_school_satisfaction,
                absence_band=ref.absence_band,
                performance_class=ref.performance_class,
            )
            db.add(eng)

    db.commit()
    print(f"-> Created/Updated {len(ref_lms_all)} students from engagement_lms")
    print(f"Total operational students in school: {db.query(Student).filter(Student.school_id == school.id).count()}")


def main():
    db = SessionLocal()
    try:
        import_reference_datasets(db)
        populate_operational_tables(db)
        print("Import completed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
