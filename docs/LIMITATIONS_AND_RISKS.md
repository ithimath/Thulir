# THULIR: Limitations, Failure Modes, and Civic Risk Analysis

**Tagline:** Recognize Early. Support Better. Grow Together.  
**Department:** Department of School Education, Government of Tamil Nadu

---

## 1. What THULIR Is and Is NOT

### What THULIR Is
THULIR is an explainable, deterministic **decision-support platform** designed for headmasters, subject teachers, and school counselors in Tamil Nadu government schools. It organizes routine academic, attendance, and assignment records to prompt human educators when a student may benefit from additional pastoral, academic, or welfare support.

### What THULIR Is NOT (Locked Civic Mandate)
1. **NOT an Emotion Detector:** THULIR has no sensors, webcam feeds, facial recognition, biometric analysis, or emotion classification algorithms. It does not attempt to deduce psychological or emotional states.
2. **NOT a Diagnostic Tool:** THULIR does not diagnose learning disabilities (e.g. dyslexia, ADHD), psychiatric conditions, or medical disorders. Indicators simply reflect logged numbers against state education standards.
3. **NOT a Dropout Predictor:** THULIR produces **no automated dropout probability scores**, synthetic composite "risk indices", or automated student rankings. Every indicator is a specific, human-readable prompt tied to verified records.
4. **NOT an Automated Decision Maker:** The platform cannot suspend, promote, penalize, or classify students autonomously. Every intervention, support case, and note is created and approved by authorized human educators.

---

## 2. Technical and Algorithmic Limitations

### 2.1 Deterministic Rule Boundaries
- All indicators are computed via transparent, deterministic thresholds (e.g., attendance < 75.0%, assessment < 35.0%).
- While deterministic rules ensure zero black-box bias and full explainability, they cannot account for unrecorded external context (such as seasonal harvest labor, family bereavement, or transit disruptions) until a teacher manually documents a contextual review note.

### 2.2 Data Timeliness and Reporting Latency
- Indicator accuracy is strictly a function of import recency. If attendance or assessment marks are uploaded with a two-week delay, warning generation is correspondingly delayed.
- THULIR includes the Data Quality Monitor (Feature 3) specifically to identify outdated records, reporting gaps, and missing periods before staff act on delayed signals.

### 2.3 Explicit Gap Policy vs. Statistical Imputation
- THULIR explicitly rejects statistical interpolation, spline smoothing, or mean imputation for missing historical records.
- If a school failed to upload Term 1 marks, the system renders an explicit "Data Gap: Not Assessed" badge rather than fabricating a trendline.

---

## 3. Failure Modes and Mitigation Protocols

| Failure Mode | Root Cause | Impact | Mitigation & Recovery |
|---|---|---|---|
| **False Positive Indicator** | Typographical error in data entry (e.g. entering 24 instead of 74 marks). | Student flagged for review when actually meeting standards. | **Feature 2 (Correction Centre):** Teachers propose a correction; admins verify and approve. Affected indicators are automatically recalculated and marked superseded in historical logs. Original records remain immutable. |
| **False Negative Signal** | Student attendance is 76% (just above 75% cutoff) but mask severe underlying struggle. | System does not trigger automated indicator. | **Student Support Request Queue:** Staff or students can initiate direct support requests regardless of rule trigger status. |
| **Data Synchronization Delay** | EMIS or local school spreadsheet not uploaded timely. | Indicators reflect past rather than present academic standing. | **Feature 3 (Data Quality Monitor):** Flags out-of-date records (>30 days since last reporting period) and displays audit findings on school dashboard. |
| **AI Summary Hallucination / Drift** | External LLM generating unsubstantiated claims. | Unverified notes entered into student record. | **Feature 10 Protocol:** AI summaries are disabled by default (`AI_ENABLED=false`). When enabled, output is strictly a DRAFT with mandatory source citations (`[ATT-1]`, `[ASM-2]`). Real student names and PII are stripped. Direct human review and explicit approval are required before committing to history. |
| **Connectivity Loss in Rural Schools** | Power outage or intermittent rural broadband. | Web app unreachable from school lab. | **Feature 9 (Offline Shell):** PWA caches static application shell. The UI displays an amber offline banner and disables write actions to prevent data conflicts and protect student privacy (zero PII is stored offline). |

---

## 4. Ethical, Stigmatization, and Privacy Risks

### 4.1 Risk of Student Stigmatization
- **Risk:** Staff perceiving early-warning indicators as labels of student inferiority or deficit.
- **Mitigation:**
  - Standardized civic language: THULIR uses labels such as "Needs Review" and "Support Recommended" rather than "At-Risk", "Failing", or "Deficient".
  - Mandated positive framing: Interventions focus on actionable support (e.g. peer study partners, attendance follow-up, Tamil remedial tutoring).

### 4.2 Confidentiality and Counselor Privilege
- **Risk:** Sensitive personal disclosures (e.g. domestic hardship, bereavement) shared during counselling becoming visible to all subject teachers.
- **Mitigation:**
  - Multi-tier note confidentiality (`CaseNote.is_sensitive = True`).
  - Sensitive notes are cryptographically restricted and visible only to the specific assigned counselor. Subject teachers receive a redacted view preserving dignity.

### 4.3 Governance Integrity
- Rule thresholds cannot be changed silently. Every threshold modification increments the rule version, requires an administrative justification reason, logs the author, and leaves historical indicators attached to their inception rule version.

