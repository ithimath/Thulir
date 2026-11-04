# THULIR: Testing Architecture & Verification Guide

This document outlines the test strategy, execution commands, and coverage breakdown for THULIR.

---

## 1. Test Architecture

The testing philosophy follows strict verified increments:
- **Pure Unit Tests:** Rule boundary and mathematical edge case tests for the warning engine that run without database or HTTP network overhead.
- **Async API Integration Tests:** FastAPI endpoints tested via `httpx.AsyncClient` with `ASGITransport`, testing real session cookies, rate-limiting, role-based authorization headers, and transactional commits.
- **Frontend Unit & i18n Tests:** Vitest suites checking translation key symmetry between English and Tamil, fallback mechanisms, and badge component mapping.

---

## 2. Test Execution Commands

### Running Backend Tests (pytest)
```bash
# Run all backend tests
backend\.venv\Scripts\pytest.exe backend/tests/ -v

# Run individual test modules
backend\.venv\Scripts\pytest.exe backend/tests/test_schema.py -v
backend\.venv\Scripts\pytest.exe backend/tests/test_auth_rbac.py -v
backend\.venv\Scripts\pytest.exe backend/tests/test_warning_engine.py -v
backend\.venv\Scripts\pytest.exe backend/tests/test_students_indicators.py -v
backend\.venv\Scripts\pytest.exe backend/tests/test_cases.py -v
backend\.venv\Scripts\pytest.exe backend/tests/test_import.py -v
backend\.venv\Scripts\pytest.exe backend/tests/test_reports.py -v
```

### Running Frontend Tests (vitest)
```bash
cd frontend
npx vitest run
```

### Frontend Production Build Check
```bash
cd frontend
npm run build
```

---

## 3. Test Suites & Verification Status

| Module | Test File | Test Count | Status | Notes |
|---|---|---|---|---|
| **Database Schema** | `backend/tests/test_schema.py` | 2 | **VERIFIED** | Core 20 tables & unique constraints |
| **Auth & RBAC** | `backend/tests/test_auth_rbac.py` | 7 | **VERIFIED** | Login, password check, rate limits, session cookies, roles |
| **Warning Engine** | `backend/tests/test_warning_engine.py` | 43 | **VERIFIED** | All 7 rules tested on upper, exact, and lower boundaries |
| **Students & Review** | `backend/tests/test_students_indicators.py` | 4 | **VERIFIED** | Directory scoping, profile RBAC, queue status transitions |
| **Support Cases** | `backend/tests/test_cases.py` | 1 | **VERIFIED** | Case lifecycle, interventions, follow-ups, sensitive notes |
| **Data Import** | `backend/tests/test_import.py` | 2 | **VERIFIED** | CSV upload preview, duplicate detection, transactional commit |
| **Reports** | `backend/tests/test_reports.py` | 1 | **VERIFIED** | Trajectory calculations, aggregations, CSV exports |
| **Frontend i18n** | `frontend/src/test/i18n.test.js` | 3 | **VERIFIED** | English and Tamil translation dictionary symmetry |
| **Total Automated** | | **60 passed** | **VERIFIED** | **0 failed** |

