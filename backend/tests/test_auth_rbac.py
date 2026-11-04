import pytest
import httpx
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.services.seed_service import seed_demo_data

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    db = SessionLocal()
    seed_demo_data(db, force=True)
    db.close()

@pytest.fixture
async def async_client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

@pytest.mark.asyncio
async def test_health_check(async_client):
    res = await async_client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_login_success_admin(async_client):
    res = await async_client.post("/api/auth/login", json={"username": "admin", "password": "Password123!"})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["username"] == "admin"
    assert data["user"]["current_role"]["role"] == "admin"
    assert "token" in data
    assert "thulir_session" in res.cookies

@pytest.mark.asyncio
async def test_login_invalid_password_returns_401(async_client):
    res = await async_client.post("/api/auth/login", json={"username": "admin", "password": "WrongPassword"})
    assert res.status_code == 401
    assert "Invalid username or password" in res.json()["detail"]

@pytest.mark.asyncio
async def test_unauthenticated_me_returns_401(async_client):
    res = await async_client.get("/api/auth/me")
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_authenticated_me_returns_profile(async_client):
    res = await async_client.post("/api/auth/login", json={"username": "teacher", "password": "Password123!"})
    assert res.status_code == 200
    token = res.json()["token"]

    me_res = await async_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["username"] == "teacher"
    assert me_data["current_role"]["role"] == "teacher"
    assert me_data["current_role"]["assigned_classes"] == "10-B,10-A"

@pytest.mark.asyncio
async def test_authenticated_counsellor_role(async_client):
    res = await async_client.post("/api/auth/login", json={"username": "counsellor", "password": "Password123!"})
    assert res.status_code == 200
    assert res.json()["user"]["current_role"]["role"] == "counsellor"

@pytest.mark.asyncio
async def test_logout_clears_session(async_client):
    login_res = await async_client.post("/api/auth/login", json={"username": "admin", "password": "Password123!"})
    token = login_res.json()["token"]
    
    logout_res = await async_client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200
    assert "thulir_session" not in logout_res.cookies or logout_res.cookies["thulir_session"] == ""
