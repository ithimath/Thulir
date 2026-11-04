import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    udise_code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    district = Column(String(100), nullable=True)
    block = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    users = relationship("UserSchoolRole", back_populates="school", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="school", cascade="all, delete-orphan")
    academic_years = relationship("AcademicYear", back_populates="school", cascade="all, delete-orphan")
    warning_indicators = relationship("WarningIndicator", back_populates="school", cascade="all, delete-orphan")
    support_cases = relationship("SupportCase", back_populates="school", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    designation = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    school_roles = relationship("UserSchoolRole", back_populates="user", cascade="all, delete-orphan")


class UserSchoolRole(Base):
    __tablename__ = "user_school_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # 'admin', 'teacher', 'counsellor'
    assigned_classes = Column(String(255), nullable=True)  # comma-separated e.g. "10-A,10-B" or JSON
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="school_roles")
    school = relationship("School", back_populates="users")

    __table_args__ = (
        UniqueConstraint("user_id", "school_id", "role", name="uq_user_school_role"),
    )


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    year_name = Column(String(32), nullable=False)  # e.g. "2024-25"
    is_current = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    school = relationship("School", back_populates="academic_years")
    reporting_periods = relationship("ReportingPeriod", back_populates="academic_year", cascade="all, delete-orphan")
    classes_sections = relationship("ClassSection", back_populates="academic_year", cascade="all, delete-orphan")


class ReportingPeriod(Base):
    __tablename__ = "reporting_periods"

    id = Column(Integer, primary_key=True, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(64), nullable=False)  # e.g. "Term I", "Term II", "Term III"
    sequence_order = Column(Integer, nullable=False, default=1)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    academic_year = relationship("AcademicYear", back_populates="reporting_periods")


class ClassSection(Base):
    __tablename__ = "classes_sections"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    grade = Column(Integer, nullable=False)  # 6 to 12
    section = Column(String(16), nullable=False)  # 'A', 'B', 'C', 'D'
    class_teacher_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    academic_year = relationship("AcademicYear", back_populates="classes_sections")
    students = relationship("Student", back_populates="class_section")

    __table_args__ = (
        UniqueConstraint("school_id", "academic_year_id", "grade", "section", name="uq_class_section"),
    )


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    emis_id = Column(String(64), nullable=False, index=True)  # unique per school
    full_name = Column(String(255), nullable=False)
    gender = Column(String(16), nullable=True)
    dob = Column(Date, nullable=True)
    current_class_section_id = Column(Integer, ForeignKey("classes_sections.id", ondelete="SET NULL"), nullable=True, index=True)
    guardian_name = Column(String(255), nullable=True)
    guardian_phone = Column(String(32), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    school = relationship("School", back_populates="students")
    class_section = relationship("ClassSection", back_populates="students")
    attendance_records = relationship("AttendanceRecord", back_populates="student", cascade="all, delete-orphan")
    assessment_records = relationship("AssessmentRecord", back_populates="student", cascade="all, delete-orphan")
    assignment_records = relationship("AssignmentRecord", back_populates="student", cascade="all, delete-orphan")
    warning_indicators = relationship("WarningIndicator", back_populates="student", cascade="all, delete-orphan")
    support_cases = relationship("SupportCase", back_populates="student", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("school_id", "emis_id", name="uq_school_student_emis"),
    )


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    reporting_period_id = Column(Integer, ForeignKey("reporting_periods.id", ondelete="SET NULL"), nullable=True, index=True)
    record_date = Column(Date, nullable=True, index=True)
    status = Column(String(32), nullable=True)  # 'present', 'absent', 'excused'
    days_present = Column(Float, nullable=True)
    total_instructional_days = Column(Float, nullable=True)
    attendance_percentage = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="attendance_records")


class AssessmentRecord(Base):
    __tablename__ = "assessment_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    reporting_period_id = Column(Integer, ForeignKey("reporting_periods.id", ondelete="SET NULL"), nullable=True, index=True)
    assessment_name = Column(String(128), nullable=False)  # e.g. "CAT 1", "CAT 2", "Half Yearly"
    subject = Column(String(100), nullable=False)  # "Mathematics", "Science", etc.
    assessment_date = Column(Date, nullable=False, index=True)
    marks_obtained = Column(Float, nullable=False)
    max_marks = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="assessment_records")


class AssignmentRecord(Base):
    __tablename__ = "assignment_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    reporting_period_id = Column(Integer, ForeignKey("reporting_periods.id", ondelete="SET NULL"), nullable=True, index=True)
    subject = Column(String(100), nullable=False)
    assignment_date = Column(Date, nullable=False)
    status = Column(String(32), nullable=False)  # 'submitted', 'missing', 'late'
    score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="assignment_records")


class WarningRule(Base):
    __tablename__ = "warning_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_code = Column(String(64), nullable=False, index=True)  # e.g. "ATT-LOW", "MARK-DECLINE"
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, default=True, nullable=False)
    category = Column(String(32), nullable=False)  # 'attendance', 'academic', 'assignment'
    priority = Column(String(32), nullable=False)  # 'High', 'Medium', 'Low'
    threshold_value = Column(Float, nullable=False)
    required_records_count = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("rule_code", "version", name="uq_rule_code_version"),
    )


class WarningIndicator(Base):
    __tablename__ = "warning_indicators"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("warning_rules.id", ondelete="RESTRICT"), nullable=False, index=True)
    rule_code = Column(String(64), nullable=False, index=True)
    rule_version = Column(Integer, nullable=False, default=1)
    category = Column(String(32), nullable=False, index=True)
    priority = Column(String(32), nullable=False)  # 'High', 'Medium', 'Low'
    status = Column(String(64), default="Needs Review", nullable=False, index=True)
    # Statuses: Needs Review -> Under Review -> Support Recommended | Referred for Support | Reviewed -> Closed
    plain_explanation = Column(Text, nullable=False)
    supporting_evidence = Column(JSON, nullable=False)
    threshold_applied = Column(Float, nullable=False)
    data_quality_limitations = Column(Text, nullable=True)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    school = relationship("School", back_populates="warning_indicators")
    student = relationship("Student", back_populates="warning_indicators")
    rule = relationship("WarningRule")
    reviews = relationship("IndicatorReview", back_populates="indicator", cascade="all, delete-orphan")


class IndicatorReview(Base):
    __tablename__ = "indicator_reviews"

    id = Column(Integer, primary_key=True, index=True)
    indicator_id = Column(Integer, ForeignKey("warning_indicators.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    previous_status = Column(String(64), nullable=False)
    new_status = Column(String(64), nullable=False)
    review_notes = Column(Text, nullable=False)
    assigned_staff_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    indicator = relationship("WarningIndicator", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    assigned_staff = relationship("User", foreign_keys=[assigned_staff_id])


class SupportCase(Base):
    __tablename__ = "support_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(64), unique=True, nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    indicator_id = Column(Integer, ForeignKey("warning_indicators.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    assigned_staff_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    category = Column(String(64), nullable=False)  # 'academic', 'attendance', 'socio_welfare', 'behavioral'
    status = Column(String(64), default="Open", nullable=False, index=True)
    # Statuses: Open, In Progress, Under Observation, Resolved, Closed
    priority = Column(String(32), default="Medium", nullable=False)
    reason = Column(Text, nullable=False)
    observations = Column(Text, nullable=True)
    review_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    school = relationship("School", back_populates="support_cases")
    student = relationship("Student", back_populates="support_cases")
    creator = relationship("User", foreign_keys=[created_by_id])
    assigned_staff = relationship("User", foreign_keys=[assigned_staff_id])
    interventions = relationship("Intervention", back_populates="case", cascade="all, delete-orphan")
    follow_ups = relationship("FollowUp", back_populates="case", cascade="all, delete-orphan")
    case_notes = relationship("CaseNote", back_populates="case", cascade="all, delete-orphan")


class Intervention(Base):
    __tablename__ = "interventions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("support_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    intervention_type = Column(String(64), nullable=False)
    # academic_guidance, remedial_support, assignment_planning, attendance_followup, teacher_discussion, counsellor_referral
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(64), default="Planned", nullable=False)
    # Planned, Active, Completed, Discontinued
    assigned_staff_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    start_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    outcome_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    case = relationship("SupportCase", back_populates="interventions")
    assigned_staff = relationship("User")


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("support_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    intervention_id = Column(Integer, ForeignKey("interventions.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_staff_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)
    completion_date = Column(Date, nullable=True)
    status = Column(String(32), default="Pending", nullable=False, index=True)  # Pending, Completed, Cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    case = relationship("SupportCase", back_populates="follow_ups")
    assigned_staff = relationship("User")


class CaseNote(Base):
    __tablename__ = "case_notes"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("support_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_sensitive = Column(Boolean, default=False, nullable=False)  # sensitive notes visible only to assigned counsellor
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    case = relationship("SupportCase", back_populates="case_notes")
    author = relationship("User")


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(16), nullable=False)  # 'csv', 'xlsx'
    import_type = Column(String(32), nullable=False)  # 'students', 'attendance', 'marks'
    total_rows = Column(Integer, default=0, nullable=False)
    imported_count = Column(Integer, default=0, nullable=False)
    warnings_count = Column(Integer, default=0, nullable=False)
    rejected_count = Column(Integer, default=0, nullable=False)
    duplicates_count = Column(Integer, default=0, nullable=False)
    status = Column(String(32), default="uploaded", nullable=False)  # uploaded, validated, committed, failed
    error_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    committed_at = Column(DateTime, nullable=True)

    row_results = relationship("ImportRowResult", back_populates="batch", cascade="all, delete-orphan")


class ImportRowResult(Base):
    __tablename__ = "import_row_results"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    raw_data = Column(JSON, nullable=False)
    category = Column(String(64), nullable=False)
    # imported, imported_with_warnings, rejected, skipped_duplicate, updated_existing
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    batch = relationship("ImportBatch", back_populates="row_results")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(64), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)


class StudentSupportRequest(Base):
    __tablename__ = "student_support_requests"

    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(64), unique=True, nullable=False, index=True)  # e.g. "SSR-2024-00123"
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    intake_staff_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    assigned_staff_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    case_id = Column(Integer, ForeignKey("support_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    requester_type = Column(String(64), default="student_direct", nullable=False)  # student_direct, staff_referred, peer_referred
    support_domain = Column(String(64), nullable=False)  # academic, wellbeing, attendance_travel, resources, other
    urgency_level = Column(String(32), default="routine", nullable=False)  # routine, priority, immediate
    status = Column(String(32), default="Submitted", nullable=False, index=True)  # Submitted, Acknowledged, Linked to Case, Resolved
    description = Column(Text, nullable=False)
    intake_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    school = relationship("School")
    student = relationship("Student")
    intake_staff = relationship("User", foreign_keys=[intake_staff_id])
    assigned_staff = relationship("User", foreign_keys=[assigned_staff_id])
    case = relationship("SupportCase")

