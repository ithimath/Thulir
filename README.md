# THULIR: Student Early-Warning & Decision Support System

**Tagline:** *Recognize Early. Support Better. Grow Together.*  
**Context:** Government Higher Secondary Schools, Department of School Education, Tamil Nadu.

THULIR is a secure, explainable decision-support platform designed to assist school staff (Administrators, Class/Subject Teachers, and Student Counsellors) in noticing students who may need academic, attendance, or welfare support and coordinating human interventions.

> **Civic Trust Mandate:**  
> THULIR is **NOT** an emotion detector, a diagnostic medical tool, or an automated dropout predictor. The system generates zero composite "risk scores", zero artificial probability metrics, and zero automated student rankings. Every indicator is an objective, explainable prompt for human review tied to concrete school records.

---

## 1. Feature Inventory (10 Enhancements Implemented)

### Run A: Data-Trust Core
- **Feature 1: Evidence-to-Intervention Pipeline**  
  Direct inspection of underlying records behind every indicator. Connected workflow: Detection -> Evidence Review -> Human Decision -> Support Case -> Intervention -> Follow-up -> Progress Observation. Prevention of duplicate cases for the same indicator.
- **Feature 2: Indicator Verification and Correction Centre**  
  Two-person verification protocol. Teachers propose corrections for their assigned classes; administrators review and apply. Original records remain immutable (`is_superseded=True`, `superseded_by_id`). Recalculates affected indicators with the existing rule engine while preserving historical audit trails.
- **Feature 3: Data Quality Monitor**  
  Integrated monitor on Data Import & Quality page. Anomaly detection for missing attendance, duplicate EMIS IDs, out-of-range marks, conflicting reporting periods, and rejected import rows. Expresses data completeness in plain counts and percentages only (never an invented score).
- **Feature 5: Student Support History & Unified Timeline**  
  Chronological unified event timeline component across the student profile. Enforces multi-tier confidentiality: sensitive counselor notes are visible only to assigned counselors and redacted for subject teachers.

### Run B: Analytics Core
- **Feature 4: Intervention Effectiveness Tracker**  
  Captures pre-intervention baseline metrics upon case creation and compares with subsequent records. Mandatory "observed change, not proof" labeling and fallback to "insufficient data" when records are sparse.
- **Feature 6: Multi-Indicator Pattern Analysis**  
  Detects co-occurring indicators across domains within the same reporting period (e.g. `academic_attendance_compounding`, `chronic_engagement_risk`, `multi_subject_academic_struggle`). Plain-language explanations guide multidisciplinary support without composite risk scoring.
- **Feature 7: Configurable Rule Management**  
  Administrative interface to inspect versioned early-warning rules, modify thresholds with mandatory justifications (incrementing to Version N+1), and simulate impact previews against live school records prior to activation. Non-admin modification attempts return 403 Forbidden.
- **Feature 8: Historical Trend Comparison**  
  Longitudinal attendance, assessment, and assignment trajectories across multiple reporting periods. Explicitly displays missing periods as data gaps; strictly forbids statistical fabrication or smoothing.

### Run C: Advanced Features & Documentation
- **Feature 9: Offline-Friendly Mode**  
  Progressive Web App (PWA) configured via `vite-plugin-pwa` precaching the application shell and static assets ONLY. Zero student PII or database records cached offline (`/api/.*` routes set to `NetworkOnly`). Prominent online/offline network banner with data-entry disabling when offline.
- **Feature 10: AI-Assisted Record Summarization**  
  Grounded, feature-flagged summary generator (`AI_ENABLED=false` by default). Minimizes data transmission by stripping student names and PII (referring to `REF-{id}`). Every claim cites verified source records (`[ATT-1]`, `[ASM-2]`). Output is tagged strictly as DRAFT, requiring explicit human review and staff approval before committing to history.

---

## 2. Architecture & Design Tokens

- **Frontend:** React 18 (JSX), Vite, Tailwind CSS, React Router v6, Recharts, Lucide React icons, `react-i18next` (English & Tamil).
- **Design Language:** Stitch *Institutional Civic Trust* design system tokens (Slate Navy `#0F172A`, Deep Teal `#0D9488`, Warning Crimson `#DC2626`, Amber `#D97706`, Sage Emerald `#059669`).
- **Backend:** Python 3.14, FastAPI, SQLAlchemy 2.0, Pydantic v2, Pandas, Alembic.
- **Database:** SQLite for local dev & testing (PostgreSQL/Supabase compatible schema). Reversible, additive Alembic migrations (`revision 1b7f5832a104`).
- **Authentication & RBAC:** Session-based authentication with bcrypt password hashing, HttpOnly cookies, login rate limiting, and strict server-side role authorization (`admin`, `teacher`, `counsellor`).
- **Early-Warning Engine:** Pure, deterministic rule-based module (`backend/app/services/warning_engine.py`) with evidence fingerprinting and versioned thresholds.

---

## 3. User Roles & Authority Matrix

| Capability | Administrator (`admin`) | Subject Teacher (`teacher`) | School Counsellor (`counsellor`) |
|---|:---:|:---:|:---:|
| **Student Directory** | All students in school | Assigned classes only | Assigned support cases only |
| **Evidence Inspection** | Full access | Assigned classes only | Assigned cases only |
| **Propose Data Correction** | Yes | **Yes** (Assigned classes) | No |
| **Approve / Apply Correction** | **Yes** (Sole Authority) | **Forbidden (403)** | **Forbidden (403)** |
| **Rule Configuration & Preview** | **Yes** (Sole Authority) | **Forbidden (403)** | **Forbidden (403)** |
| **Support Case Notes** | Full access | Assigned cases only | **Sensitive confidential notes** |
| **Data Import Upload** | **Yes** | **Forbidden (403)** | **Forbidden (403)** |
| **AI Draft Review & Approve** | Yes | Yes (Assigned) | Yes (Assigned) |

---

## 4. Quick Start & Local Setup

### Prerequisites
- Node.js (v18+) & npm
- Python (3.12+) via `uv` or system virtual environment

### Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment and install dependencies
uv venv .venv --python 3.14
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Run migrations to latest revision (1b7f5832a104)
python run_alembic.py upgrade head

# Start FastAPI server
.\.venv\Scripts\uvicorn.exe backend.app.main:app --reload --port 8000
```

### Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies (includes vite-plugin-pwa)
npm install

# Start development server
npm run dev
```
The frontend starts at `http://localhost:5173` with reverse proxy configured to `http://localhost:8000`.

### Dataset Ingestion & Mock Seeding Commands
```bash
# 1. Ingest cleaned reference datasets (1044 SP, 478 LMS, 4424 Higher Ed)
backend\.venv\Scripts\python.exe backend/scripts/import_datasets.py

# 2. Seed synthetic mock data (attendance registers, assessments, assignments, workflow cases)
backend\.venv\Scripts\python.exe backend/scripts/seed_mock.py

# 3. Reset mock data only (preserves all dataset and user records)
backend\.venv\Scripts\python.exe backend/scripts/seed_mock.py --reset-mock

# 4. Run deterministic rule backtesting & calibration across 5,946 student records
backend\.venv\Scripts\python.exe backend/scripts/backtest_rules.py
```

### Default Demo Credentials (Development & Testing)
*All default test accounts seeded with password:* `Password123!`
- **Administrator (Headmaster):** `admin`
- **Subject Teacher (Grade 10-A, 10-B):** `teacher`
- **School Counsellor (Head Counselor):** `counsellor`

---

## 5. Automated Testing & Verification

THULIR is verified through 86 automated tests (83 backend pytest tests + 3 frontend vitest tests) with a **100% pass rate**:

```bash
# Run dataset integration & mock layer tests (6 tests, 100% pass)
backend\.venv\Scripts\pytest.exe backend/tests/test_dataset_integration.py -v

# Run warning engine unit tests (43 tests, 100% pass)
backend\.venv\Scripts\pytest.exe backend/tests/test_warning_engine.py -v

# Run Run A acceptance tests (Features 1, 2, 3, 5)
backend\.venv\Scripts\pytest.exe backend/tests/test_run_a_core.py -v

# Run Run B acceptance tests (Features 4, 6, 7, 8)
backend\.venv\Scripts\pytest.exe backend/tests/test_run_b_analytics.py -v

# Run Run C acceptance tests (Features 9, 10)
backend\.venv\Scripts\pytest.exe backend/tests/test_run_c_advanced.py -v

# Run frontend tests (vitest i18n & dictionary symmetry)
npm test --prefix frontend

# Verify production build & PWA shell generation
npm run build --prefix frontend
```

---

## 6. Documentation Suite

- [Dataset Specifications & Data Architecture](docs/DATA_SOURCES.md)
- [Rule Calibration & Empirical Validation Report](docs/RULE_CALIBRATION_REPORT.md)
- [Limitations, Failure Modes, and Civic Risk Analysis](docs/LIMITATIONS_AND_RISKS.md)
- [Relationship with Related Systems (EMIS, LMS)](docs/RELATED_SYSTEMS.md)
- [Data Privacy, Security & Confidentiality Policy](docs/DATA_PRIVACY.md)
- [Role-Based Access Control (RBAC) Matrix](docs/ROLES.md)
- [Deterministic Early-Warning Rules Specification](docs/RULES.md)
- [Testing Architecture & Verification Guide](docs/TESTING.md)
- [Environment Configuration Template](.env.example)
