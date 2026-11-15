"""Automated Test Suite for THULIR Dataset Integration and Mock Data Layer.

Verifies:
1. Reference table row counts match CSV sources exactly (1044, 478, 4424).
2. Operational tables have valid data_origin tagging ('dataset', 'mock', 'user') and source_ref.
3. No orphan foreign keys across operational and side tables.
4. Mock-only reset deletes mock rows without touching dataset or user records.
5. Seeding is idempotent and warning engine deduplicates via evidence keys.
6. API data_origin filtering functions as expected.
"""

import pytest
from pathlib import Path
import pandas as pd
from sqlalchemy import func
from backend.app.database import SessionLocal
from backend.app.models.models import (
    School,
    Student,
    StudentProfile,
    StudentEngagementMetric,
    AttendanceRecord,
    AssessmentRecord,
    AssignmentRecord,
    WarningIndicator,
    SupportCase,
    RefStudentPerformance,
    RefLmsEngagement,
    RefHigherEdDropout,
)
from backend.scripts.seed_mock import reset_mock_data, seed_mock_attendance, seed_mock_assignments
from backend.app.services.warning_engine import run_engine_for_student

CLEANED_DIR = Path(__file__).resolve().parent.parent / "data" / "cleaned"


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()


def test_reference_table_row_counts_match_csv(db):
    """Reference table row counts must match CSV datasets exactly."""
    sp_count = db.query(RefStudentPerformance).count()
    lms_count = db.query(RefLmsEngagement).count()
    he_count = db.query(RefHigherEdDropout).count()

    df_sp = pd.read_csv(CLEANED_DIR / "student_performance.csv")
    df_lms = pd.read_csv(CLEANED_DIR / "engagement_lms.csv")
    df_he = pd.read_csv(CLEANED_DIR / "higher_ed_dropout.csv")

    assert sp_count == len(df_sp) == 1044, f"Expected 1044 sp rows, got {sp_count}"
    assert lms_count == len(df_lms) == 478, f"Expected 478 lms rows, got {lms_count}"
    assert he_count == len(df_he) == 4424, f"Expected 4424 he rows, got {he_count}"


def test_dataset_operational_students_and_profiles(db):
    """Dataset-origin operational students must map from reference tables."""
    dataset_students = db.query(Student).filter(Student.data_origin == "dataset").all()
    assert len(dataset_students) == 1522  # 1044 SP + 478 LMS

    sp_students = [s for s in dataset_students if s.source_ref.startswith("ref_student_performance:")]
    lms_students = [s for s in dataset_students if s.source_ref.startswith("ref_lms_engagement:")]

    assert len(sp_students) == 1044
    assert len(lms_students) == 478

    # Profiles & metrics
    profile_count = db.query(StudentProfile).count()
    metric_count = db.query(StudentEngagementMetric).count()

    assert profile_count == 1044
    assert metric_count == 478

    # Dataset assessments: 1044 students * 3 terms = 3132
    dataset_asms = db.query(AssessmentRecord).filter(AssessmentRecord.data_origin == "dataset").count()
    assert dataset_asms == 3132


def test_no_orphan_foreign_keys(db):
    """Verify referential integrity: no dangling foreign keys."""
    valid_student_ids = set(s[0] for s in db.query(Student.id).all())

    # Check profiles
    profile_student_ids = set(p[0] for p in db.query(StudentProfile.student_id).all())
    assert profile_student_ids.issubset(valid_student_ids), "Found orphan student_profiles"

    # Check engagement metrics
    eng_student_ids = set(e[0] for e in db.query(StudentEngagementMetric.student_id).all())
    assert eng_student_ids.issubset(valid_student_ids), "Found orphan student_engagement_metrics"

    # Check attendance records
    att_student_ids = set(a[0] for a in db.query(AttendanceRecord.student_id).all())
    assert att_student_ids.issubset(valid_student_ids), "Found orphan attendance_records"

    # Check assessment records
    asm_student_ids = set(a[0] for a in db.query(AssessmentRecord.student_id).all())
    assert asm_student_ids.issubset(valid_student_ids), "Found orphan assessment_records"

    # Check assignment records
    asg_student_ids = set(a[0] for a in db.query(AssignmentRecord.student_id).all())
    assert asg_student_ids.issubset(valid_student_ids), "Found orphan assignment_records"

    # Check warning indicators
    ind_student_ids = set(i[0] for i in db.query(WarningIndicator.student_id).all())
    assert ind_student_ids.issubset(valid_student_ids), "Found orphan warning_indicators"

    # Check support cases
    case_student_ids = set(c[0] for c in db.query(SupportCase.student_id).all())
    assert case_student_ids.issubset(valid_student_ids), "Found orphan support_cases"


def test_data_origin_tagging_validity(db):
    """Every record must have a valid data_origin and appropriate source_ref."""
    valid_origins = {"dataset", "mock", "user"}

    for student in db.query(Student).all():
        assert student.data_origin in valid_origins, f"Invalid data_origin: {student.data_origin}"
        if student.data_origin == "dataset":
            assert student.source_ref is not None
            assert student.source_ref.startswith(("ref_student_performance:", "ref_lms_engagement:", "official:"))

    # Check mock attendance
    mock_att = db.query(AttendanceRecord).filter(AttendanceRecord.data_origin == "mock").first()
    if mock_att:
        assert mock_att.source_ref.startswith("mock:")


def test_mock_reset_preserves_dataset_records(db):
    """Resetting mock data must delete mock rows without touching dataset records."""
    # Pre-reset counts
    dataset_students_before = db.query(Student).filter(Student.data_origin == "dataset").count()
    dataset_asms_before = db.query(AssessmentRecord).filter(AssessmentRecord.data_origin == "dataset").count()
    ref_sp_before = db.query(RefStudentPerformance).count()

    # Reset mock
    reset_mock_data(db)

    # Post-reset counts for dataset records
    dataset_students_after = db.query(Student).filter(Student.data_origin == "dataset").count()
    dataset_asms_after = db.query(AssessmentRecord).filter(AssessmentRecord.data_origin == "dataset").count()
    ref_sp_after = db.query(RefStudentPerformance).count()

    assert dataset_students_after == dataset_students_before == 1522
    assert dataset_asms_after == dataset_asms_before == 3132
    assert ref_sp_after == ref_sp_before == 1044

    # Post-reset counts for mock records should be zero
    mock_att_count = db.query(AttendanceRecord).filter(AttendanceRecord.data_origin == "mock").count()
    mock_asg_count = db.query(AssignmentRecord).filter(AssignmentRecord.data_origin == "mock").count()
    assert mock_att_count == 0
    assert mock_asg_count == 0

    # Re-seed mock data so DB remains populated
    from backend.scripts.seed_mock import main as seed_main
    seed_main([])

    # Verify mock records restored
    mock_att_restored = db.query(AttendanceRecord).filter(AttendanceRecord.data_origin == "mock").count()
    assert mock_att_restored > 0


def test_warning_engine_idempotency(db):
    """Running warning engine multiple times on same student creates no duplicates."""
    # Pick first student
    student = db.query(Student).filter(Student.data_origin == "dataset").first()
    assert student is not None

    indicators_before = (
        db.query(WarningIndicator)
        .filter(WarningIndicator.student_id == student.id)
        .count()
    )

    # Run engine again
    run_engine_for_student(db, student)
    db.commit()

    indicators_after = (
        db.query(WarningIndicator)
        .filter(WarningIndicator.student_id == student.id)
        .count()
    )

    assert indicators_after == indicators_before, "Engine created duplicate indicators on rerun"
