# THULIR: Deterministic Early-Warning Rules Specification

This document details the deterministic rules implemented in `backend/app/services/warning_engine.py`.  
Every rule is rule-based, explainable, versioned, and strictly objective.

---

## 1. Principles
- **No Black Boxes:** No probabilistic machine learning scores, opaque weights, or hidden flags.
- **Explainability:** Every generated indicator stores a plain-language explanation (`plain_explanation`) alongside structured mathematical evidence (`supporting_evidence`) and the exact threshold applied (`threshold_applied`).
- **Idempotency:** A deterministic SHA-256 evidence fingerprint (`evidence_key`) guarantees that re-running the engine does not duplicate indicators for unchanged data.
- **Human Oversight:** Indicators trigger a "Needs Review" status in the review queue. Only an authorized human staff member can record a review decision or recommend an intervention plan.

---

## 2. Rule Catalogue & Boundary Behavior

### Rule 1: `ATT-LOW` (Attendance Floor)
* **Category:** Attendance
* **Default Priority:** High
* **Condition:** Latest period attendance percentage is **strictly less than 75.0%** ($P < 75.0$).
* **Data Requirement:** At least 1 reporting period with a valid non-zero denominator of instructional days.
* **Boundary Behavior:**
  * Attendance at $74.9\%$ triggers `ATT-LOW`.
  * Attendance at exactly $75.0\%$ does **NOT** trigger `ATT-LOW`.

### Rule 2: `ATT-DECLINE` (Attendance Drop)
* **Category:** Attendance
* **Default Priority:** Medium
* **Condition:** Attendance percentage dropped by **$10.0$ or more percentage points** between the two most recent reporting periods ($\Delta P \ge 10.0$).
* **Data Requirement:** At least 2 consecutive reporting periods with valid data.
* **Boundary Behavior:**
  * Drop of $9.9$ pp does **NOT** trigger.
  * Drop of exactly $10.0$ pp **DOES** trigger `ATT-DECLINE`.

### Rule 3: `ATT-CONSEC` (Consecutive Absences)
* **Category:** Attendance
* **Default Priority:** Medium
* **Condition:** **3 or more consecutive unexcused daily absence records** (`status == 'absent'`).
* **Data Requirement:** Dated daily attendance register entries.
* **Boundary Behavior:**
  * 2 consecutive absent days do **NOT** trigger.
  * 3 consecutive absent days **DO** trigger.
  * Excused absence (`status == 'excused'`) or presence breaks the sequence.

### Rule 4: `MARK-LOW` (Academic Pass Threshold)
* **Category:** Academic
* **Default Priority:** High
* **Condition:** Latest Continuous Assessment Test (CAT) or term score is **strictly less than 35.0%** ($S < 35.0$).
* **Data Requirement:** At least 1 dated assessment record. Evaluated per subject; the worst subject score is flagged.
* **Boundary Behavior:**
  * Score of $34.9\%$ triggers `MARK-LOW`.
  * Score of exactly $35.0\%$ does **NOT** trigger.

### Rule 5: `MARK-DECLINE` (Academic Trajectory Drop)
* **Category:** Academic
* **Default Priority:** Medium
* **Condition:** **3 or more chronologically consecutive assessments** in a subject, each lower than the previous ($S_1 > S_2 > S_3$), with a cumulative drop of **$15.0$ or more percentage points** ($S_1 - S_3 \ge 15.0$).
* **Data Requirement:** 3+ consecutive dated assessments per subject.
* **Boundary Behavior:**
  * 2 consecutive dropping tests do **NOT** trigger.
  * 3 consecutive drops with cumulative drop of $14.9$ pp do **NOT** trigger.
  * 3 consecutive drops with cumulative drop of exactly $15.0$ pp **DO** trigger.

### Rule 6: `ASG-LOW` (Assignment Completion Rate)
* **Category:** Assignment
* **Default Priority:** Medium
* **Condition:** Latest period assignment completion rate is **strictly less than 60.0%** ($C < 60.0$).
* **Data Requirement:** At least 3 assignments logged in the period.
* **Boundary Behavior:**
  * Fewer than 3 assignments are skipped (insufficient data).
  * Exactly $60.0\%$ completion does **NOT** trigger.
  * $59.9\%$ completion triggers.

### Rule 7: `ASG-DECLINE` (Assignment Completion Drop)
* **Category:** Assignment
* **Default Priority:** Low
* **Condition:** Assignment completion rate fell by **$20.0$ or more percentage points** between consecutive periods.
* **Data Requirement:** At least 2 consecutive periods with $\ge 3$ assignments each.
* **Boundary Behavior:**
  * Drop of $19.9$ pp does **NOT** trigger.
  * Drop of exactly $20.0$ pp **DOES** trigger.

