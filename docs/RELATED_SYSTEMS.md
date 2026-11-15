# THULIR: Integration & Relationship with Related Systems

**Department:** Department of School Education, Government of Tamil Nadu  
**System Classification:** School-Level Pastoral Care and Decision Support

---

## 1. System Ecosystem Overview

THULIR operates alongside several state and national educational information systems. It occupies a distinct operational layer focused on **pastoral care, early notice, and intervention coordination** at the school level.

```
+-----------------------------------------------------------------------+
|                    State Educational Ecosystem                         |
+-----------------------------------------------------------------------+
        |                                                 |
        v                                                 v
+-----------------------+                         +-------------------+
| TN EMIS Portal        |                         | TN SED Examination|
| (Administrative &     |                         | Directorate       |
| Census Master Data)   |                         | (Board Results)   |
+-----------------------+                         +-------------------+
        |                                                 |
        | [Scheduled Export / CSV Intake]                | [Term Assessment]
        +-----------------------+-------------------------+
                                |
                                v
                +-------------------------------+
                |            THULIR             |
                | (School-Level Decision Support|
                |  & Intervention Tracker)      |
                +-------------------------------+
                                |
        +-----------------------+-----------------------+
        |                       |                       |
        v                       v                       v
+----------------+      +----------------+      +----------------+
| Headmaster /   |      | Subject        |      | School         |
| Admin Console  |      | Teachers       |      | Counsellors    |
+----------------+      +----------------+      +----------------+
```

---

## 2. Comparison Matrix: THULIR vs. Other Platforms

| Dimension | TN EMIS (Educational Management Information System) | THULIR (Student Support Platform) | Learning Management Systems (LMS / DIKSHA) |
|---|---|---|---|
| **Primary Purpose** | State-wide student census, teacher postings, school infrastructure tracking, official certificates. | Notice students who need support early; coordinate interventions and track follow-up progress. | Course content delivery, digital textbooks, online quizzes, and teacher training. |
| **Data Scope** | Macro administrative, demographic, enrollment, and statutory census data. | Micro attendance history, assessment trajectories, assignment completion, and pastoral notes. | Lesson plans, digital asset engagement, video views. |
| **Decision Role** | Official statutory record of student enrollment and progression. | Explainable decision support prompting human staff review. | Self-paced instructional enrichment. |
| **Warning / Alerts** | None (reporting and aggregate dashboards only). | Transparent, rule-based indicators with underlying evidence inspection. | Automated course progress indicators. |
| **Privacy Scope** | State-wide administrative access by authorized departmental officers. | Strict school-level and class-level scoping; multi-tier confidential notes for counsellors. | User-level course completion records. |

---

## 3. Data Integration Interfaces

### 3.1 EMIS Master Import
- THULIR ingests student demographic master records via the standard EMIS CSV/XLSX export format.
- Supported fields: `emis_id`, `full_name`, `grade`, `section`, `gender`, `guardian_name`, `guardian_phone`.
- Flexible column alias resolution: Automatically recognizes variants such as `EMIS Number`, `Student_Name`, `Class`, and `Contact`.

### 3.2 Attendance & Periodic Assessment Intake
- Attendance registers from school day logs or bio-metric/app logs are imported with reporting period boundaries (e.g., `Term 1 - Continuous Assessment`, `Term 2`).
- Mark rosters from Continuous Assessment Tests (CAT-1, CAT-2, Mid-Term, Annual) are ingested per subject.

### 3.3 Data Quality Guardrails on Ingestion
- Uploaded data passes through the **Data Quality Monitor (Feature 3)**:
  - Validates marks are between 0 and `max_marks`.
  - Flags duplicate EMIS IDs across batches.
  - Verifies instructional days match school calendar norms.
  - Rejects malformed rows with plain-language row-by-row error logs.

---

## 4. Boundary Enforcement and Non-Interference
- THULIR **never overwrites master records in EMIS**. It operates read-only with respect to external statutory registers.
- All internal corrections made in THULIR (Feature 2) generate immutable superseding records within THULIR's local school database and do not modify central government archives without separate administrative sanction.

