"""Direct sync tests for Academic Year and Import History logic without anyio TestClient."""
import pytest
from backend.app.database import SessionLocal
from backend.app.models.models import AcademicYear, ReportingPeriod, ImportBatch, User, UserSchoolRole

def test_academic_year_is_2025_26():
    db = SessionLocal()
    try:
        ay = db.query(AcademicYear).filter(AcademicYear.is_current == True).first()
        assert ay is not None
        assert ay.year_name == "2025-26"
    finally:
        db.close()

def test_reporting_periods_exist_for_current_year():
    db = SessionLocal()
    try:
        ay = db.query(AcademicYear).filter(AcademicYear.is_current == True).first()
        periods = db.query(ReportingPeriod).filter(ReportingPeriod.academic_year_id == ay.id).all()
        assert len(periods) >= 1
        current_period = next((p for p in periods if p.is_current), None)
        assert current_period is not None
        assert current_period.name in ["Term I", "Term II", "Term 1", "Term 2"]
    finally:
        db.close()

def test_users_and_roles_registered():
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        assert admin_user is not None

        teacher_user = db.query(User).filter(User.username == "teacher").first()
        assert teacher_user is not None

        counsellor_user = db.query(User).filter(User.username == "counsellor").first()
        assert counsellor_user is not None
    finally:
        db.close()

def test_import_batch_schema():
    db = SessionLocal()
    try:
        batches = db.query(ImportBatch).all()
        assert isinstance(batches, list)
    finally:
        db.close()

def test_ai_summary_generation_and_approval_workflow():
    from backend.app.config import settings
    from backend.app.models.models import Student, CaseNote
    from backend.app.services.ai_summary_service import generate_student_ai_summary, approve_and_save_ai_summary

    assert settings.AI_ENABLED is True, "AI_ENABLED should be true in environment"

    db = SessionLocal()
    try:
        student = db.query(Student).first()
        assert student is not None

        # 1. Generate Grounded AI Draft Summary
        summary = generate_student_ai_summary(db, student.id)
        assert summary["available"] is True
        assert summary["status"] == "DRAFT"
        assert summary["is_draft"] is True
        assert summary["requires_human_approval"] is True
        assert f"REF-{student.id:04d}" in summary["summary_text"]
        assert len(summary["sources_cited"]) > 0

        # Verify no raw PII in anonymized reference ID
        assert student.full_name not in summary["anonymized_reference_id"]

        # 2. Staff Explicit Approval Flow
        admin_user = db.query(User).filter(User.username == "admin").first()
        approved = approve_and_save_ai_summary(
            db=db,
            student_id=student.id,
            staff_user_id=admin_user.id,
            approved_text=summary["summary_text"] + " [Staff Approved]",
        )
        assert approved["status"] == "APPROVED_AND_SAVED"
        assert approved["case_id"] is not None

        # Verify saved note in database
        note = db.query(CaseNote).filter(CaseNote.id == approved["note_id"]).first()
        assert note is not None
        assert "[Staff Approved]" in note.note_text
    finally:
        db.close()

