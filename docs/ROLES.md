# THULIR: Role-Based Access Control (RBAC) & Authority Matrix

**Department:** Department of School Education, Government of Tamil Nadu  
**Security Standard:** Strict Server-Enforced RBAC with Class-Level and Case-Level Scoping

---

## 1. Staff Roles and Definitions

THULIR defines three distinct operational roles for school personnel:

### 1. School Administrator (`admin`)
- **Profile:** Headmaster, Headmistress, or designated School Vice-Principal.
- **Responsibilities:**
  - School-wide oversight of student enrollment, warning distributions, and support cases.
  - Verification and approval of proposed data corrections.
  - Review and adjustment of statutory early-warning rule thresholds.
  - Management of bulk data imports and data quality audits.

### 2. Subject / Class Teacher (`teacher`)
- **Profile:** Classroom teachers assigned to specific grades and sections (e.g. Grade 10-A).
- **Responsibilities:**
  - Monitoring early warning indicators and academic progress for assigned classes.
  - Reviewing underlying evidence records and recording pedagogical observations.
  - Proposing corrections for attendance, assessment, or assignment records in assigned classes.
  - Initiating support cases and delivering classroom-level remedial interventions.

### 3. School Counsellor (`counsellor`)
- **Profile:** Head Counselor or Student Welfare Officer.
- **Responsibilities:**
  - Specialized pastoral care, social-emotional guidance, and family follow-up.
  - Managing active support cases assigned to counseling.
  - Recording sensitive, confidential case notes protected from general staff view.
  - Coordinating multidisciplinary support for students with compounding indicators.

---

## 2. Comprehensive Permissions & Authority Matrix

| Action / Capability | Administrator (`admin`) | Subject Teacher (`teacher`) | School Counsellor (`counsellor`) |
|---|:---:|:---:|:---:|
| **View Overview Dashboard** | Full School | Assigned Classes Only | Assigned Students / Cases |
| **Search Student Directory** | Full School | Assigned Classes Only | Assigned Students / Cases |
| **View Student Profile & Timeline** | Full School | Assigned Classes Only | Assigned Students / Cases |
| **View Standard Case Notes** | Yes | Yes (Assigned) | Yes (Assigned) |
| **View Sensitive Confidential Notes** | Redacted | Redacted | **Full Text** (Assigned only) |
| **Review Early Warning Indicators** | Full School | Assigned Classes Only | Assigned Students / Cases |
| **Inspect Underlying Evidence Records** | Yes | Yes (Assigned) | Yes (Assigned) |
| **Propose Data Correction** | Yes | **Yes** (Assigned Classes) | No |
| **Approve / Apply Data Correction** | **Yes** (Sole Authority) | **Forbidden (403)** | **Forbidden (403)** |
| **Configure Early Warning Rules** | **Yes** (Sole Authority) | **Forbidden (403)** | **Forbidden (403)** |
| **Preview Rule Simulation** | **Yes** | **Forbidden (403)** | **Forbidden (403)** |
| **Upload CSV / XLSX Imports** | **Yes** | **Forbidden (403)** | **Forbidden (403)** |
| **Data Quality Monitor Access** | Full School | Assigned Classes Filter | Assigned Students Filter |
| **Generate & Approve AI Summaries** | Yes | Yes (Assigned) | Yes (Assigned) |
| **Export Official School CSV Reports** | Yes | Assigned Classes Only | Assigned Cases Only |

---

## 3. Two-Person Integrity for Data Corrections (Feature 2)

To preserve institutional trust and audit compliance:
1. **Teacher Proposes:** A teacher notices an erroneous assessment score (e.g. 24 entered instead of 74) in their assigned class and submits a correction proposal with original value, proposed value, and mandatory reason.
2. **Admin Approves:** Only an administrator can approve and apply the proposal. Direct API requests by non-administrators to the apply endpoint (`POST /api/corrections/{id}/decide`) return an immediate `403 Forbidden`.
3. **Automatic Engine Re-run:** Upon administrative approval, affected early-warning indicators are recalculated. Previous indicator versions remain in audit history marked as `is_superseded = True`.

---

## 4. Rule Governance & Versioning Authority (Feature 7)

- Only Administrators possess permission to modify early-warning thresholds.
- Every threshold adjustment increments the rule version (Version N+1), records the author's user ID, requires an administrative justification, and establishes an effective-from timestamp.
- Historical indicators remain immutably linked to the rule version that generated them.

