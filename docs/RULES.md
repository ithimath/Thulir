# THULIR: Deterministic Early-Warning Rules Specification

**Department:** Department of School Education, Government of Tamil Nadu  
**Engine Architecture:** Deterministic, Transparent, Versioned Early Warning Engine (`backend/app/services/warning_engine.py`)

---

## 1. Principles
- **No Black Boxes:** Zero probabilistic machine learning scores, opaque weights, or hidden flags.
- **Explainability:** Every generated indicator stores a plain-language explanation (`plain_explanation`) alongside structured mathematical evidence (`supporting_evidence`), the exact rule version (`rule_version`), and the exact threshold applied (`threshold_applied`).
- **Idempotency:** A deterministic SHA-256 evidence fingerprint (`evidence_key`) guarantees that re-running the engine does not duplicate indicators for unchanged data.
- **Human Oversight:** Indicators trigger a "Needs Review" status in the review queue. Only an authorized human staff member can record a review decision or recommend an intervention plan.

---

## 2. Core Rule Catalogue & Boundary Behavior

### Rule 1: `ATT-LOW` (Attendance Floor)
* **Category:** Attendance
* **Default Priority:** High
* **Statutory Baseline:** 75.0% (TN Directorate of Government Examinations Minimum Attendance Norm)
* **Condition:** Latest period attendance percentage is **strictly less than threshold** ($P < 75.0$).
* **Data Requirement:** At least 1 reporting period with a valid non-zero denominator of instructional days.
* **Boundary Behavior:**
  * Attendance at $74.9\%$ triggers `ATT-LOW`.
  * Attendance at exactly $75.0\%$ does **NOT** trigger `ATT-LOW`.

### Rule 2: `ATT-DECLINE` (Attendance Drop)
* **Category:** Attendance
* **Default Priority:** Medium
* **Default Threshold:** 10.0 percentage points
* **Condition:** Attendance percentage dropped by **$10.0$ or more percentage points** between the two most recent reporting periods ($\Delta P \ge 10.0$).
* **Data Requirement:** At least 2 consecutive reporting periods with valid data.
* **Boundary Behavior:**
  * Drop of $9.9$ pp does **NOT** trigger.
  * Drop of exactly $10.0$ pp **DOES** trigger `ATT-DECLINE`.

### Rule 3: `ATT-CONSEC` (Consecutive Absences)
* **Category:** Attendance
* **Default Priority:** Medium
* **Default Threshold:** 3 consecutive unexcused days
* **Condition:** **3 or more consecutive unexcused daily absence records** (`status == 'absent'`).
* **Data Requirement:** Dated daily attendance register entries.
* **Boundary Behavior:**
  * 2 consecutive absent days do **NOT** trigger.
  * 3 consecutive absent days **DO** trigger.
  * Excused absence (`status == 'excused'`) or presence breaks the sequence.

### Rule 4: `MARK-LOW` (Academic Pass Threshold)
* **Category:** Academic
* **Default Priority:** High
* **Statutory Baseline:** 35.0% (Samacheer Kalvi Continuous Assessment Passing Norm)
* **Condition:** Latest Continuous Assessment Test (CAT) or term score is **strictly less than threshold** ($S < 35.0$).
* **Data Requirement:** At least 1 dated assessment record. Evaluated per subject; the worst subject score is flagged.
* **Boundary Behavior:**
  * Score of $34.9\%$ triggers `MARK-LOW`.
  * Score of exactly $35.0\%$ does **NOT** trigger.

### Rule 5: `MARK-DECLINE` (Academic Trajectory Drop)
* **Category:** Academic
* **Default Priority:** Medium
* **Default Threshold:** 15.0 percentage points
* **Condition:** **3 or more chronologically consecutive assessments** in a subject, each lower than the previous ($S_1 > S_2 > S_3$), with a cumulative drop of **$15.0$ or more percentage points** ($S_1 - S_3 \ge 15.0$).
* **Data Requirement:** 3+ consecutive dated assessments per subject.
* **Boundary Behavior:**
  * 2 consecutive dropping tests do **NOT** trigger.
  * 3 consecutive drops with cumulative drop of $14.9$ pp do **NOT** trigger.
  * 3 consecutive drops with cumulative drop of exactly $15.0$ pp **DO** trigger.

### Rule 6: `ASG-LOW` (Assignment Completion Rate)
* **Category:** Assignment
* **Default Priority:** Medium
* **Default Threshold:** 60.0% completion rate
* **Condition:** Latest period assignment completion rate is **strictly less than 60.0%** ($C < 60.0$).
* **Data Requirement:** At least 3 assignments logged in the period.
* **Boundary Behavior:**
  * Fewer than 3 assignments are skipped (insufficient data).
  * Exactly $60.0\%$ completion does **NOT** trigger.
  * $59.9\%$ completion triggers.

### Rule 7: `ASG-DECLINE` (Assignment Completion Drop)
* **Category:** Assignment
* **Default Priority:** Low
* **Default Threshold:** 20.0 percentage points
* **Condition:** Assignment completion rate fell by **$20.0$ or more percentage points** between consecutive periods.
* **Data Requirement:** At least 2 consecutive periods with $\ge 3$ assignments each.
* **Boundary Behavior:**
  * Drop of $19.9$ pp does **NOT** trigger.
  * Drop of exactly $20.0$ pp **DOES** trigger.

---

## 3. Configurable Rule Management & Versioning (Feature 7)

- **Admin-Only Modification:** Only administrators can modify active rule thresholds.
- **Rule Version Increment:** Every modification increments the rule version to Version $N+1$.
- **Audit Mandate:** Modifications require an administrative reason and log the author's user ID and timestamp.
- **Inception Version Preservation:** Historical indicators retain the rule version and threshold that generated them; altering a threshold never mutates historical indicators retrospectively.
- **Simulation Preview:** Administrators can test a proposed threshold against current school records (`GET /api/rules/preview-change`) before activating it, observing the delta in flagged students.

---

## 4. Multi-Indicator Pattern Analysis (Feature 6)

THULIR strictly rejects composite risk scores or automated rankings. When multiple indicators co-occur within the same period, THULIR groups them into named, explainable patterns to prompt multidisciplinary support:

1. **Academic & Attendance Compounding (`academic_attendance_compounding`):**
   - **Trigger:** Concurrent attendance drop (`ATT-LOW`, `ATT-DECLINE`, `ATT-CONSEC`) and assessment failure (`MARK-LOW`, `MARK-DECLINE`).
   - **Contextual Meaning:** Attendance drop compounded by falling marks suggests external barriers or disengagement requiring coordinated holistic support rather than academic tutoring alone.
   - **Recommended Domain:** `attendance_followup_and_remedial`.

2. **Chronic Engagement Disconnection (`chronic_engagement_risk`):**
   - **Trigger:** Consecutive unexcused absences (`ATT-CONSEC`) paired with incomplete assignments (`ASG-LOW`, `ASG-DECLINE`).
   - **Contextual Meaning:** Growing disconnection from routine school participation.
   - **Recommended Domain:** `counsellor_referral_and_home_visit`.

3. **Multi-Subject Academic Struggle (`multi_subject_academic_struggle`):**
   - **Trigger:** Assessment marks failing threshold across two or more distinct subjects concurrently.
   - **Contextual Meaning:** Widespread academic difficulty indicates foundational learning gaps or language barriers rather than single-subject difficulty.
   - **Recommended Domain:** `foundational_literacy_numeracy_remedial`.

---

## 5. Evidence Inspection and Case Prevention Protocol (Feature 1)

- Every indicator links directly to underlying concrete records (`/api/indicators/{id}/evidence-records`).
- Authorized staff can transition an indicator into a formal `SupportCase`.
- Duplicate prevention: Attempting to create a second active case for the same indicator is blocked with an informative conflict message and links directly to the existing active case.
- Chronological alignment: All indicator detections, human reviews, case notes, and intervention observations appear in a single unified timeline (`/api/students/{id}/timeline`).
