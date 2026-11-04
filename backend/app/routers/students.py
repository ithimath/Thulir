"""Students router — CRUD with school-scoped, role-enforced access."""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, func
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.middleware.auth_middleware import (
    AuthenticatedUser,
    get_current_user,
    require_role,
)
from backend.app.models.models import (
    AcademicYear,
    AttendanceRecord,
    AssessmentRecord,
    ClassSection,
    ReportingPeriod,
    Student,
    SupportCase,
    WarningIndicator,
    UserSchoolRole,
)
from backend.app.schemas.students import (
    StudentCreate,
    StudentListItem,
    StudentListOut,
    StudentProfileOut,
    StudentUpdate,
    ClassSectionOut,
    AttendanceSummaryOut,
    AssessmentSummaryOut,
)

router = APIRouter(prefix="/api/students", tags=["Students"])


def _get_student_or_404(db: Session, student_id: int, school_id: int) -> Student:
    student = (
        db.query(Student)
        .filter(Student.id == student_id, Student.school_id == school_id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student


def _check_teacher_class_access(auth: AuthenticatedUser, student: Student, db: Session) -> None:
    """Teacher may only access students in their assigned classes."""
    if auth.role_name == "teacher":
        allowed = auth.assigned_classes_list  # e.g. ["10-A", "10-B"]
        if not allowed:
            raise HTTPException(status_code=403, detail="No classes assigned to your account.")
        cs = student.class_section
        if not cs:
            raise HTTPException(status_code=403, detail="Student not in an assigned class.")
        label = f"{cs.grade}-{cs.section}"
        if label not in allowed:
            raise HTTPException(status_code=403, detail="Access denied: student not in your assigned classes.")


def _check_counsellor_case_access(auth: AuthenticatedUser, student: Student, db: Session) -> None:
    """Counsellor may only access students assigned to them via open cases."""
    if auth.role_name == "counsellor":
        case = (
            db.query(SupportCase)
            .filter(
                SupportCase.student_id == student.id,
                SupportCase.assigned_staff_id == auth.id,
                SupportCase.status.notin_(["Closed"]),
            )
            .first()
        )
        if not case:
            raise HTTPException(
                status_code=403,
                detail="Access denied: student has no active case assigned to you.",
            )


def _build_class_query_filter(auth: AuthenticatedUser, query):
    """Filter a Student query to only classes the teacher is assigned to."""
    if auth.role_name != "teacher":
        return query
    allowed = auth.assigned_classes_list
    if not allowed:
        return query.filter(False)  # return empty

    # Parse "grade-section" strings
    grade_section_pairs = []
    for label in allowed:
        parts = label.split("-", 1)
        if len(parts) == 2 and parts[0].isdigit():
            grade_section_pairs.append((int(parts[0]), parts[1]))

    if not grade_section_pairs:
        return query.filter(False)

    from sqlalchemy import or_, and_
    conditions = [
        and_(ClassSection.grade == g, ClassSection.section == s)
        for g, s in grade_section_pairs
    ]
    query = query.join(ClassSection, Student.current_class_section_id == ClassSection.id)
    return query.filter(or_(*conditions))


# ---------------------------------------------------------------------------
# GET /api/students — paginated list (teacher: assigned classes; counsellor: assigned cases)
# ---------------------------------------------------------------------------

@router.get("", response_model=StudentListOut)
def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name or EMIS ID"),
    grade: Optional[int] = Query(None),
    section: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    auth: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if auth.role_name == "counsellor":
        # Counsellor: only students in their active assigned cases
        subquery = (
            db.query(SupportCase.student_id)
            .filter(
                SupportCase.assigned_staff_id == auth.id,
                SupportCase.status.notin_(["Closed"]),
            )
            .subquery()
        )
        base_q = (
            db.query(Student)
            .filter(
                Student.school_id == auth.school_id,
                Student.id.in_(subquery),
            )
        )
    else:
        base_q = db.query(Student).filter(Student.school_id == auth.school_id)
        if auth.role_name == "teacher":
            base_q = _build_class_query_filter(auth, base_q)

    # Filters
    if search:
        term = f"%{search.strip()}%"
        base_q = base_q.filter(
            Student.full_name.ilike(term) | Student.emis_id.ilike(term)
        )
    if is_active is not None:
        base_q = base_q.filter(Student.is_active == is_active)
    if grade is not None or section is not None:
        if auth.role_name != "teacher":  # teacher already joined ClassSection
            base_q = base_q.join(ClassSection, Student.current_class_section_id == ClassSection.id, isouter=True)
        if grade is not None:
            base_q = base_q.filter(ClassSection.grade == grade)
        if section is not None:
            base_q = base_q.filter(ClassSection.section == section)

    total = base_q.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size
    students = base_q.offset(offset).limit(page_size).all()

    # Build list items (lightweight: no full history)
    items = []
    for s in students:
        # Latest attendance pct (most recent period aggregate)
        latest_att = (
            db.query(AttendanceRecord.attendance_percentage)
            .join(ReportingPeriod, AttendanceRecord.reporting_period_id == ReportingPeriod.id)
            .filter(
                AttendanceRecord.student_id == s.id,
                AttendanceRecord.record_date == None,  # noqa: E711
            )
            .order_by(ReportingPeriod.sequence_order.desc())
            .first()
        )
        latest_att_pct = latest_att[0] if latest_att else None

        open_ind = db.query(func.count(WarningIndicator.id)).filter(
            WarningIndicator.student_id == s.id,
            WarningIndicator.status.notin_(["Closed", "Reviewed - No Action"]),
        ).scalar()
        open_cases = db.query(func.count(SupportCase.id)).filter(
            SupportCase.student_id == s.id,
            SupportCase.status.notin_(["Closed"]),
        ).scalar()

        cs_out = None
        if s.class_section:
            cs_out = ClassSectionOut(
                id=s.class_section.id,
                grade=s.class_section.grade,
                section=s.class_section.section,
            )
        items.append(StudentListItem(
            id=s.id,
            emis_id=s.emis_id,
            full_name=s.full_name,
            gender=s.gender,
            class_section=cs_out,
            is_active=s.is_active,
            latest_attendance_pct=latest_att_pct,
            open_indicators_count=open_ind or 0,
            open_cases_count=open_cases or 0,
        ))

    return StudentListOut(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ---------------------------------------------------------------------------
# GET /api/students/{student_id} — full profile
# ---------------------------------------------------------------------------

@router.get("/{student_id}", response_model=StudentProfileOut)
def get_student(
    student_id: int,
    auth: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = _get_student_or_404(db, student_id, auth.school_id)
    _check_teacher_class_access(auth, student, db)
    _check_counsellor_case_access(auth, student, db)

    # Attendance history (periodic)
    att_rows = (
        db.query(
            ReportingPeriod.name,
            AttendanceRecord.days_present,
            AttendanceRecord.total_instructional_days,
            AttendanceRecord.attendance_percentage,
        )
        .join(AttendanceRecord, AttendanceRecord.reporting_period_id == ReportingPeriod.id)
        .filter(
            AttendanceRecord.student_id == student.id,
            AttendanceRecord.record_date == None,  # noqa: E711
        )
        .order_by(asc(ReportingPeriod.sequence_order))
        .all()
    )
    attendance_history = [
        AttendanceSummaryOut(
            period_name=r.name,
            days_present=r.days_present,
            total_instructional_days=r.total_instructional_days,
            attendance_percentage=r.attendance_percentage,
        )
        for r in att_rows
    ]

    # Assessment history
    asmnt_rows = (
        db.query(
            AssessmentRecord.assessment_name,
            AssessmentRecord.subject,
            AssessmentRecord.assessment_date,
            AssessmentRecord.marks_obtained,
            AssessmentRecord.max_marks,
            AssessmentRecord.percentage,
        )
        .filter(AssessmentRecord.student_id == student.id)
        .order_by(asc(AssessmentRecord.assessment_date))
        .all()
    )
    assessment_history = [
        AssessmentSummaryOut(
            assessment_name=r.assessment_name,
            subject=r.subject,
            assessment_date=r.assessment_date,
            marks_obtained=r.marks_obtained,
            max_marks=r.max_marks,
            percentage=r.percentage,
        )
        for r in asmnt_rows
    ]

    open_ind = db.query(func.count(WarningIndicator.id)).filter(
        WarningIndicator.student_id == student.id,
        WarningIndicator.status.notin_(["Closed", "Reviewed - No Action"]),
    ).scalar()
    open_cases = db.query(func.count(SupportCase.id)).filter(
        SupportCase.student_id == student.id,
        SupportCase.status.notin_(["Closed"]),
    ).scalar()

    cs_out = None
    if student.class_section:
        cs_out = ClassSectionOut(
            id=student.class_section.id,
            grade=student.class_section.grade,
            section=student.class_section.section,
        )

    return StudentProfileOut(
        id=student.id,
        emis_id=student.emis_id,
        full_name=student.full_name,
        gender=student.gender,
        dob=student.dob,
        class_section=cs_out,
        guardian_name=student.guardian_name,
        guardian_phone=student.guardian_phone,
        address=student.address,
        is_active=student.is_active,
        created_at=student.created_at,
        updated_at=student.updated_at,
        attendance_history=attendance_history,
        assessment_history=assessment_history,
        open_indicators_count=open_ind or 0,
        open_cases_count=open_cases or 0,
    )


# ---------------------------------------------------------------------------
# POST /api/students — create (admin only)
# ---------------------------------------------------------------------------

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    auth: AuthenticatedUser = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    # Duplicate check
    existing = db.query(Student).filter(
        Student.school_id == auth.school_id,
        Student.emis_id == payload.emis_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A student with EMIS ID '{payload.emis_id}' already exists in this school.",
        )

    # Resolve class section
    ay = db.query(AcademicYear).filter(
        AcademicYear.school_id == auth.school_id,
        AcademicYear.is_current == True,
    ).first()
    cs = None
    if ay:
        cs = db.query(ClassSection).filter(
            ClassSection.school_id == auth.school_id,
            ClassSection.academic_year_id == ay.id,
            ClassSection.grade == payload.grade,
            ClassSection.section == payload.section,
        ).first()
    if not cs:
        raise HTTPException(
            status_code=422,
            detail=f"Class section {payload.grade}-{payload.section} not found for the current academic year.",
        )

    student = Student(
        school_id=auth.school_id,
        emis_id=payload.emis_id,
        full_name=payload.full_name,
        gender=payload.gender,
        dob=payload.dob,
        current_class_section_id=cs.id,
        guardian_name=payload.guardian_name,
        guardian_phone=payload.guardian_phone,
        address=payload.address,
        is_active=True,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return {"id": student.id, "emis_id": student.emis_id, "message": "Student created successfully."}


# ---------------------------------------------------------------------------
# PUT /api/students/{student_id} — update (admin or teacher own-class)
# ---------------------------------------------------------------------------

@router.put("/{student_id}", response_model=dict)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    student = _get_student_or_404(db, student_id, auth.school_id)
    if auth.role_name == "teacher":
        _check_teacher_class_access(auth, student, db)

    # Update allowed fields
    if payload.full_name is not None:
        student.full_name = payload.full_name.strip()
    if payload.gender is not None:
        student.gender = payload.gender
    if payload.dob is not None:
        student.dob = payload.dob
    if payload.guardian_name is not None:
        student.guardian_name = payload.guardian_name
    if payload.guardian_phone is not None:
        student.guardian_phone = payload.guardian_phone
    if payload.address is not None:
        student.address = payload.address
    # Only admin can change is_active or class section
    if auth.role_name == "admin":
        if payload.is_active is not None:
            student.is_active = payload.is_active
        if payload.grade is not None and payload.section is not None:
            ay = db.query(AcademicYear).filter(
                AcademicYear.school_id == auth.school_id,
                AcademicYear.is_current == True,
            ).first()
            if ay:
                cs = db.query(ClassSection).filter(
                    ClassSection.school_id == auth.school_id,
                    ClassSection.academic_year_id == ay.id,
                    ClassSection.grade == payload.grade,
                    ClassSection.section == payload.section,
                ).first()
                if cs:
                    student.current_class_section_id = cs.id

    db.commit()
    return {"id": student.id, "message": "Student updated successfully."}

