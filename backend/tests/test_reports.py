"""Integration tests for Reports & Dashboard aggregations (Phase 8)."""
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

async def get_admin_token(client: httpx.AsyncClient) -> str:
    global _TOKEN
    if not _TOKEN:
        resp = await client.post("/api/auth/login", json={"username": "admin", "password": "Password123!"})
        _TOKEN = resp.json()["token"]
    return _TOKEN

@pytest.mark.asyncio
async def test_dashboard_aggregations_and_trajectory():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        token = await get_admin_token(client)

        # 1. Dashboard stats
        resp = await client.get("/api/reports/dashboard-stats", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        stats = resp.json()
        assert stats["total_enrolled"] >= 20
        assert "indicators_by_category" in stats
        assert "interventions_by_type" in stats

        # 2. Trajectory data
        traj_resp = await client.get("/api/reports/trajectory", headers={"Authorization": f"Bearer {token}"})
        assert traj_resp.status_code == 200
        data = traj_resp.json()
        assert "trajectory" in data
        assert len(data["trajectory"]) >= 1

        # 3. Export CSV - students_review
        export_resp = await client.get("/api/reports/export?report_type=students_review", headers={"Authorization": f"Bearer {token}"})
        assert export_resp.status_code == 200
        assert "text/csv" in export_resp.headers["content-type"]
        assert "EMIS_ID,Student_Name" in export_resp.text

        # 4. Export CSV - cases_summary
        cases_resp = await client.get("/api/reports/export?report_type=cases_summary", headers={"Authorization": f"Bearer {token}"})
        assert cases_resp.status_code == 200
        assert "Case_Number,EMIS_ID" in cases_resp.text

        # 5. Export CSV - interventions_log
        interventions_resp = await client.get("/api/reports/export?report_type=interventions_log", headers={"Authorization": f"Bearer {token}"})
        assert interventions_resp.status_code == 200
        assert "Case_Number,EMIS_ID,Student_Name,Intervention_Type" in interventions_resp.text

        # 6. Export CSV - attendance_summary
        att_resp = await client.get("/api/reports/export?report_type=attendance_summary", headers={"Authorization": f"Bearer {token}"})
        assert att_resp.status_code == 200
        assert "EMIS_ID,Student_Name,Grade,Section" in att_resp.text
        assert "Below_75_Flag" in att_resp.text

