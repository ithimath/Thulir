"""Integration tests for Data Import pipeline (Phase 4)."""
import pytest
import time
import httpx
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.services.seed_service import seed_demo_data
from backend.app.models.models import Student, ImportBatch

@pytest.fixture(scope="module", autouse=True)
def init_db():
    db = SessionLocal()
    seed_demo_data(db, force=True)
    db.close()

# Shared token
_TOKEN = None

async def get_admin_token(client: httpx.AsyncClient) -> str:
    global _TOKEN
    if not _TOKEN:
        resp = await client.post("/api/auth/login", json={"username": "admin", "password": "Password123!"})
        _TOKEN = resp.json()["token"]
    return _TOKEN

@pytest.mark.asyncio
async def test_import_students_csv_preview_and_commit():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        token = await get_admin_token(client)

        ts = int(time.time()) % 100000
        emis1 = f"33280{ts:05d}1"
        emis2 = f"33280{ts:05d}2"

        # Create synthetic CSV with unique EMIS IDs:
        # Row 1: Valid new student
        # Row 2: Valid new student
        # Row 3: Duplicate of Row 2 in same file
        # Row 4: Missing student name (rejected)
        # Row 5: Existing student Kavitha M (updated_existing)
        csv_content = (
            "emis_id,full_name,grade,section,gender,guardian_name,guardian_phone\n"
            f"{emis1},Manoj Kumar,10,A,Male,Kumar M,9842100099\n"
            f"{emis2},Swetha R,10,B,Female,Ravi P,9842100098\n"
            f"{emis2},Swetha R,10,B,Female,Ravi P,9842100098\n"
            "3328099003,,10,A,Female,Gopal V,9842100097\n"
            "3328014490,Kavitha M.,10,B,Female,Mani K.,9842100001\n"
        )

        files = {"file": ("students_test.csv", csv_content.encode("utf-8"), "text/csv")}
        data = {"import_type": "students"}

        # 1. Upload & Preview
        resp = await client.post(
            "/api/import/upload",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data,
        )
        assert resp.status_code == 200
        preview = resp.json()
        assert preview["total_rows"] == 5
        assert preview["valid_count"] == 2
        assert preview["duplicates_count"] == 1
        assert preview["rejected_count"] == 1
        assert preview["warnings_count"] == 1 # Kavitha already exists
        batch_id = preview["batch_id"]

        # 2. Confirm Commit
        commit_resp = await client.post(
            f"/api/import/{batch_id}/confirm",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert commit_resp.status_code == 200
        commit_data = commit_resp.json()
        assert commit_data["status"] == "committed"
        assert commit_data["imported_count"] == 2
        assert commit_data["duplicates_count"] == 1
        assert commit_data["rejected_count"] == 2 # 1 missing name + 1 file duplicate

        # 3. Verify newly imported student exists in student directory
        check_stu = await client.get(f"/api/students?search={emis1}", headers={"Authorization": f"Bearer {token}"})
        assert check_stu.status_code == 200
        assert check_stu.json()["total"] == 1
        assert check_stu.json()["items"][0]["full_name"] == "Manoj Kumar"

        # 4. Check Import History
        hist_resp = await client.get("/api/import/history", headers={"Authorization": f"Bearer {token}"})
        assert hist_resp.status_code == 200
        batches = hist_resp.json()
        assert any(b["id"] == batch_id and b["status"] == "committed" for b in batches)

        # 5. Check Row Results Audit Log
        row_res = await client.get(f"/api/import/{batch_id}/results", headers={"Authorization": f"Bearer {token}"})
        assert row_res.status_code == 200
        rows = row_res.json()
        assert len(rows) == 5

@pytest.mark.asyncio
async def test_import_with_header_aliases_and_spaces():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        token = await get_admin_token(client)

        ts = int(time.time() * 1000) % 1000000
        emis_alias = f"33280{ts:06d}"

        # CSV with real-world school column variations: "EMIS No", "Student Name", "Class", "Section"
        csv_content = (
            "EMIS No,Student Name,Class,Section,Gender\n"
            f"{emis_alias},Praveen Kumar,10,A,Male\n"
        )
        files = {"file": ("students_aliased.csv", csv_content.encode("utf-8"), "text/csv")}
        data = {"import_type": "students"}

        resp = await client.post(
            "/api/import/upload",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data,
        )
        assert resp.status_code == 200
        preview = resp.json()
        assert preview["valid_count"] == 1
        batch_id = preview["batch_id"]

        commit_resp = await client.post(
            f"/api/import/{batch_id}/confirm",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert commit_resp.status_code == 200
        assert commit_resp.json()["imported_count"] == 1

@pytest.mark.asyncio
async def test_teacher_cannot_upload_import():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        # Teacher login
        resp = await client.post("/api/auth/login", json={"username": "teacher", "password": "Password123!"})
        teacher_token = resp.json()["token"]

        files = {"file": ("test.csv", b"dummy", "text/csv")}
        res = await client.post(
            "/api/import/upload",
            headers={"Authorization": f"Bearer {teacher_token}"},
            files=files,
            data={"import_type": "students"},
        )
        assert res.status_code == 403 # Only Admin can import!
