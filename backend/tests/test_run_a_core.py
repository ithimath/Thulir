"""Acceptance and integration tests for Run A: Data-Trust Core.

Covers:
- Feature 1: Evidence-to-Intervention Pipeline & Duplicate Case Prevention
- Feature 2: Indicator Verification & Correction Centre (Super-ceding records & RBAC)
- Feature 3: Data Quality Monitor (Import anomalies matching quality issues)
- Feature 5: Student Support History (Shared timeline & confidential note privacy)
"""
import pytest
import datetime
import httpx

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.services.seed_service import seed_demo_data
from backend.app.models.models import (
    Student,
    AssessmentRecord,
    AttendanceRecord,
    WarningIndicator,
    SupportCase,
    DataCorrection,
    User,
)


@pytest.fixture(scope="module", autouse=True)
def init_db():
    db = SessionLocal()
    seed_demo_data(db, force=True)
    db.close()


async def get_token(client: httpx.AsyncClient, username: str) -> str:
    resp = await client.post("/api/auth/login", json={"username": username, "password": "Password123!"})
    assert resp.status_code == 200
    return resp.json()["token"]


# ---------------------------------------------------------------------------
# FEATURE 1: EVIDENCE-TO-INTERVENTION PIPELINE ACCEPTANCE TEST
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_feature_1_evidence_to_intervention_pipeline():
    """ACCEPTANCE TEST F1:

    An indicator is reviewed, a case is created from it, an intervention and follow-up are added,
    and all appear in one timeline in order. Attempting to create a second case for the same indicator
    is blocked with a clear message.
    """
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        admin_tok = await get_token(client, "admin")
        counsellor_tok = await get_token(client, "counsellor")

        # 1. Reset/Ensure an indicator in 'Needs Review' status with no linked case
        db = SessionLocal()
        kavitha = db.query(Student).filter(Student.emis_id == "3328014490").first()
        student_id = kavitha.id
        
        # Clear any existing cases linked to this indicator
        ind = db.query(WarningIndicator).filter(
            WarningIndicator.student_id == student_id,
            WarningIndicator.category == "attendance"
        ).first()
        if ind:
            db.query(SupportCase).filter(SupportCase.indicator_id == ind.id).delete()
            ind.status = "Needs Review"
            ind.is_superseded = False
            db.commit()
            ind_id = ind.id
        else:
            db.close()
            await client.post("/api/indicators/run-engine", headers={"Authorization": f"Bearer {admin_tok}"})
            db = SessionLocal()
            ind = db.query(WarningIndicator).filter(WarningIndicator.student_id == student_id).first()
            ind_id = ind.id
        db.close()

        # 2. Inspect underlying evidence records (Feature 1 Pipeline requirement)
        ev_resp = await client.get(f"/api/indicators/{ind_id}/evidence-records", headers={"Authorization": f"Bearer {admin_tok}"})
        assert ev_resp.status_code == 200
        ev_data = ev_resp.json()
        assert len(ev_data["records"]) > 0

        # 3. Review the indicator with staff notes
        rev_resp = await client.post(
            f"/api/indicators/{ind_id}/review",
            headers={"Authorization": f"Bearer {admin_tok}"},
            json={
                "new_status": "Under Review",
                "review_notes": "Reviewed evidence records with class teacher; preparing intervention.",
            }
        )
        assert rev_resp.status_code == 200

        # 4. Create support case connected to indicator
        counsellor_me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {counsellor_tok}"})
        counsellor_id = counsellor_me.json()["id"]

        case_resp = await client.post(
            "/api/cases",
            headers={"Authorization": f"Bearer {admin_tok}"},
            json={
                "student_id": student_id,
                "indicator_id": ind_id,
                "assigned_staff_id": counsellor_id,
                "category": "attendance",
                "priority": "High",
                "reason": "Attendance dropped below threshold. Action required.",
                "observations": "Student missing morning sessions regularly.",
            }
        )
        assert case_resp.status_code == 201
        case_id = case_resp.json()["id"]

        # 5. ATTEMPT TO CREATE SECOND CASE FOR SAME INDICATOR -> MUST BE BLOCKED (HTTP 409)
        dup_case_resp = await client.post(
            "/api/cases",
            headers={"Authorization": f"Bearer {admin_tok}"},
            json={
                "student_id": student_id,
                "indicator_id": ind_id,
                "assigned_staff_id": counsellor_id,
                "category": "attendance",
                "priority": "High",
                "reason": "Duplicate case attempt for same indicator.",
            }
        )
        assert dup_case_resp.status_code == 409
        assert "already exists for this indicator" in dup_case_resp.json()["detail"]

        # 6. Add an intervention
        inv_resp = await client.post(
            f"/api/cases/{case_id}/interventions",
            headers={"Authorization": f"Bearer {admin_tok}"},
            json={
                "intervention_type": "attendance_followup",
                "title": "Morning transport assistance & guardian talk",
                "description": "Speak with guardian regarding bus transit delays.",
                "start_date": str(datetime.date.today()),
            }
        )
        assert inv_resp.status_code == 201
        inv_id = inv_resp.json()["id"]

        # 7. Add a follow-up
        fu_resp = await client.post(
            f"/api/cases/{case_id}/follow-ups",
            headers={"Authorization": f"Bearer {admin_tok}"},
            json={
                "intervention_id": inv_id,
                "assigned_staff_id": counsellor_id,
                "due_date": str(datetime.date.today() + datetime.timedelta(days=4)),
                "notes": "Check student attendance register on Friday.",
            }
        )
        assert fu_resp.status_code == 201

        # 8. Verify all appear in the shared chronological timeline in order
        tl_resp = await client.get(
            f"/api/students/{student_id}/timeline?case_id={case_id}",
            headers={"Authorization": f"Bearer {admin_tok}"}
        )
        assert tl_resp.status_code == 200
        tl_data = tl_resp.json()
        event_types = [e["event_type"] for e in tl_data["events"]]

        assert "indicator_detected" in event_types
        assert "indicator_reviewed" in event_types
        assert "case_created" in event_types
        assert "intervention_started" in event_types
        assert "follow_up_scheduled" in event_types

        # Verify timeline is chronologically sorted
        timestamps = [e["timestamp"] for e in tl_data["events"]]
        assert timestamps == sorted(timestamps)


# ---------------------------------------------------------------------------
# FEATURE 2: INDICATOR VERIFICATION & CORRECTION CENTRE ACCEPTANCE TEST
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_feature_2_indicator_verification_and_correction_centre():
    """ACCEPTANCE TEST F2:

    Correcting a mark creates a superseding record, preserves the original,
    re-runs the rule engine, and keeps the old indicator in history.
    A teacher's direct API call to apply (not propose) a correction is rejected.
    """
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        teacher_tok = await get_token(client, "teacher")
        admin_tok = await get_token(client, "admin")

        # 1. Get Kavitha (in Teacher's class 10-B) and ensure her CAT 3 assessment is 24 marks
        db = SessionLocal()
        kavitha = db.query(Student).filter(Student.emis_id == "3328014490").first()
        student_id = kavitha.id
        failing_asm = db.query(AssessmentRecord).filter(
            AssessmentRecord.student_id == student_id,
            AssessmentRecord.assessment_name == "CAT 3",
            AssessmentRecord.subject == "Mathematics",
        ).first()
        if not failing_asm:
            failing_asm = AssessmentRecord(
                student_id=student_id,
                school_id=kavitha.school_id,
                assessment_name="CAT 3",
                subject="Mathematics",
                assessment_date=datetime.date(2025, 1, 18),
                marks_obtained=24.0,
                max_marks=100.0,
                percentage=24.0,
                is_superseded=False,
            )
            db.add(failing_asm)
        else:
            failing_asm.is_superseded = False
            failing_asm.marks_obtained = 24.0
            failing_asm.percentage = 24.0
            failing_asm.superseded_by_id = None
        db.query(DataCorrection).filter(
            DataCorrection.record_type == "assessment",
            DataCorrection.target_record_id == failing_asm.id,
        ).delete()
        db.commit()
        db.refresh(failing_asm)
        target_asm_id = failing_asm.id
        db.close()

        # 2. Teacher PROPOSES correction (data entry error: marks should be 84 instead of 24)
        prop_resp = await client.post(
            "/api/corrections",
            headers={"Authorization": f"Bearer {teacher_tok}"},
            json={
                "record_type": "assessment",
                "target_record_id": target_asm_id,
                "proposed_data": {
                    "marks_obtained": 84.0,
                    "max_marks": 100.0,
                },
                "reason": "Clerical data entry mistake: physical answer sheet verified as 84/100.",
            }
        )
        assert prop_resp.status_code == 201
        corr_id = prop_resp.json()["id"]
        assert prop_resp.json()["status"] == "Pending"

        # 3. TEACHER DIRECT CALL TO APPLY / DECIDE CORRECTION MUST BE REJECTED (HTTP 403)
        teacher_apply_resp = await client.post(
            f"/api/corrections/{corr_id}/decide",
            headers={"Authorization": f"Bearer {teacher_tok}"},
            json={"action": "approve"}
        )
        assert teacher_apply_resp.status_code == 403
        assert "Only an administrator can approve" in teacher_apply_resp.json()["detail"]

        # 4. Administrator APPROVES and APPLIES correction
        admin_apply_resp = await client.post(
            f"/api/corrections/{corr_id}/decide",
            headers={"Authorization": f"Bearer {admin_tok}"},
            json={"action": "approve"}
        )
        assert admin_apply_resp.status_code == 200
        decided_data = admin_apply_resp.json()
        assert decided_data["status"] == "Approved"
        superseding_id = decided_data["superseding_record_id"]
        assert superseding_id is not None

        # 5. Verify in DB: Original record preserved with is_superseded = True & link
        db = SessionLocal()
        orig_rec = db.query(AssessmentRecord).filter(AssessmentRecord.id == target_asm_id).first()
        assert orig_rec.is_superseded is True
        assert orig_rec.superseded_by_id == superseding_id
        assert orig_rec.marks_obtained == 24.0  # Original preserved!

        new_rec = db.query(AssessmentRecord).filter(AssessmentRecord.id == superseding_id).first()
        assert new_rec.is_superseded is False
        assert new_rec.marks_obtained == 84.0
        assert new_rec.percentage == 84.0

        # Verify old academic indicators for Kavitha are marked is_superseded = True (kept in history!)
        old_indicators = db.query(WarningIndicator).filter(
            WarningIndicator.student_id == student_id,
            WarningIndicator.category == "academic",
            WarningIndicator.is_superseded == True,
        ).all()
        assert len(old_indicators) > 0  # Historical indicators preserved!
        db.close()


# ---------------------------------------------------------------------------
# FEATURE 3: DATA QUALITY MONITOR ACCEPTANCE TEST
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_feature_3_data_quality_monitor():
    """ACCEPTANCE TEST F3:

    Importing a file with duplicate IDs and invalid marks produces the correct issue
    counts in the monitor, and the counts match the import error report.
    """
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        admin_tok = await get_token(client, "admin")

        # 1. Fetch baseline data quality issues
        initial_dq = await client.get("/api/data-quality/issues", headers={"Authorization": f"Bearer {admin_tok}"})
        assert initial_dq.status_code == 200
        initial_rejected = initial_dq.json()["summary"]["categories"]["import_rejected_rows"]["count"]

        # 2. Upload an import file containing:
        # - Row 1: Valid new student
        # - Row 2: Duplicate ID in same file (rejected)
        # - Row 3: Missing required student name (rejected)
        # - Row 4: Invalid marks / fields (rejected)
        import time
        ts = int(time.time()) % 100000
        emis_unique = f"33280{ts:05d}8"

        csv_payload = (
            "emis_id,full_name,grade,section,gender,guardian_name,guardian_phone\n"
            f"{emis_unique},Karan T,10,A,Male,Thangavel K,9842100055\n"
            f"{emis_unique},Karan Duplicate,10,A,Male,Thangavel K,9842100055\n"
            f"33280{ts:05d}9,,10,B,Female,Suresh P,9842100056\n"
            f"33280{ts:05d}0,Gita R,99,Z,InvalidGender,Ramesh S,123\n"
        )
        files = {"file": ("quality_test.csv", csv_payload.encode("utf-8"), "text/csv")}

        preview_resp = await client.post(
            "/api/import/upload",
            headers={"Authorization": f"Bearer {admin_tok}"},
            files=files,
            data={"import_type": "students"},
        )
        assert preview_resp.status_code == 200
        preview_data = preview_resp.json()
        assert preview_data["rejected_count"] >= 2  # rows rejected
        assert preview_data["duplicates_count"] >= 1 # duplicate rows in file

        # Commit batch to persist rejection logs in DB
        commit_resp = await client.post(
            f"/api/import/{preview_data['batch_id']}/confirm",
            headers={"Authorization": f"Bearer {admin_tok}"},
        )
        assert commit_resp.status_code == 200
        import_rejected_in_batch = commit_resp.json()["rejected_count"]

        # 3. Check Data Quality Monitor: rejected count must match import report
        updated_dq = await client.get("/api/data-quality/issues", headers={"Authorization": f"Bearer {admin_tok}"})
        assert updated_dq.status_code == 200
        new_rejected = updated_dq.json()["summary"]["categories"]["import_rejected_rows"]["count"]

        # Newly rejected issues in data quality monitor match exactly the import errors
        assert new_rejected == initial_rejected + import_rejected_in_batch

        # Verify summary counts and percentage calculations exist without artificial scores
        summary = updated_dq.json()["summary"]
        assert "profile_completeness_pct" in summary
        assert "attendance_completeness_pct" in summary
        assert 0.0 <= summary["profile_completeness_pct"] <= 100.0


# ---------------------------------------------------------------------------
# FEATURE 5: STUDENT SUPPORT HISTORY ACCEPTANCE TEST
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_feature_5_student_support_history_privacy():
    """ACCEPTANCE TEST F5:

    A teacher cannot see counselling notes for any student, confirmed by a direct API call
    as well as the UI. An assigned counsellor can.
    """
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        teacher_tok = await get_token(client, "teacher")
        counsellor_tok = await get_token(client, "counsellor")
        admin_tok = await get_token(client, "admin")

        # 1. Get Kavitha (Grade 10-B, taught by Teacher Revathi)
        db = SessionLocal()
        kavitha = db.query(Student).filter(Student.emis_id == "3328014490").first()
        student_id = kavitha.id
        db.close()

        # 2. Get counsellor ID and create a case assigned to this counsellor
        counsellor_me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {counsellor_tok}"})
        counsellor_id = counsellor_me.json()["id"]

        case_resp = await client.post(
            "/api/cases",
            headers={"Authorization": f"Bearer {teacher_tok}"},
            json={
                "student_id": student_id,
                "assigned_staff_id": counsellor_id,
                "category": "academic",
                "priority": "High",
                "reason": "Support case for confidential notes test.",
            }
        )
        assert case_resp.status_code == 201
        case_id = case_resp.json()["id"]

        confidential_text = "CONFIDENTIAL COUNSELLING: Student disclosed sensitive personal family circumstance."
        note_resp = await client.post(
            f"/api/cases/{case_id}/notes",
            headers={"Authorization": f"Bearer {counsellor_tok}"},
            json={
                "note_text": confidential_text,
                "is_sensitive": True,
            }
        )
        assert note_resp.status_code == 201

        # 3. COUNSELLOR QUERIES TIMELINE DIRECT API: Must see confidential counselling note
        c_tl_resp = await client.get(
            f"/api/students/{student_id}/timeline",
            headers={"Authorization": f"Bearer {counsellor_tok}"}
        )
        assert c_tl_resp.status_code == 200
        c_events = c_tl_resp.json()["events"]
        c_notes = [e for e in c_events if e["event_type"] == "case_note" and e["is_confidential"] is True]
        assert len(c_notes) > 0
        assert any(confidential_text in n["description"] for n in c_notes)

        # 4. TEACHER QUERIES TIMELINE DIRECT API: MUST NOT SEE CONFIDENTIAL COUNSELLING NOTE!
        t_tl_resp = await client.get(
            f"/api/students/{student_id}/timeline",
            headers={"Authorization": f"Bearer {teacher_tok}"}
        )
        assert t_tl_resp.status_code == 200
        t_events = t_tl_resp.json()["events"]
        # Direct assertion: No event may have is_confidential=True and confidential text cannot appear
        for ev in t_events:
            assert ev.get("is_confidential") is not True
            assert confidential_text not in ev.get("description", "")

        # 5. TEACHER DIRECT API CALL TO /api/cases/{case_id}: Must also redact sensitive notes
        t_case_resp = await client.get(
            f"/api/cases/{case_id}",
            headers={"Authorization": f"Bearer {teacher_tok}"}
        )
        assert t_case_resp.status_code == 200
        t_case_notes = t_case_resp.json()["case_notes"]
        assert not any(n["is_sensitive"] for n in t_case_notes)
        assert not any(confidential_text in n["note_text"] for n in t_case_notes)
