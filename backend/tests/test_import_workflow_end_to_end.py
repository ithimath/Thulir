"""End-to-end acceptance test for Data Import workflow, error handling, and data reflection."""
import io
import pytest
from backend.app.database import SessionLocal
from backend.app.models.models import Student, ImportBatch, User
from backend.app.services.import_service import (
    parse_file_to_dataframe,
    validate_student_rows,
    commit_student_import,
    validate_attendance_rows,
    commit_attendance_import,
    validate_marks_rows,
    commit_marks_import,
)
from backend.app.models.models import AttendanceRecord, AssessmentRecord, WarningIndicator

def test_invalid_student_file_rejected():
    db = SessionLocal()
    with open("backend/data/test_invalid_import.csv", "rb") as f:
        content = f.read()
    
    df = parse_file_to_dataframe(content, "test_invalid_import.csv")
    with pytest.raises(ValueError) as excinfo:
        validate_student_rows(df, school_id=1, db=db)
    assert "Missing required columns" in str(excinfo.value)
    db.close()

def test_valid_student_import_lifecycle():
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    assert admin is not None
    school_id = 1

    # Clean up any previous test students if present
    test_emis_list = ["3328099001", "3328099002", "3328099003", "3328099004", "3328099005"]
    db.query(Student).filter(Student.emis_id.in_(test_emis_list)).delete(synchronize_session=False)
    db.commit()

    # Initial count
    initial_count = db.query(Student).filter(Student.school_id == school_id, Student.is_active == True).count()

    # 1. Parse file
    with open("backend/data/test_student_import.csv", "rb") as f:
        content = f.read()
    df = parse_file_to_dataframe(content, "test_student_import.csv")
    assert len(df) == 5

    # 2. Validate rows
    rows_analysis, stats = validate_student_rows(df, school_id, db)
    assert stats["valid"] == 5
    assert stats["rejected"] == 0
    assert stats["duplicates"] == 0

    # 3. Create batch
    batch = ImportBatch(
        school_id=school_id,
        uploaded_by_id=admin.id,
        file_name="test_student_import.csv",
        file_type="csv",
        import_type="students",
        total_rows=len(df),
        imported_count=0,
        warnings_count=stats["warnings"],
        rejected_count=stats["rejected"],
        duplicates_count=stats["duplicates"],
        status="validated",
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # 4. Commit batch
    res = commit_student_import(batch, rows_analysis, school_id, db)
    assert res["imported"] == 5
    assert res["duplicates"] == 0
    assert res["rejected"] == 0
    assert batch.status == "committed"

    # 5. Verify database storage and data_origin
    stored_students = db.query(Student).filter(Student.emis_id.in_(test_emis_list)).all()
    assert len(stored_students) == 5
    for s in stored_students:
        assert s.data_origin == "user"
        assert s.is_active is True
        assert s.class_section is not None

    aakash = db.query(Student).filter(Student.emis_id == "3328099001").first()
    assert aakash.full_name == "Aakash Murugan"
    assert aakash.class_section.grade == 10
    assert aakash.class_section.section == "A"

    # 6. Verify total enrolled count increased by exactly 5
    new_count = db.query(Student).filter(Student.school_id == school_id, Student.is_active == True).count()
    assert new_count == initial_count + 5

    # 7. Test re-importing same file -> handles update without duplicate primary key crash
    rows_analysis_re, stats_re = validate_student_rows(df, school_id, db)
    assert stats_re["warnings"] == 5 # All 5 detected as existing in school
    assert stats_re["valid"] == 0

    batch2 = ImportBatch(
        school_id=school_id,
        uploaded_by_id=admin.id,
        file_name="test_student_import_re.csv",
        file_type="csv",
        import_type="students",
        total_rows=len(df),
        status="validated",
    )
    db.add(batch2)
    db.commit()
    db.refresh(batch2)

    res2 = commit_student_import(batch2, rows_analysis_re, school_id, db)
    assert res2["imported"] == 0
    assert res2["duplicates"] == 5
    assert batch2.status == "committed"

    db.close()


def test_attendance_and_marks_import_lifecycle():
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    school_id = 1

    # 1. Attendance CSV with 1 student below 75% floor (triggers ATT-LOW)
    att_csv = b"""emis_id,total_days,attended_days
3328099001,80,50
3328099002,80,75
"""
    df_att = parse_file_to_dataframe(att_csv, "test_att.csv")
    rows_att, stats_att = validate_attendance_rows(df_att, school_id, db)
    assert stats_att["valid"] == 2
    assert stats_att["rejected"] == 0

    batch_att = ImportBatch(
        school_id=school_id,
        uploaded_by_id=admin.id,
        file_name="test_att.csv",
        file_type="csv",
        import_type="attendance",
        total_rows=2,
        status="validated",
    )
    db.add(batch_att)
    db.commit()
    db.refresh(batch_att)

    res_att = commit_attendance_import(batch_att, rows_att, school_id, db)
    assert res_att["imported"] >= 1 or res_att["duplicates"] >= 1

    # Verify Aakash Murugan (50/80 = 62.5%) triggered ATT-LOW indicator
    aakash = db.query(Student).filter(Student.emis_id == "3328099001").first()
    att_ind = db.query(WarningIndicator).filter(
        WarningIndicator.student_id == aakash.id,
        WarningIndicator.rule_code == "ATT-LOW",
        WarningIndicator.is_superseded == False
    ).first()
    assert att_ind is not None
    assert "62.5%" in att_ind.plain_explanation
    assert "statutory floor" in att_ind.plain_explanation

    # 2. Marks CSV with 1 student scoring 25/100 in Mathematics (triggers MARK-LOW)
    marks_csv = b"""emis_id,subject,marks_obtained,max_marks,assessment_type
3328099002,Mathematics,25,100,Quarterly Exam
3328099003,Science,85,100,Quarterly Exam
"""
    df_marks = parse_file_to_dataframe(marks_csv, "test_marks.csv")
    rows_m, stats_m = validate_marks_rows(df_marks, school_id, db)
    assert stats_m["valid"] == 2
    assert stats_m["rejected"] == 0

    batch_m = ImportBatch(
        school_id=school_id,
        uploaded_by_id=admin.id,
        file_name="test_marks.csv",
        file_type="csv",
        import_type="marks",
        total_rows=2,
        status="validated",
    )
    db.add(batch_m)
    db.commit()
    db.refresh(batch_m)

    res_m = commit_marks_import(batch_m, rows_m, school_id, db)
    assert res_m["imported"] >= 1 or res_m["duplicates"] >= 1

    # Verify Bharathi Kannan (25%) triggered MARK-LOW indicator
    bharathi = db.query(Student).filter(Student.emis_id == "3328099002").first()
    mark_ind = db.query(WarningIndicator).filter(
        WarningIndicator.student_id == bharathi.id,
        WarningIndicator.rule_code == "MARK-LOW",
        WarningIndicator.is_superseded == False
    ).first()
    assert mark_ind is not None
    assert "25.0%" in mark_ind.plain_explanation
    assert "below the 35% pass threshold" in mark_ind.plain_explanation

    db.close()
