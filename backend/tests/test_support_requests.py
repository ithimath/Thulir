"""Integration tests for Student Support Requests (Stretch 1)."""
import pytest
import httpx
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.services.seed_service import seed_demo_data

@pytest.fixture(scope="module", autouse=True)
def init_db():
    db = SessionLocal()
    seed_demo_data(db, force=True)
    db.close()

_TOKEN = None

async def get_teacher_token(client: httpx.AsyncClient) -> str:
    global _TOKEN
    if not _TOKEN:
        resp = await client.post("/api/auth/login", json={"username": "teacher", "password": "Password123!"})
        _TOKEN = resp.json()["token"]
    return _TOKEN

@pytest.mark.asyncio
async def test_student_support_request_intake_tracking_and_escalation():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        token = await get_teacher_token(client)

        # 1. Lookup Kavitha (Grade 10-B)
        stu_resp = await client.get("/api/students?search=Kavitha", headers={"Authorization": f"Bearer {token}"})
        assert stu_resp.status_code == 200
        kavitha = stu_resp.json()["items"][0]

        # 2. Staff assisted intake: Teacher logs a support request on student's behalf
        create_resp = await client.post(
            "/api/support-requests",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "student_id": kavitha["id"],
                "requester_type": "student_direct",
                "support_domain": "attendance_travel",
                "urgency_level": "priority",
                "description": "Student shared difficulties with bus route timing leading to morning tardiness.",
                "intake_notes": "Student requested bus pass renewal assistance.",
            }
        )
        assert create_resp.status_code == 201
        data = create_resp.json()
        assert "SSR-" in data["tracking_number"]
        assert data["status"] == "Submitted"
        tracking_code = data["tracking_number"]
        ssr_id = data["id"]

        # 3. Anonymous tracking verification (unauthenticated student/parent query)
        track_resp = await client.get(f"/api/support-requests/track/{tracking_code}")
        assert track_resp.status_code == 200
        track_info = track_resp.json()
        assert track_info["tracking_number"] == tracking_code
        assert track_info["status"] == "Submitted"
        assert "student" not in track_info # Anonymity check: no sensitive student fields exposed
        assert "queued for staff review" in track_info["status_explanation"]

        # 4. Link to case / escalate to full Support Case
        link_resp = await client.post(
            f"/api/support-requests/{ssr_id}/link-case",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "category": "attendance",
                "priority": "High",
                "reason": "Escalated from Support Request: Bus pass renewal and schedule adjustment."
            }
        )
        assert link_resp.status_code == 200
        assert link_resp.json()["status"] == "Linked to Case"

        # 5. Re-check tracking status
        track_updated = await client.get(f"/api/support-requests/track/{tracking_code}")
        assert track_updated.status_code == 200
        assert track_updated.json()["status"] == "Linked to Case"
        assert track_updated.json()["case_linked"] is True

