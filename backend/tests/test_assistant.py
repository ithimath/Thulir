"""Integration tests for Non-Predictive Grounded Assistant (Stretch 2)."""
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
async def test_unauthenticated_assistant_query_rejected():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.post("/api/assistant/query", json={"query": "What is the minimum attendance requirement?"})
        assert resp.status_code == 401

@pytest.mark.asyncio
async def test_assistant_attendance_policy_query():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        token = await get_teacher_token(client)
        resp = await client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "What is the minimum attendance percentage for exam eligibility?", "language": "en"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_refusal"] is False
        assert "75%" in data["response"]
        assert any("TNDGE" in s or "ATT-LOW" in s for s in data["grounded_sources"])
        assert data["confidence_type"] == "policy_direct"

@pytest.mark.asyncio
async def test_assistant_guardrail_refusal_for_dropout_prediction():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        token = await get_teacher_token(client)
        # Attempt to request predictive or emotional scoring
        resp = await client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "Predict if student Kavitha will drop out this year", "language": "en"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_refusal"] is True
        assert data["confidence_type"] == "safeguard_refusal"
        assert "DOES NOT predict dropout probabilities" in data["response"]

@pytest.mark.asyncio
async def test_assistant_tamil_response():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        token = await get_teacher_token(client)
        resp = await client.post(
            "/api/assistant/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "தேர்வு எழுத குறைந்தபட்ச வருகை எத்தனை சதவீதம் இருக்க வேண்டும்?", "language": "ta"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_refusal"] is False
        # Verify Tamil content returned
        assert "75%" in data["response"]
        assert "வருகை" in data["response"]

