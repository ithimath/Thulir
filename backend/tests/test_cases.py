"""Integration tests for Support Cases, Interventions, Follow-ups, and Case Notes (Phase 7)."""
import pytest
import datetime
import httpx
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.services.seed_service import seed_demo_data
from backend.app.models.models import Student, User

@pytest.fixture(scope="module", autouse=True)
def init_db():
    db = SessionLocal()
    seed_demo_data(db, force=True)
    db.close()

async def get_auth_token(client: httpx.AsyncClient, username: str, password: str = "Password123!"):
    resp = await client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return resp.json()["token"]

@pytest.mark.asyncio
async def test_case_lifecycle_and_confidential_notes():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        admin_token = await get_auth_token(client, "admin")
        teacher_token = await get_auth_token(client, "teacher")
        counsellor_token = await get_auth_token(client, "counsellor")

        # 1. Get Kavitha (Grade 10-B) & Counsellor Meenakshi's ID
        stu_resp = await client.get("/api/students?search=Kavitha", headers={"Authorization": f"Bearer {admin_token}"})
        stu_json = stu_resp.json()
        print("STUDENTS RESPONSE:", stu_resp.status_code, stu_json)
        kavitha = stu_json["items"][0]
        
        counsellor_me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {counsellor_token}"})
        counsellor_id = counsellor_me.json()["id"]

        # 2. Teacher Revathi creates a case for Kavitha (assigned to Counsellor)
        case_create_resp = await client.post(
            "/api/cases",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "student_id": kavitha["id"],
                "assigned_staff_id": counsellor_id,
                "category": "attendance",
                "priority": "High",
                "reason": "Sudden drop in attendance from 91% to 71% with unexcused absences.",
                "observations": "Student appeared withdrawn during math class.",
                "review_date": str(datetime.date.today() + datetime.timedelta(days=7))
            }
        )
        assert case_create_resp.status_code == 201
        case_data = case_create_resp.json()
        case_id = case_data["id"]
        assert "CAS-" in case_data["case_number"]

        # 3. Counsellor adds an Intervention
        interv_resp = await client.post(
            f"/api/cases/{case_id}/interventions",
            headers={"Authorization": f"Bearer {counsellor_token}"},
            json={
                "intervention_type": "attendance_followup",
                "title": "Home visit and guardian conference",
                "description": "Coordinate with guardian regarding morning commute and health reasons.",
                "assigned_staff_id": counsellor_id,
                "start_date": str(datetime.date.today()),
                "target_date": str(datetime.date.today() + datetime.timedelta(days=5)),
            }
        )
        assert interv_resp.status_code == 201
        interv_id = interv_resp.json()["id"]

        # 4. Counsellor adds a Follow-up
        fu_resp = await client.post(
            f"/api/cases/{case_id}/follow-ups",
            headers={"Authorization": f"Bearer {counsellor_token}"},
            json={
                "intervention_id": interv_id,
                "assigned_staff_id": counsellor_id,
                "due_date": str(datetime.date.today() + datetime.timedelta(days=3)),
                "notes": "Verify attendance register with class teacher."
            }
        )
        assert fu_resp.status_code == 201

        # 5. Counsellor adds two notes: one regular, one sensitive
        note_reg_resp = await client.post(
            f"/api/cases/{case_id}/notes",
            headers={"Authorization": f"Bearer {counsellor_token}"},
            json={
                "note_text": "Met student in office; student expressed desire to catch up on lessons.",
                "is_sensitive": False
            }
        )
        assert note_reg_resp.status_code == 201

        note_sens_resp = await client.post(
            f"/api/cases/{case_id}/notes",
            headers={"Authorization": f"Bearer {counsellor_token}"},
            json={
                "note_text": "CONFIDENTIAL: Guardian disclosed private domestic welfare hardship.",
                "is_sensitive": True
            }
        )
        assert note_sens_resp.status_code == 201

        # 6. Verify Counsellor sees both notes
        c_detail_resp = await client.get(f"/api/cases/{case_id}", headers={"Authorization": f"Bearer {counsellor_token}"})
        assert c_detail_resp.status_code == 200
        c_detail = c_detail_resp.json()
        assert len(c_detail["case_notes"]) == 2
        assert any(n["is_sensitive"] for n in c_detail["case_notes"])

        # 7. Verify Teacher sees only the non-sensitive note (sensitive note is redacted!)
        t_detail_resp = await client.get(f"/api/cases/{case_id}", headers={"Authorization": f"Bearer {teacher_token}"})
        assert t_detail_resp.status_code == 200
        t_detail = t_detail_resp.json()
        assert len(t_detail["case_notes"]) == 1
        assert not any(n["is_sensitive"] for n in t_detail["case_notes"])

        # 8. Verify Admin sees only non-sensitive notes by default
        a_detail_resp = await client.get(f"/api/cases/{case_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert a_detail_resp.status_code == 200
        a_detail = a_detail_resp.json()
        assert len(a_detail["case_notes"]) == 1
        assert not any(n["is_sensitive"] for n in a_detail["case_notes"])
