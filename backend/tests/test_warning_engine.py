"""
Pure unit tests for the warning engine rule functions.
These tests do NOT touch the database — they test the pure Python rule functions
using in-memory data, covering boundary cases for all 7 rules.
"""
import datetime
import pytest

from backend.app.services.warning_engine import (
    check_att_low,
    check_att_decline,
    check_att_consec,
    check_mark_low,
    check_mark_decline,
    check_asg_low,
    check_asg_decline,
)


# ===========================================================================
# ATT-LOW  (threshold: strictly < 75.0)
# ===========================================================================

class TestAttLow:
    def test_no_data_returns_none(self):
        assert check_att_low([]) is None

    def test_exactly_75_does_not_trigger(self):
        # Exactly 75% must NOT trigger
        assert check_att_low([("Term I", 75.0, 100.0, 75.0)]) is None

    def test_just_below_75_triggers(self):
        result = check_att_low([("Term I", 74.0, 100.0, 74.0)])
        assert result is not None
        assert result.rule_code == "ATT-LOW"
        assert result.threshold_applied == 75.0

    def test_71_pct_triggers(self):
        # Kavitha's data: 71.05%
        result = check_att_low([("Term I", 91.0, 100.0, 91.0), ("Term II", 54.0, 76.0, 71.05)])
        assert result is not None
        assert result.supporting_evidence["period"] == "Term II"
        assert result.supporting_evidence["attendance_pct"] == pytest.approx(71.05)

    def test_zero_total_days_skipped(self):
        # Period with 0 total days must be skipped — cannot compute
        assert check_att_low([("Term I", 0.0, 0.0, 0.0)]) is None

    def test_uses_latest_period(self):
        # Even if earlier period is low, only the latest triggers
        result = check_att_low([("Term I", 50.0, 100.0, 50.0), ("Term II", 80.0, 100.0, 80.0)])
        assert result is None  # Latest (Term II, 80%) is fine


# ===========================================================================
# ATT-DECLINE  (threshold: drop >= 10.0 pp)
# ===========================================================================

class TestAttDecline:
    def test_no_data_returns_none(self):
        assert check_att_decline([]) is None

    def test_single_period_returns_none(self):
        assert check_att_decline([("Term I", 70.0, 100.0, 70.0)]) is None

    def test_exactly_10pp_drop_triggers(self):
        # Exactly 10 pp must trigger
        result = check_att_decline([("Term I", 90.0, 100.0, 90.0), ("Term II", 80.0, 100.0, 80.0)])
        assert result is not None
        assert result.rule_code == "ATT-DECLINE"
        assert result.supporting_evidence["drop_pp"] == pytest.approx(10.0)

    def test_just_under_10pp_does_not_trigger(self):
        result = check_att_decline([("Term I", 89.9, 100.0, 89.9), ("Term II", 80.0, 100.0, 80.0)])
        assert result is None  # 9.9 pp drop — not enough

    def test_kavitha_scenario(self):
        # 91% -> 71.05% = 19.95 pp drop
        result = check_att_decline([("Term I", 91.0, 100.0, 91.0), ("Term II", 54.0, 76.0, 71.05)])
        assert result is not None
        assert result.supporting_evidence["drop_pp"] == pytest.approx(19.95, abs=0.01)

    def test_improvement_does_not_trigger(self):
        result = check_att_decline([("Term I", 70.0, 100.0, 70.0), ("Term II", 85.0, 100.0, 85.0)])
        assert result is None


# ===========================================================================
# ATT-CONSEC  (threshold: 3+ consecutive absent days)
# ===========================================================================

class TestAttConsec:
    def _make_records(self, statuses: list[str]) -> list[tuple]:
        base = datetime.date(2025, 2, 10)
        return [(base + datetime.timedelta(days=i), s) for i, s in enumerate(statuses)]

    def test_no_data_returns_none(self):
        assert check_att_consec([]) is None

    def test_two_consecutive_does_not_trigger(self):
        assert check_att_consec(self._make_records(["absent", "absent", "present"])) is None

    def test_exactly_3_triggers(self):
        result = check_att_consec(self._make_records(["absent", "absent", "absent"]))
        assert result is not None
        assert result.rule_code == "ATT-CONSEC"
        assert result.supporting_evidence["consecutive_absent_days"] == 3

    def test_5_consecutive_vignesh(self):
        # Vignesh's scenario
        result = check_att_consec(self._make_records(["absent"] * 5))
        assert result is not None
        assert result.supporting_evidence["consecutive_absent_days"] == 5

    def test_excused_breaks_run(self):
        # absent, absent, excused, absent, absent → max run = 2
        result = check_att_consec(self._make_records(["absent", "absent", "excused", "absent", "absent"]))
        assert result is None

    def test_present_breaks_run(self):
        result = check_att_consec(self._make_records(["absent", "absent", "present", "absent", "absent", "absent"]))
        # Second run has 3 absent
        assert result is not None
        assert result.supporting_evidence["consecutive_absent_days"] == 3

    def test_multiple_runs_picks_longest(self):
        # Run of 2 then run of 4
        result = check_att_consec(self._make_records(
            ["absent", "absent", "present", "absent", "absent", "absent", "absent"]
        ))
        assert result.supporting_evidence["consecutive_absent_days"] == 4


# ===========================================================================
# MARK-LOW  (threshold: strictly < 35%)
# ===========================================================================

class TestMarkLow:
    def _a(self, name, subj, pct, date=datetime.date(2025, 1, 1)):
        return (name, subj, date, pct * 1.0, 100.0, pct)

    def test_no_data_returns_none(self):
        assert check_mark_low([]) is None

    def test_exactly_35_does_not_trigger(self):
        assert check_mark_low([self._a("CAT 1", "Math", 35.0)]) is None

    def test_just_below_35_triggers(self):
        result = check_mark_low([self._a("CAT 1", "Math", 34.9)])
        assert result is not None
        assert result.rule_code == "MARK-LOW"

    def test_kavitha_24pct(self):
        assessments = [
            self._a("CAT 1", "Mathematics", 78.0, datetime.date(2024, 8, 14)),
            self._a("CAT 2", "Mathematics", 56.0, datetime.date(2024, 11, 20)),
            self._a("CAT 3", "Mathematics", 24.0, datetime.date(2025, 1, 18)),
        ]
        result = check_mark_low(assessments)
        assert result is not None
        assert result.supporting_evidence["percentage"] == pytest.approx(24.0)
        assert result.supporting_evidence["subject"] == "Mathematics"

    def test_uses_latest_per_subject(self):
        # Earlier CAT 1 at 20% but latest CAT 2 at 50% — should NOT trigger
        assessments = [
            self._a("CAT 1", "Math", 20.0, datetime.date(2024, 8, 1)),
            self._a("CAT 2", "Math", 50.0, datetime.date(2024, 11, 1)),
        ]
        assert check_mark_low(assessments) is None

    def test_multiple_low_subjects_reports_worst(self):
        assessments = [
            self._a("CAT 1", "Math", 30.0, datetime.date(2024, 8, 1)),
            self._a("CAT 1", "Tamil", 20.0, datetime.date(2024, 8, 2)),
        ]
        result = check_mark_low(assessments)
        assert result is not None
        assert result.supporting_evidence["percentage"] == pytest.approx(20.0)


# ===========================================================================
# MARK-DECLINE  (3+ consecutive, cumulative drop >= 15 pp)
# ===========================================================================

class TestMarkDecline:
    def _a(self, name, subj, pct, date=None):
        if date is None:
            date = datetime.date(2024, 8, 1)
        return (name, subj, date, pct, 100.0, pct)

    def test_no_data_returns_none(self):
        assert check_mark_decline([]) is None

    def test_two_records_not_enough(self):
        a = [
            self._a("CAT 1", "Math", 80.0, datetime.date(2024, 8, 1)),
            self._a("CAT 2", "Math", 60.0, datetime.date(2024, 11, 1)),
        ]
        assert check_mark_decline(a) is None

    def test_kavitha_scenario(self):
        # 78 -> 56 -> 24: declining, drop = 54 pp >= 15 pp
        a = [
            self._a("CAT 1", "Mathematics", 78.0, datetime.date(2024, 8, 14)),
            self._a("CAT 2", "Mathematics", 56.0, datetime.date(2024, 11, 20)),
            self._a("CAT 3", "Mathematics", 24.0, datetime.date(2025, 1, 18)),
        ]
        result = check_mark_decline(a)
        assert result is not None
        assert result.rule_code == "MARK-DECLINE"
        assert result.supporting_evidence["consecutive_count"] == 3
        assert result.supporting_evidence["cumulative_drop_pp"] == pytest.approx(54.0)

    def test_exactly_15pp_drop_triggers(self):
        a = [
            self._a("CAT 1", "Math", 65.0, datetime.date(2024, 8, 1)),
            self._a("CAT 2", "Math", 55.0, datetime.date(2024, 9, 1)),
            self._a("CAT 3", "Math", 50.0, datetime.date(2024, 10, 1)),
        ]
        result = check_mark_decline(a)
        assert result is not None
        assert result.supporting_evidence["cumulative_drop_pp"] == pytest.approx(15.0)

    def test_just_under_15pp_does_not_trigger(self):
        a = [
            self._a("CAT 1", "Math", 64.9, datetime.date(2024, 8, 1)),
            self._a("CAT 2", "Math", 55.0, datetime.date(2024, 9, 1)),
            self._a("CAT 3", "Math", 50.0, datetime.date(2024, 10, 1)),
        ]
        result = check_mark_decline(a)
        assert result is None  # 14.9 pp < 15

    def test_improvement_breaks_sequence(self):
        a = [
            self._a("CAT 1", "Math", 80.0, datetime.date(2024, 8, 1)),
            self._a("CAT 2", "Math", 50.0, datetime.date(2024, 9, 1)),
            self._a("CAT 3", "Math", 70.0, datetime.date(2024, 10, 1)),  # went up
            self._a("CAT 4", "Math", 40.0, datetime.date(2024, 11, 1)),
        ]
        # Longest declining run: CAT 1→CAT 2 (len=2) or CAT 3→CAT 4 (len=2). None >= 3
        assert check_mark_decline(a) is None


# ===========================================================================
# ASG-LOW  (completion rate < 60%, requires >= 3 assignments)
# ===========================================================================

class TestAsgLow:
    def test_no_data_returns_none(self):
        assert check_asg_low([]) is None

    def test_fewer_than_3_assignments_skipped(self):
        # Only 2 assignments — no trigger even if rate is 0%
        assert check_asg_low([("Term I", ["missing", "missing"])]) is None

    def test_exactly_60_does_not_trigger(self):
        # 3 of 5 submitted = 60.0% — must NOT trigger
        statuses = ["submitted", "submitted", "submitted", "missing", "missing"]
        assert check_asg_low([("Term I", statuses)]) is None

    def test_just_below_60_triggers(self):
        # 2 of 4 = 50%
        statuses = ["submitted", "submitted", "missing", "missing"]
        result = check_asg_low([("Term I", statuses)])
        assert result is not None
        assert result.rule_code == "ASG-LOW"

    def test_late_counts_as_completed(self):
        # 1 submitted + 2 late = 3/5 = 60% — no trigger
        statuses = ["submitted", "late", "late", "missing", "missing"]
        assert check_asg_low([("Term I", statuses)]) is None

    def test_uses_latest_period(self):
        # Earlier period was bad (40%) but latest is fine (80%)
        result = check_asg_low([
            ("Term I", ["submitted", "missing", "missing", "missing", "missing"]),  # 20%
            ("Term II", ["submitted"] * 4 + ["missing"]),  # 80%
        ])
        assert result is None


# ===========================================================================
# ASG-DECLINE  (drop >= 20 pp, each period >= 3 assignments)
# ===========================================================================

class TestAsgDecline:
    def test_no_data_returns_none(self):
        assert check_asg_decline([]) is None

    def test_single_period_returns_none(self):
        assert check_asg_decline([("Term I", ["submitted"] * 5)]) is None

    def test_period_with_fewer_than_3_skipped(self):
        # Term I has only 2 assignments — should not be compared
        result = check_asg_decline([
            ("Term I", ["submitted", "missing"]),  # 2 assignments — skipped
            ("Term II", ["submitted", "submitted", "missing", "missing", "missing"]),  # 5
        ])
        assert result is None  # only 1 valid period

    def test_exactly_20pp_drop_triggers(self):
        # 80% -> 60% = 20 pp
        result = check_asg_decline([
            ("Term I", ["submitted"] * 4 + ["missing"]),  # 80%
            ("Term II", ["submitted"] * 3 + ["missing"] * 2),  # 60%
        ])
        assert result is not None
        assert result.rule_code == "ASG-DECLINE"
        assert result.supporting_evidence["drop_pp"] == pytest.approx(20.0)

    def test_just_under_20pp_does_not_trigger(self):
        # 79% -> 60% = 19 pp — no trigger
        result = check_asg_decline([
            ("Term I", ["submitted"] * 79 + ["missing"] * 21),   # 79%
            ("Term II", ["submitted"] * 60 + ["missing"] * 40),   # 60%
        ])
        assert result is None

    def test_improvement_does_not_trigger(self):
        result = check_asg_decline([
            ("Term I", ["submitted", "missing", "missing", "missing", "missing"]),  # 20%
            ("Term II", ["submitted"] * 4 + ["missing"]),  # 80%
        ])
        assert result is None

