# THULIR: Data Privacy, Security, & Confidentiality Policy

THULIR is deployed in public education environments to support vulnerable students. Protecting student privacy, personal welfare details, and institutional records is fundamental to the architecture.

---

## 1. Principles of Least Privilege & Scope

1. **School-Level Isolation:**  
   Every query executed on the backend is strictly scoped by the authenticated user's `school_id`. Direct API requests for records belonging to another school return an immediate `404 Not Found` or `403 Forbidden`.

2. **Class & Assignment Scoping:**  
   - **Teachers:** Restricted to students belonging to their assigned class sections (e.g. `10-A`, `10-B`). Out-of-class lookups return `403 Forbidden`.
   - **Counsellors:** Restricted to students who have active support cases assigned to that specific counsellor. Direct lookups for unassigned students return `403 Forbidden`.
   - **Administrators:** Oversee school-wide cohorts, indicators, and case distribution.

---

## 2. Sensitive Case Notes & Multi-Tier Confidentiality

During student counselling, guardians or students may disclose private family, medical, or socioeconomic hardships (e.g. domestic instability, severe financial distress, health issues).

- **`CaseNote.is_sensitive` Field:**  
  When a note is created with `is_sensitive = True`:
  - Only the **Assigned Counsellor** who holds the professional counselling relationship can read the full text.
  - For **Subject Teachers** and **Administrators**, sensitive notes are completely redacted from the API response payload.
  - Non-counsellor roles cannot mark notes as sensitive (preventing unauthorized escalation).

---

## 3. URL Hygiene & Student Privacy

- Student internal database primary keys (`id`) are separate from official government school identifiers (`emis_id`).
- Sensitive personal parameters (such as student medical history, guardian contact information, or disciplinary details) are **never passed in URL query strings or path parameters**.
- All state changes are submitted via secure HTTP `POST` and `PUT` request bodies.

---

## 4. Audit Logging

Every critical event is permanently logged to the `audit_log` table:
- User login attempts (both successful logins and failed password attempts with IP address).
- User logouts and session terminations.
- Bulk data import operations (recording uploaded batch ID, file name, timestamp, and row counts).
- Status changes and human review decisions on warning indicators.

---

## 5. Synthetic Data Guarantee

To protect student anonymity:
- All student names, EMIS IDs, guardian names, addresses, and phone numbers in local development and test databases are purely synthetic.
- All seed scripts (`backend/app/services/seed_service.py`) include strict environment guards:
  ```python
  if settings.APP_ENV == "production" and not force:
      raise RuntimeError("Refusing to seed synthetic demo data in production environment!")
  ```

