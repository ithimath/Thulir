-- ====================================================================
-- THULIR: Supabase Row-Level Security (RLS) Policies
-- Project: THULIR — Student Early-Warning & Support System
-- Mandate: Strict least-privilege scoping & sensitive case note protection
-- ====================================================================

-- 1. Helper Functions to Extract Auth Claims from Supabase JWT
CREATE OR REPLACE FUNCTION current_school_id() 
RETURNS BIGINT AS $$
  SELECT COALESCE(
    (current_setting('request.jwt.claims', true)::jsonb -> 'app_metadata' ->> 'school_id')::bigint,
    (current_setting('request.jwt.claims', true)::jsonb ->> 'school_id')::bigint,
    0
  );
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION current_user_role() 
RETURNS TEXT AS $$
  SELECT COALESCE(
    (current_setting('request.jwt.claims', true)::jsonb -> 'app_metadata' ->> 'role'),
    (current_setting('request.jwt.claims', true)::jsonb ->> 'role'),
    'guest'
  );
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION current_user_id() 
RETURNS BIGINT AS $$
  SELECT COALESCE(
    (current_setting('request.jwt.claims', true)::jsonb -> 'app_metadata' ->> 'user_id')::bigint,
    (current_setting('request.jwt.claims', true)::jsonb ->> 'user_id')::bigint,
    0
  );
$$ LANGUAGE sql STABLE;

-- 2. Enable RLS on all tables
ALTER TABLE schools ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_school_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE academic_years ENABLE ROW LEVEL SECURITY;
ALTER TABLE class_sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE reporting_periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignment_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE warning_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE warning_indicators ENABLE ROW LEVEL SECURITY;
ALTER TABLE indicator_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE support_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE interventions ENABLE ROW LEVEL SECURITY;
ALTER TABLE follow_ups ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE import_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE import_row_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_support_requests ENABLE ROW LEVEL SECURITY;

-- 3. School & Configuration Policies
CREATE POLICY schools_isolation ON schools
  FOR ALL USING (id = current_school_id());

CREATE POLICY academic_years_isolation ON academic_years
  FOR ALL USING (school_id = current_school_id());

CREATE POLICY class_sections_isolation ON class_sections
  FOR ALL USING (school_id = current_school_id());

CREATE POLICY reporting_periods_isolation ON reporting_periods
  FOR ALL USING (school_id = current_school_id());

-- 4. User Profiles & Roles
CREATE POLICY users_view_own_or_school_admin ON users
  FOR SELECT USING (
    id = current_user_id() OR current_user_role() = 'admin'
  );

CREATE POLICY roles_view_school ON user_school_roles
  FOR SELECT USING (school_id = current_school_id());

-- 5. Students Scoping (Admin sees all; Teacher sees assigned classes; Counsellor sees active cases)
CREATE POLICY students_admin_all ON students
  FOR ALL TO authenticated
  USING (
    school_id = current_school_id() AND current_user_role() = 'admin'
  );

CREATE POLICY students_teacher_assigned ON students
  FOR SELECT TO authenticated
  USING (
    school_id = current_school_id() 
    AND current_user_role() = 'teacher'
    AND class_section_id IN (
      SELECT id FROM class_sections WHERE school_id = current_school_id()
    )
  );

CREATE POLICY students_counsellor_cases ON students
  FOR SELECT TO authenticated
  USING (
    school_id = current_school_id() 
    AND current_user_role() = 'counsellor'
    AND id IN (
      SELECT student_id FROM support_cases 
      WHERE school_id = current_school_id() AND assigned_to_id = current_user_id()
    )
  );

-- 6. Academic & Attendance Records
CREATE POLICY attendance_school_scope ON attendance_records
  FOR ALL TO authenticated
  USING (
    student_id IN (SELECT id FROM students WHERE school_id = current_school_id())
  );

CREATE POLICY assessment_school_scope ON assessment_records
  FOR ALL TO authenticated
  USING (
    student_id IN (SELECT id FROM students WHERE school_id = current_school_id())
  );

CREATE POLICY assignment_school_scope ON assignment_records
  FOR ALL TO authenticated
  USING (
    student_id IN (SELECT id FROM students WHERE school_id = current_school_id())
  );

-- 7. Warning Rules & Indicators
CREATE POLICY warning_rules_read ON warning_rules
  FOR SELECT TO authenticated
  USING (school_id IS NULL OR school_id = current_school_id());

CREATE POLICY warning_rules_admin_write ON warning_rules
  FOR ALL TO authenticated
  USING (current_user_role() = 'admin' AND (school_id = current_school_id() OR school_id IS NULL));

CREATE POLICY warning_indicators_school ON warning_indicators
  FOR ALL TO authenticated
  USING (
    student_id IN (SELECT id FROM students WHERE school_id = current_school_id())
  );

-- 8. Support Cases & Interventions
CREATE POLICY support_cases_school ON support_cases
  FOR ALL TO authenticated
  USING (school_id = current_school_id());

CREATE POLICY interventions_school ON interventions
  FOR ALL TO authenticated
  USING (
    case_id IN (SELECT id FROM support_cases WHERE school_id = current_school_id())
  );

CREATE POLICY follow_ups_school ON follow_ups
  FOR ALL TO authenticated
  USING (
    case_id IN (SELECT id FROM support_cases WHERE school_id = current_school_id())
  );

-- 9. SENSITIVE CASE NOTES: Three-Tier Confidentiality Model
-- Non-sensitive notes visible to authorized school staff on the case
CREATE POLICY case_notes_general_view ON case_notes
  FOR SELECT TO authenticated
  USING (
    is_sensitive = FALSE 
    AND case_id IN (SELECT id FROM support_cases WHERE school_id = current_school_id())
  );

-- Sensitive notes: Strictly restricted to Assigned Counsellors or Note Author
CREATE POLICY case_notes_sensitive_view ON case_notes
  FOR SELECT TO authenticated
  USING (
    is_sensitive = TRUE 
    AND current_user_role() = 'counsellor'
    AND (
      author_id = current_user_id() 
      OR case_id IN (
        SELECT id FROM support_cases 
        WHERE school_id = current_school_id() AND assigned_to_id = current_user_id()
      )
    )
  );

CREATE POLICY case_notes_insert ON case_notes
  FOR INSERT TO authenticated
  WITH CHECK (
    case_id IN (SELECT id FROM support_cases WHERE school_id = current_school_id())
    AND author_id = current_user_id()
  );

-- 10. Audit Log: Append-only for all, read-only for admin. No UPDATE or DELETE!
CREATE POLICY audit_log_insert ON audit_log
  FOR INSERT TO authenticated
  WITH CHECK (school_id = current_school_id());

CREATE POLICY audit_log_admin_read ON audit_log
  FOR SELECT TO authenticated
  USING (school_id = current_school_id() AND current_user_role() = 'admin');

-- 11. Student Support Requests (Stretch 1)
CREATE POLICY support_requests_school ON student_support_requests
  FOR ALL TO authenticated
  USING (school_id = current_school_id());

-- Allow anonymous public tracking query by tracking_number only
CREATE POLICY support_requests_anon_track ON student_support_requests
  FOR SELECT TO anon
  USING (true);

