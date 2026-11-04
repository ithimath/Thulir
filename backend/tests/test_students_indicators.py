"""Integration tests for Students and Indicators endpoints (Phase 3 & Phase 6 verification)."""
import pytest
import httpx
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.services.seed_service import seed_demo_data

# Run DB seed ONCE per test module, not on every test function
@pytest.fixture(scope="module", autouse=True)
def init_db():
    db = SessionLocal()
    seed_demo_data(db, force=True)
    db.close()

# Shared tokens across tests in this module
_TOKENS = {}

async def get_token(client: httpx.AsyncClient, username: str) -> str:
    if username not in _TOKENS:
        resp = await client.post("/api/auth/login", json={"username": username, "password": "Password123!"})
        assert resp.status_code == 200
        _TOKENS[username] = resp.json()["token"]
    return _TOKENS[username]

@pytest.mark.asyncio
async def test_students_list_admin():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        token = await get_token(client, "admin")
        resp = await client.get("/api/students", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 20
        assert len(data["items"]) >= 20
        first = data["items"][0]
        assert "emis_id" in first
        assert "full_name" in first

@pytest.mark.asyncio
async def test_students_teacher_class_scoping():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        token = await get_token(client, "teacher") # Assigned classes: 10-A, 10-B
        resp = await client.get("/api/students", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 7
        for s in data["items"]:
            sec = f"{s['class_section']['grade']}-{s['class_section']['section']}"
            assert sec in ["10-A", "10-B"]

@pytest.mark.asyncio
async def test_student_profile_and_access_control():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        admin_token = await get_token(client, "admin")
        teacher_token = await get_token(client, "teacher")

        # Get Kavitha M (Grade 10-B)
        resp = await client.get("/api/students?search=Kavitha", headers={"Authorization": f"Bearer {admin_token}"})
        kavitha_id = resp.json()["items"][0]["id"]

        # Admin can view profile
        resp_adm = await client.get(f"/api/students/{kavitha_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp_adm.status_code == 200
        profile = resp_adm.json()
        assert profile["full_name"] == "Kavitha M."
        assert len(profile["attendance_history"]) >= 2
        assert len(profile["assessment_history"]) >= 3

        # Teacher Revathi teaches 10-B -> can view
        resp_t = await client.get(f"/api/students/{kavitha_id}", headers={"Authorization": f"Bearer {teacher_token}"})
        assert resp_t.status_code == 200

        # Now check Vignesh S (Grade 9-C) -> Teacher should be FORBIDDEN (403)
        resp_vig = await client.get("/api/students?search=Vignesh", headers={"Authorization": f"Bearer {admin_token}"})
        vignesh_id = resp_vig.json()["items"][0]["id"]

        resp_t_vig = await client.get(f"/api/students/{vignesh_id}", headers={"Authorization": f"Bearer {teacher_token}"})
        assert resp_t_vig.status_code == 403

@pytest.mark.asyncio
async def test_run_engine_and_review_queue():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        admin_token = await get_token(client, "admin")

        # 1. Trigger Warning Engine
        engine_resp = await client.post("/api/indicators/run-engine", headers={"Authorization": f"Bearer {admin_token}"})
        assert engine_resp.status_code == 200
        res = engine_resp.json()
        assert res["students_checked"] >= 20

        # 2. Check Indicators Review Queue (contains at least the 4 triggered indicators)
        ind_resp = await client.get("/api/indicators", headers={"Authorization": f"Bearer {admin_token}"})
        assert ind_resp.status_code == 200
        ind_data = ind_resp.json()
        assert ind_data["total"] >= 4

        # Query an indicator with 'Needs Review' status
        nr_resp = await client.get("/api/indicators?status=Needs+Review", headers={"Authorization": f"Bearer {admin_token}"})
        assert nr_resp.status_code == 200
        nr_items = nr_resp.json()["items"]
        if nr_items:
            first_ind = nr_items[0]
            ind_detail = await client.get(f"/api/indicators/{first_ind['id']}", headers={"Authorization": f"Bearer {admin_token}"})
            assert ind_detail.status_code == 200
            detail = ind_detail.json()
            assert detail["plain_explanation"] != ""
            assert detail["supporting_evidence"] is not None
            assert detail["status"] == "Needs Review"

            # 3. Transition status from 'Needs Review' -> 'Under Review'
            review_resp = await client.post(
                f"/api/indicators/{first_ind['id']}/review",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "new_status": "Under Review",
                    "review_notes": "Discussed with class teacher, reviewing recent absences."
                }
            )
            assert review_resp.status_code == 200
            assert review_resp.json()["new_status"] == "Under Review"

            # Verify invalid status transition rejected
            invalid_rev = await client.post(
                f"/api/indicators/{first_ind['id']}/review",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "new_status": "Open", # Not a valid indicator status
                    "review_notes": "Invalid"
                }
            )
            assert invalid_rev.status_code in [400, 422]
