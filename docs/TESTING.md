# THULIR: Testing Architecture & Verification Guide

**Department:** Department of School Education, Government of Tamil Nadu  
**Verification Philosophy:** Every feature must be verified through automated acceptance tests before being marked complete.

---

## 1. Test Architecture

The testing framework follows strict verified increments:
- **Pure Unit Tests:** Rule boundary and mathematical edge case tests for the warning engine that run without database or HTTP network overhead.
- **Async API Integration Tests:** FastAPI endpoints tested via `httpx.AsyncClient` with `ASGITransport`, testing real session authentication, rate-limiting, role-based authorization, and transactional rollback.
- **Acceptance Test Suites (Runs A, B, C):** Dedicated end-to-end acceptance tests specifically verifying all 10 enhancements against prompt requirements.
- **Frontend Unit & i18n Tests:** Vitest suites checking translation key symmetry between English and Tamil, fallback mechanisms, and badge component mapping.
- **Production Build & PWA Shell Verification:** Tests verifying the production bundle compiles cleanly and service-worker precaches static assets with zero student PII.

---

## 2. Test Execution Commands

### Running Backend Tests (pytest)
```bash
# Run the entire backend test suite (77 tests)
backend\.venv\Scripts\pytest.exe backend/tests/ -v

# Run Run A Acceptance Tests (Features 1, 2, 3, 5)
backend\.venv\Scripts\pytest.exe backend/tests/test_run_a_core.py -v

# Run Run B Acceptance Tests (Features 4, 6, 7, 8)
backend\.venv\Scripts\pytest.exe backend/tests/test_run_b_analytics.py -v

# Run Run C Acceptance Tests (Features 9, 10)
backend\.venv\Scripts\pytest.exe backend/tests/test_run_c_advanced.py -v

# Run Warning Engine Edge Case Unit Tests
backend\.venv\Scripts\pytest.exe backend/tests/test_warning_engine.py -v
```

### Running Frontend Tests (vitest)
```bash
npm test --prefix frontend
```

### Frontend Production Build Check
```bash
npm run build --prefix frontend
```

---

## 3. Test Suites & Verification Status

| Module / Scope | Test File | Test Count | Status | Notes |
|---|---|:---:|:---:|---|
| **Database Schema** | `backend/tests/test_schema.py` | 2 | **VERIFIED** | Core tables, foreign keys, unique constraints |
| **Auth & RBAC** | `backend/tests/test_auth_rbac.py` | 7 | **VERIFIED** | Login, password check, rate limits, session tokens, roles |
| **Warning Engine** | `backend/tests/test_warning_engine.py` | 43 | **VERIFIED** | All 7 rules tested on upper, exact, and lower boundaries |
| **Students & Review** | `backend/tests/test_students_indicators.py` | 4 | **VERIFIED** | Directory scoping, profile RBAC, queue status transitions |
| **Support Cases** | `backend/tests/test_cases.py` | 1 | **VERIFIED** | Case lifecycle, interventions, follow-ups, sensitive notes |
| **Data Import** | `backend/tests/test_import.py` | 3 | **VERIFIED** | CSV upload preview, duplicate detection, alias normalization |
| **Reports** | `backend/tests/test_reports.py` | 1 | **VERIFIED** | Trajectory calculations, aggregations, CSV exports |
| **Student Support Requests** | `backend/tests/test_support_requests.py` | 1 | **VERIFIED** | Direct intake queue, status tracking, and escalation |
| **Policy Assistant** | `backend/tests/test_assistant.py` | 4 | **VERIFIED** | Grounded guidance, guardrails refusal for dropout predictions, Tamil support |
| **Run A Core Acceptance** | `backend/tests/test_run_a_core.py` | 4 | **VERIFIED** | Features 1 (Pipeline), 2 (Corrections), 3 (Data Quality), 5 (Student Timeline) |
| **Run B Analytics Acceptance** | `backend/tests/test_run_b_analytics.py` | 4 | **VERIFIED** | Features 6 (Patterns), 7 (Rules Config), 8 (Trends), 4 (Intervention Tracker) |
| **Run C Advanced Acceptance** | `backend/tests/test_run_c_advanced.py` | 3 | **VERIFIED** | Features 9 (PWA shell / zero PII), 10 (AI summaries flag, draft & approve flow) |
| **Frontend i18n** | `frontend/src/test/i18n.test.js` | 3 | **VERIFIED** | English and Tamil translation dictionary symmetry |
| **Total Automated Tests** | | **80 passed (77 backend + 3 frontend)** | **VERIFIED** | **0 failed (100% pass rate)** |

---

## 4. Acceptance Criteria Verification Traceability

- **Feature 1 (Evidence-to-Intervention Pipeline):** Tested in `test_feature_1_evidence_to_intervention_pipeline`. An indicator is reviewed, a case is created from it, an intervention and follow-up are added, and all appear in one timeline in order. Attempting to create a second case for the same indicator is blocked with a 409 conflict.
- **Feature 2 (Indicator Verification & Correction Centre):** Tested in `test_feature_2_indicator_verification_and_correction_centre`. Correcting a mark creates a superseding record, preserves the original, re-runs the rule engine, and keeps the old indicator in history. A teacher's direct API call to apply (not propose) a correction is rejected with 403.
- **Feature 3 (Data Quality Monitor):** Tested in `test_feature_3_data_quality_monitor`. Ingesting files with duplicate IDs and invalid marks produces exact issue counts matching the import error report.
- **Feature 4 (Intervention Effectiveness Tracker):** Tested in `test_feature_4_intervention_effectiveness_tracker`. Captures baseline metrics upon creation and compares post-intervention records with mandatory "observed change, not proof" disclaimer.
- **Feature 5 (Student Support History):** Tested in `test_feature_5_student_support_history_privacy`. Shared chronological timeline properly scopes events and redacts sensitive counselor notes for teachers.
- **Feature 6 (Multi-Indicator Pattern Analysis):** Tested in `test_feature_6_multi_indicator_patterns`. Concurrent indicators grouped into named patterns with plain explanations and zero artificial risk scores.
- **Feature 7 (Configurable Rule Management):** Tested in `test_feature_7_configurable_rule_management`. Admin modifies threshold with justification creating version N+1; non-admin call returns 403; simulation preview estimates impact before activation.
- **Feature 8 (Historical Trend Comparison):** Tested in `test_feature_8_historical_trend_comparison`. Longitudinal trajectory shows multi-period progression with explicit gap markers for missing data.
- **Feature 9 (Offline-Friendly Shell):** Tested in `test_feature_9_offline_pwa_shell_cache_and_zero_pii`. Service worker generated precaching static shell only; API routes configured as `NetworkOnly` ensuring zero student PII offline.
- **Feature 10 (AI-Assisted Summarization):** Tested in `test_feature_10_ai_summaries_disabled_by_default` and `test_feature_10_ai_summaries_enabled_grounded_and_anonymized`. Summaries unavailable by default; when enabled, output is anonymized to `REF-{id}`, cites verified sources, marked DRAFT, and commits to record only upon explicit human approval.
