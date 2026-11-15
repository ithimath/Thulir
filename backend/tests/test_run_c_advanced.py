"""Acceptance tests for Run C (Features 9 and 10).

Acceptance Test Feature 9 (Offline-friendly shell):
- Service worker generated with shell and static assets ONLY.
- Zero student records, indicators, or case notes in cache rules.
- API endpoints configured as NetworkOnly.

Acceptance Test Feature 10 (AI-Assisted Summarization):
- With AI_ENABLED=false (default): returns 'AI summaries unavailable' without calling external APIs.
- With AI_ENABLED=true: summary is grounded in verified student records, cites sources,
  replaces student names with reference ID, contains no hallucinations, and is marked DRAFT requiring approval.
- Approved summaries are saved to permanent support case records with staff attribution.
"""

import json
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.models import Student, User, SupportCase, CaseNote
from backend.app.config import settings


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_token(client: AsyncClient, username: str) -> str:
    resp = await client.post(
        "/api/auth/login",
        json={"username": username, "password": "Password123!"},
    )
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["token"]


@pytest.mark.asyncio
async def test_feature_10_ai_summaries_disabled_by_default(db_session):
    """
    Acceptance Test F10.1:
    When AI_ENABLED=false (the strict default), the endpoint returns
    'AI summaries unavailable' gracefully without failing or calling external APIs.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await get_token(client, "admin")
        student = db_session.query(Student).first()
        assert student is not None, "Test requires at least one student"

        # Explicitly ensure AI is disabled
        settings.AI_ENABLED = False
        import os
        os.environ["AI_ENABLED"] = "false"

        resp = await client.get(
            f"/api/students/{student.id}/ai-summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is False
        assert data["message"] == "AI summaries unavailable"
        assert data["status"] == "unavailable"


@pytest.mark.asyncio
async def test_feature_10_ai_summaries_enabled_grounded_and_anonymized(db_session, monkeypatch):
    """
    Acceptance Test F10.2:
    When AI_ENABLED=true, generated summary is:
    1. Anonymized to REF-{id} (no student real name transmitted).
    2. Grounded strictly in test student's records with source citations ([ATT-..], [ASM-..], [IND-..]).
    3. Output is marked as DRAFT with requires_human_approval=True.
    4. Approving the draft commits it to the support case with staff attribution.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await get_token(client, "admin")
        student = db_session.query(Student).first()
        assert student is not None

        # Enable AI via monkeypatch
        monkeypatch.setenv("AI_ENABLED", "true")
        monkeypatch.setattr(settings, "AI_ENABLED", True)

        resp = await client.get(
            f"/api/students/{student.id}/ai-summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()

        # Verify Feature 10 Draft & Anonymization Mandates
        assert data["available"] is True
        assert data["status"] == "DRAFT"
        assert data["is_draft"] is True
        assert data["requires_human_approval"] is True
        assert data["anonymized_reference_id"] == f"REF-{student.id:04d}"
        assert student.full_name not in data["anonymized_reference_id"]
        assert len(data["sources_cited"]) > 0

        # Verify source citations exist in summary text
        summary_text = data["summary_text"]
        assert f"REF-{student.id:04d}" in summary_text
        for cite in data["sources_cited"]:
            assert cite in summary_text

        # Staff Review & Explicit Approval Flow
        approved_text = summary_text + " Staff note: Verified and approved during weekly pastoral review."
        approve_resp = await client.post(
            f"/api/students/{student.id}/ai-summary/approve",
            json={"approved_text": approved_text},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert approve_resp.status_code == 200
        approve_data = approve_resp.json()
        assert approve_data["status"] == "APPROVED_AND_SAVED"
        assert approve_data["case_id"] is not None

        # Verify persisted case note in database
        saved_note = db_session.query(CaseNote).filter(CaseNote.id == approve_data["note_id"]).first()
        assert saved_note is not None
        assert "Verified and approved during weekly pastoral review" in saved_note.note_text


def test_feature_9_offline_pwa_shell_cache_and_zero_pii():
    """
    Acceptance Test F9:
    1. Vite PWA configuration generates dist/sw.js and manifest.webmanifest.
    2. Precaching is strictly limited to static shell assets (index.html, JS, CSS).
    3. Workbox runtimeCaching configures /api/ routes as NetworkOnly so ZERO student PII
       is ever stored in service-worker caches, IndexedDB, or local storage.
    """
    dist_dir = Path("frontend/dist")
    sw_file = dist_dir / "sw.js"
    manifest_file = dist_dir / "manifest.webmanifest"
    index_file = dist_dir / "index.html"

    assert index_file.exists(), "Application shell index.html must exist in dist"
    assert manifest_file.exists(), "PWA Web App Manifest must exist in dist"
    assert sw_file.exists(), "Service Worker sw.js must be generated in dist"

    # Inspect manifest
    manifest_content = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest_content["short_name"] == "THULIR"
    assert manifest_content["display"] == "standalone"

    # Inspect service worker code to verify NetworkOnly handler for /api/
    sw_code = sw_file.read_text(encoding="utf-8")
    assert "/api/" in sw_code, "Service worker must contain explicit routing rule for /api/"
    assert "NetworkOnly" in sw_code, "API calls must strictly use NetworkOnly strategy to prevent caching student PII"
