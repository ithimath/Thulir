# THULIR: Data Privacy, Security, & Confidentiality Policy

**Department:** Department of School Education, Government of Tamil Nadu  
**System Mandate:** Absolute student data dignity, least privilege, zero offline PII, and explainable decision support.

---

## 1. Principles of Least Privilege & Access Scoping

1. **School-Level Isolation:**  
   Every query executed on the backend is strictly scoped by the authenticated user's `school_id`. Direct API requests for records belonging to another school return an immediate `404 Not Found` or `403 Forbidden`.

2. **Class & Section Scoping for Teachers:**  
   - **Subject Teachers:** Restricted to students belonging to their assigned class sections (e.g. `10-A`, `10-B`). Out-of-class lookups return `403 Forbidden`.
   - Teachers may propose data corrections only for records within their assigned sections.

3. **Counsellor Scoping:**  
   - **School Counsellors:** Restricted to students who have active support cases assigned to that specific counsellor or school-level guidance workflows. Direct lookups for unassigned students outside their care remit return `403 Forbidden`.

4. **Administrative Oversight:**  
   - **Headmaster / Administrator:** School-wide visibility over cohort statistics, indicator review queues, and system configuration. Only administrators can approve data corrections or modify rule thresholds.

---

## 2. Multi-Tier Note Confidentiality Model

During student counselling, guardians or students may disclose private family, medical, or socioeconomic hardships (e.g. domestic instability, severe financial distress, medical issues).

- **`CaseNote.is_sensitive` Field:**  
  When a note is created with `is_sensitive = True`:
  - Only the **Assigned Counsellor** who holds the professional counselling relationship can read the full text.
  - For **Subject Teachers** and **Administrators**, sensitive notes are completely redacted from the API response payload.
  - Non-counsellor roles cannot mark notes as sensitive (preventing unauthorized escalation).

---

## 3. Zero Offline PII Policy (PWA & Service Worker)

To comply with the National and State Digital Personal Data Protection standards:
- **Application Shell Only:** The Progressive Web App (PWA) caches HTML, CSS, JavaScript, icons, and static fonts ONLY.
- **Zero Student PII Cached:** The service worker explicitly configures all `/api/.*` network routes as `NetworkOnly`.
- **No Local Storage or IndexedDB of PII:** Student personal data, EMIS IDs, indicator records, and case notes are **never** stored in browser `localStorage`, `sessionStorage`, `IndexedDB`, or service-worker runtime caches.
- **Offline Banner & Disabled Actions:** When network connectivity is lost, the frontend renders an amber offline banner and disables data-entry and mutation forms to protect data integrity and prevent unencrypted offline write conflicts.

---

## 4. Anonymization & AI Privacy Protocol (Feature 10)

THULIR adheres to a strict data minimization protocol when integrating with AI decision-support capabilities:
1. **Disabled by Default:** `AI_ENABLED=false` is enforced across all standard configurations.
2. **De-Identification & Reference IDs:** When generating record summaries, all student identifying details (full name, EMIS number, guardian name, phone number, address) are stripped. The student is referred to only as an opaque reference identifier (e.g. `REF-0012`).
3. **No Confidential Notes Transmitted:** Free-text counselling notes, medical remarks, and sensitive welfare logs are strictly excluded from the AI prompt context. Only structured academic numbers (percentages, attendance rates, rule codes) are provided.
4. **Draft-Only Protocol:** Every AI summary is tagged as a `DRAFT` requiring explicit human review and staff signature before any note can be committed to the student's record.

---

## 5. Immutable Data Corrections & Audit Trails

- **Non-Destructive Corrections:** When attendance or assessment records are corrected, original values are never overwritten or deleted.
- **Superseding Records:** The original record is marked `is_superseded = True` with a link to `superseded_by_id`, recording who proposed the change, who approved it, the exact timestamp, and the mandatory administrative justification reason.
- **Audit Logging:** Every critical action (authentication attempts, import batch uploads, indicator status transitions, rule threshold adjustments) is permanently recorded in the `audit_logs` table.

---

## 6. Synthetic Data Guarantee

To protect student anonymity during testing, demonstration, and development:
- All student names, EMIS IDs, guardian names, addresses, and phone numbers in local development and test databases are purely synthetic.
- All seed scripts (`backend/app/services/seed_service.py`) include strict environment guards:
  ```python
  if settings.APP_ENV == "production" and not force:
      raise RuntimeError("Refusing to seed synthetic demo data in production environment!")
  ```
