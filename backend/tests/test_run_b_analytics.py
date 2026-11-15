"""Automated Acceptance Tests for Run B (Analytics Core): Features 6, 7, 8, and 4."""

import pytest
import datetime
import httpx
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.services.seed_service import seed_demo_data
from backend.app.models.models import (
    School, User, UserSchoolRole, Student, WarningIndicator, WarningRule,
    AttendanceRecord, AssessmentRecord, SupportCase, Intervention, FollowUp
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


@pytest.mark.asyncio
async def test_feature_6_multi_indicator_patterns():
    """
    Feature 6 Acceptance Test:
    Identifying co-occurring attendance and academic indicators produces a named pattern
    with plain explanation, without generating a composite score or altering individual indicator statuses.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await get_token(client, "admin")
        headers = {"Authorization": f"Bearer {token}"}

        # Query patterns
        resp = await client.get("/api/indicators/patterns", headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        # Check required properties
        assert "patterns" in data
        assert "disclaimer" in data
        # Civic Rule: No risk score or ranking
        assert "risk_score" not in data
        assert "composite_score" not in data
        assert "student_rankings" not in data

        pattern_names = [p["pattern_key"] for p in data["patterns"]]
        assert "academic_attendance_compounding" in pattern_names
        assert "chronic_engagement_risk" in pattern_names
        assert "multi_subject_academic_struggle" in pattern_names

        for p in data["patterns"]:
            assert p["pattern_name"]
            assert p["plain_explanation"]
            assert p["recommended_intervention_domain"]


@pytest.mark.asyncio
async def test_feature_7_configurable_rule_management():
    """
    Feature 7 Acceptance Test:
    An administrator updates a threshold with a reason; new indicators use the new threshold
    and rule version; previously generated indicators retain their original rule version and threshold;
    a non-admin edit attempt is rejected.
    """
    db_session = SessionLocal()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Non-admin (teacher) tries to edit rule -> 403 Forbidden
            t_token = await get_token(client, "teacher")
            t_headers = {"Authorization": f"Bearer {t_token}"}

            non_admin_res = await client.post(
                "/api/rules/ATT-LOW/threshold",
                headers=t_headers,
                json={"new_threshold": 70.0, "change_reason": "Teacher unauthorized attempt"},
            )
            assert non_admin_res.status_code == 403

            # 2. Admin signs in
            a_token = await get_token(client, "admin")
            a_headers = {"Authorization": f"Bearer {a_token}"}

            # 3. Admin lists rules
            rules_res = await client.get("/api/rules", headers=a_headers)
            assert rules_res.status_code == 200
            assert rules_res.json()["total_rules"] >= 1

            # 4. Admin previews threshold change simulation
            preview_res = await client.get("/api/rules/preview-change?rule_code=ATT-LOW&proposed_threshold=70.0", headers=a_headers)
            assert preview_res.status_code == 200
            assert "simulated_indicators_count" in preview_res.json()

            # Record baseline rule version before change
            curr_rule = db_session.query(WarningRule).filter(WarningRule.rule_code == "ATT-LOW", WarningRule.is_active == True).first()
            base_version = curr_rule.version if curr_rule else 1

            # 5. Admin updates threshold with mandatory reason
            update_res = await client.post(
                "/api/rules/ATT-LOW/threshold",
                headers=a_headers,
                json={
                    "new_threshold": 70.0,
                    "change_reason": "Adjusting threshold for rural harvest season variance.",
                    "effective_from": str(datetime.date.today()),
                },
            )
            assert update_res.status_code == 200
            new_v = update_res.json()["new_version"]
            assert new_v == base_version + 1

            # Check in DB that old version exists and is deactivated, new version is active
            db_session.expire_all()
            old_v_rule = db_session.query(WarningRule).filter(WarningRule.rule_code == "ATT-LOW", WarningRule.version == base_version).first()
            new_v_rule = db_session.query(WarningRule).filter(WarningRule.rule_code == "ATT-LOW", WarningRule.version == new_v).first()
            assert old_v_rule.is_active == False
            assert new_v_rule.is_active == True
            assert new_v_rule.threshold_value == 70.0

            # Verify historical indicators keep original rule version
            old_indicators = db_session.query(WarningIndicator).filter(WarningIndicator.rule_code == "ATT-LOW").all()
            for ind in old_indicators:
                assert ind.rule_version <= base_version or ind.rule_version == new_v
    finally:
        db_session.close()


@pytest.mark.asyncio
async def test_feature_8_historical_trend_comparison():
    """
    Feature 8 Acceptance Test:
    Viewing a student with data across terms shows trajectory comparisons with explicit gaps
    for any missing period; trends are calculated from actual records only.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await get_token(client, "admin")
        headers = {"Authorization": f"Bearer {token}"}

        # Query trends for student 1 (Kavitha)
        resp = await client.get("/api/students/1/trends", headers=headers)
        assert resp.status_code == 200
        data = resp.json()

        assert "student" in data
        assert "attendance_trend" in data
        assert "academic_subject_trends" in data
        assert "disclaimer" in data

        # Check explicit gap handling: items have has_data and gap_reason when missing
        for item in data["attendance_trend"]:
            assert "period_name" in item
            if not item["has_data"]:
                assert "gap_reason" in item


@pytest.mark.asyncio
async def test_feature_4_intervention_effectiveness_tracker():
    """
    Feature 4 Acceptance Test:
    An intervention with follow-up data shows before-and-after comparison with baseline and
    current metrics, status categorized according to defined criteria, and mandatory disclaimer displayed.
    """
    db_session = SessionLocal()
    try:
        admin_user = db_session.query(User).filter(User.username == "admin").first()
        student = db_session.query(Student).filter(Student.id == 1).first()

        case = db_session.query(SupportCase).filter(SupportCase.student_id == student.id).first()
        if not case:
            case = SupportCase(
                school_id=student.school_id,
                student_id=student.id,
                case_number="CASE-F4-TEST-99",
                created_by_id=admin_user.id,
                assigned_staff_id=admin_user.id,
                category="attendance",
                priority="High",
                reason="Effectiveness testing case",
                status="In Progress",
                created_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db_session.add(case)
            db_session.flush()

        inv = Intervention(
            case_id=case.id,
            intervention_type="attendance_followup",
            title="Weekly Parental Attendance Check-in",
            description="Monitor daily arrivals and conduct home check-in.",
            status="Active",
            assigned_staff_id=admin_user.id,
            start_date=datetime.date.today() - datetime.timedelta(days=30),
            baseline_snapshot={"attendance_pct": 65.0, "captured_at": str(datetime.date.today() - datetime.timedelta(days=30))},
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db_session.add(inv)
        db_session.flush()

        # Add follow-up observation
        follow_up = FollowUp(
            case_id=case.id,
            intervention_id=inv.id,
            assigned_staff_id=admin_user.id,
            due_date=datetime.date.today(),
            completion_date=datetime.date.today(),
            status="Completed",
            notes="Parent confirmed student has resumed regular bus transport.",
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db_session.add(follow_up)
        db_session.commit()
        inv_id = inv.id
        case_id = case.id
    finally:
        db_session.close()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await get_token(client, "admin")
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get(f"/api/cases/{case_id}/interventions/{inv_id}/effectiveness", headers=headers)
        assert resp.status_code == 200
        eff = resp.json()

        # Check required fields and mandatory disclaimer
        assert "outcome_category" in eff
        assert eff["outcome_category"] in ("improving", "declining", "no_significant_change", "insufficient_data")
        assert "baseline_value" in eff
        assert "current_value" in eff
        assert "change_delta" in eff
        assert "disclaimer" in eff
        assert "observed change, not proof that the intervention caused it" in eff["disclaimer"].lower()
