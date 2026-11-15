# THULIR Data Sources & Architecture Specification

## 1. Overview & Core Philosophy

THULIR is a deterministic, explainable decision-support platform designed for Tamil Nadu school staff. To ensure high empirical validity while maintaining student privacy and statutory compliance:
1. **Real Data Grounding (`data_origin = 'dataset'`):** Cleaned, open educational research datasets serve as the primary foundational data layer for student demographics, historical performance trajectories, and behavioral indicators.
2. **Read-Only Reference Tables:** Raw dataset records are stored immutably in dedicated reference tables (`ref_student_performance`, `ref_lms_engagement`, `ref_higher_ed_dropout`).
3. **Synthetic Mock Layer (`data_origin = 'mock'`):** Clearly identified, reproducible synthetic records fill operational gaps that research datasets do not provide (daily working-day registers, continuous term assessments, assignment submissions, support cases, and interventions).
4. **Human Operational Layer (`data_origin = 'user'`):** Records entered, verified, or corrected by authorized teachers, counsellors, and administrators.
5. **No Machine Learning:** All early-warning alerts are generated deterministically through explicit, human-auditable rule thresholds.

---

## 2. Ingested Datasets & Citations

| Dataset | Records | Domain / Scope | Ground Truth Target | Role in THULIR |
|---|---|---|---|---|
| **UCI Student Performance**<br>*(Cortez & Silva, 2008)* | 1,044 rows<br>(Math: 395, Port: 649) | Secondary school students (Grades 10-12) | Course Failure (`passed == 0`, final grade < 10/20) | Mapped directly to operational `students` (1,044), `student_profiles`, and 3 period `assessment_records` (3,132). |
| **LMS Engagement Dataset**<br>*(Amrieh et al., 2016)* | 478 rows | Middle & High school students in LMS environment | Low Academic Class (`performance_class == 'Low'`) | Mapped directly to operational `students` (478) and `student_engagement_metrics`. |
| **Higher Education Dropout**<br>*(Realinho et al., 2021)* | 4,424 rows | Tertiary / polytechnic higher education | Dropout Outcome (`outcome == 'Dropout'`) | Preserved in `ref_higher_ed_dropout` for **rule calibration and back-testing only**; not exposed as school students. |

### Source Citations:
- **Cortez, P., & Silva, A. (2008).** *Using Data Mining to Predict Secondary School Student Performance.* In Proceedings of 5th Annual Future Business Technology Conference (FUBUTEC 2008), pp. 5-12, Porto, Portugal. EUROSIS-ETI.
- **Amrieh, E. A., Hamtini, T., & Al-Zoubi, A. (2016).** *Mining Educational Data to Predict Student's academic Performance using Ensemble Methods.* International Journal of Database Theory and Application, 9(8), 119-136.
- **Realinho, V., Machado, J., Baptista, L., & Martins, M. V. (2021).** *Predicting Student Dropout and Academic Success.* Data, 6(11), 110.

---

## 3. Database Schema & Origin Separation

All operational tables enforce strict lineage tracing via two standard columns:
- `data_origin`: String (`'dataset'`, `'mock'`, `'user'`)
- `source_ref`: External or reference identifier (e.g., `ref_student_performance:412`, `mock:attendance_periodic:p1:84`, `official:udise_33280100412`)

### Reference Tables (Read-Only)
- `ref_student_performance`: 1,044 rows. Contains 33 demographic, lifestyle, and academic features with period marks `grade_p1`, `grade_p2`, and `grade_final`.
- `ref_lms_engagement`: 478 rows. Contains raised hands, resource visits, discussion participation, announcements viewed, `absence_band`, and `performance_class`.
- `ref_higher_ed_dropout`: 4,424 rows. Contains curricular units credited/enrolled/approved, socioeconomic flags, and final academic outcomes.

### Operational Tables
- `schools`: Seeded with official Tamil Nadu school metadata (`Government Higher Secondary School Kovilpatti`, UDISE: `33280100412`).
- `classes_sections`: High school (10-A, 10-B, 11-A, 11-B, 12-A, 12-B) and Middle school (7-A, 8-A, 9-A).
- `students`: 1,522 operational students derived from datasets (1,044 SP + 478 LMS).
- `student_profiles`: Demographic, socioeconomic, and parental factors for UCI SP students.
- `student_engagement_metrics`: Topic, participation, and interaction counts for LMS students.
- `assessment_records`:
  - Dataset: 3,132 records (P1, P2, Final) converted to percentage: `(grade / 20.0) * 100.0`.
  - Mock: 1,434 continuous assessment marks generated for LMS students matching their `performance_class`.
- `attendance_records`:
  - Daily registers: Working days only (excluding weekends and official Tamil Nadu public holidays).
  - Period aggregates: Term 1 and Term 2 attendance totals and percentages.
  - Absence totals strictly match `ref_student_performance.absences` and `ref_lms_engagement.absence_band`.
- `assignment_records`: 12,176 records spanning Term 1 and Term 2, correlated with performance class.
- `warning_indicators`: Generated deterministically by the rule engine (`ATT-LOW`, `ATT-DECLINE`, `ATT-CONSEC`, `MARK-LOW`, `MARK-DECLINE`, `ASG-LOW`, `ASG-DECLINE`).
- `support_cases`, `interventions`, `follow_ups`, `case_notes`, `student_support_requests`: Sample workflow records.

---

## 4. Synthetic Identity & Cultural Grounding

To protect student anonymity while ensuring cultural realism in Tamil Nadu schools:
1. **Bilingual Names:** Every dataset student is assigned an authentic Tamil Nadu name in English and Tamil script (e.g., `Kavitha M. / கவிதா எம்`, `Vignesh S. / விக்னேஷ் எஸ்`).
2. **Guardian Names & Contacts:** Guardians are paired with realistic Tamil names and non-routable phone prefixes (`984210XXXX`).
3. **UDISE-Style Identifiers:** Students receive unique 16-character EMIS IDs matching Tamil Nadu school education format (`33280100412XXXXX`).

---

## 5. Management & Reproduction CLI Commands

### 1. Ingest Datasets (Idempotent)
```bash
python backend/scripts/import_datasets.py
```
*Validates CSV row counts, imports reference tables, and creates operational student entities.*

### 2. Seed Mock Records
```bash
# Seed with default SEED=42
python backend/scripts/seed_mock.py

# Custom seed
python backend/scripts/seed_mock.py --seed 123
```

### 3. Reset Mock Data (Preserves Dataset & User Records)
```bash
python backend/scripts/seed_mock.py --reset-mock
```
*Purges only records where `data_origin == 'mock'`. All `data_origin == 'dataset'` and `data_origin == 'user'` records are strictly preserved.*

### 4. Run Backtesting & Rule Calibration
```bash
python backend/scripts/backtest_rules.py
```
*Generates precision/recall metrics across all 5,946 records and updates `docs/RULE_CALIBRATION_REPORT.md`.*

