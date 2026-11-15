"""Indicators (warning review queue) router."""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload

from backend.app.database import get_db
from backend.app.middleware.auth_middleware import (
    AuthenticatedUser,
    get_current_user,
    require_role,
)
from backend.app.models.models import (
    IndicatorReview,
    Student,
    SupportCase,
    User,
    UserSchoolRole,
    WarningIndicator,
)
from backend.app.schemas.indicators import (
    IndicatorListItem,
    IndicatorListOut,
    IndicatorOut,
    IndicatorReviewCreate,
    IndicatorStudentRef,
    IndicatorReviewOut,
    VALID_STATUS_TRANSITIONS,
)

router = APIRouter(prefix="/api/indicators", tags=["Indicators"])


def _build_indicator_query(auth: AuthenticatedUser, db: Session):
    """Base query scoped to school + role."""
    base_q = db.query(WarningIndicator).filter(
        WarningIndicator.school_id == auth.school_id
    )
    if auth.role_name == "teacher":
        # Teacher: only indicators for students in their assigned classes
        from sqlalchemy import or_, and_
        from backend.app.models.models import ClassSection

        allowed = auth.assigned_classes_list
        if not allowed:
            return base_q.filter(False)
        pairs = []
        for label in allowed:
            parts = label.split("-", 1)
            if len(parts) == 2 and parts[0].isdigit():
                pairs.append((int(parts[0]), parts[1]))
        if not pairs:
            return base_q.filter(False)
        conditions = [
            and_(ClassSection.grade == g, ClassSection.section == s) for g, s in pairs
        ]
        base_q = (
            base_q
            .join(Student, WarningIndicator.student_id == Student.id)
            .join(ClassSection, Student.current_class_section_id == ClassSection.id)
            .filter(or_(*conditions))
        )
    elif auth.role_name == "counsellor":
        # Counsellor: only indicators for students in their active cases
        subquery = (
            db.query(SupportCase.student_id)
            .filter(
                SupportCase.assigned_staff_id == auth.id,
                SupportCase.status.notin_(["Closed"]),
            )
            .subquery()
        )
        base_q = base_q.filter(WarningIndicator.student_id.in_(subquery))
    return base_q


def _build_indicator_ref(ind: WarningIndicator, db: Session) -> IndicatorStudentRef:
    student = db.query(Student).filter(Student.id == ind.student_id).first()
    cs = student.class_section if student else None
    return IndicatorStudentRef(
        id=student.id,
        emis_id=student.emis_id,
        full_name=student.full_name,
        grade=cs.grade if cs else None,
        section=cs.section if cs else None,
    )


# ---------------------------------------------------------------------------
# GET /api/indicators — review queue
# ---------------------------------------------------------------------------

@router.get("", response_model=IndicatorListOut)
def list_indicators(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    category: Optional[str] = Query(None, description="attendance | academic | assignment"),
    priority: Optional[str] = Query(None, description="High | Medium | Low"),
    status_filter: Optional[str] = Query(None, alias="status"),
    rule_code: Optional[str] = Query(None),
    student_id: Optional[int] = Query(None),
    data_origin: Optional[str] = Query(None, description="Filter by origin: all | dataset | mock | user"),
    auth: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base_q = _build_indicator_query(auth, db)

    if category:
        base_q = base_q.filter(WarningIndicator.category == category)
    if priority:
        base_q = base_q.filter(WarningIndicator.priority == priority)
    if status_filter:
        base_q = base_q.filter(WarningIndicator.status == status_filter)
    if rule_code:
        base_q = base_q.filter(WarningIndicator.rule_code == rule_code)
    if student_id:
        base_q = base_q.filter(WarningIndicator.student_id == student_id)
    if data_origin and data_origin != "all":
        base_q = base_q.filter(WarningIndicator.data_origin == data_origin)

    # Default: newest first
    base_q = base_q.order_by(desc(WarningIndicator.detected_at))

    total = base_q.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size
    indicators = base_q.offset(offset).limit(page_size).all()

    # Bulk load students with class_section in 1 single query (eliminates N+1 query buffering)
    student_ids = {ind.student_id for ind in indicators}
    student_map = {}
    if student_ids:
        students = (
            db.query(Student)
            .options(joinedload(Student.class_section))
            .filter(Student.id.in_(student_ids))
            .all()
        )
        student_map = {s.id: s for s in students}

    items = []
    for ind in indicators:
        student = student_map.get(ind.student_id)
        cs = student.class_section if student else None
        student_ref = IndicatorStudentRef(
            id=student.id if student else ind.student_id,
            emis_id=student.emis_id if student else "N/A",
            full_name=student.full_name if student else f"Student #{ind.student_id}",
            grade=cs.grade if cs else None,
            section=cs.section if cs else None,
        )
        items.append(
            IndicatorListItem(
                id=ind.id,
                rule_code=ind.rule_code,
                category=ind.category,
                priority=ind.priority,
                status=ind.status,
                plain_explanation=ind.plain_explanation,
                detected_at=ind.detected_at,
                data_origin=ind.data_origin,
                source_ref=ind.source_ref,
                student=student_ref,
            )
        )
    return IndicatorListOut(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ---------------------------------------------------------------------------
# GET /api/indicators/patterns — Multi-Indicator Pattern Analysis (Feature 6)
# ---------------------------------------------------------------------------

@router.get("/patterns", response_model=dict)
def get_indicator_patterns(
    reporting_period: Optional[str] = Query(None),
    grade: Optional[int] = Query(None),
    section: Optional[str] = Query(None),
    auth: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Identifies co-occurring indicator patterns across students.
    Strictly avoids synthetic risk scores or automated ranking.
    """
    from backend.app.services.pattern_service import analyze_indicator_patterns
    return analyze_indicator_patterns(
        db=db,
        school_id=auth.school_id,
        reporting_period=reporting_period,
        grade=grade,
        section=section,
    )


# ---------------------------------------------------------------------------
# GET /api/indicators/{indicator_id} — single indicator with evidence + history
# ---------------------------------------------------------------------------

@router.get("/{indicator_id}", response_model=IndicatorOut)
def get_indicator(
    indicator_id: int,
    auth: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ind = (
        db.query(WarningIndicator)
        .filter(
            WarningIndicator.id == indicator_id,
            WarningIndicator.school_id == auth.school_id,
        )
        .first()
    )
    if not ind:
        raise HTTPException(status_code=404, detail="Indicator not found.")

    # Scope check
    if auth.role_name == "teacher":
        from backend.app.models.models import ClassSection
        student = db.query(Student).filter(Student.id == ind.student_id).first()
        allowed = auth.assigned_classes_list
        cs = student.class_section if student else None
        if not cs or f"{cs.grade}-{cs.section}" not in allowed:
            raise HTTPException(status_code=403, detail="Access denied.")
    elif auth.role_name == "counsellor":
        case = db.query(SupportCase).filter(
            SupportCase.student_id == ind.student_id,
            SupportCase.assigned_staff_id == auth.id,
            SupportCase.status.notin_(["Closed"]),
        ).first()
        if not case:
            raise HTTPException(status_code=403, detail="Access denied.")

    reviews = []
    for rev in ind.reviews:
        reviewer = db.query(User).filter(User.id == rev.reviewer_id).first()
        reviews.append(IndicatorReviewOut(
            id=rev.id,
            reviewer_name=reviewer.full_name if reviewer else "Unknown",
            previous_status=rev.previous_status,
            new_status=rev.new_status,
            review_notes=rev.review_notes,
            created_at=rev.created_at,
        ))

    return IndicatorOut(
        id=ind.id,
        rule_code=ind.rule_code,
        rule_version=ind.rule_version,
        category=ind.category,
        priority=ind.priority,
        status=ind.status,
        plain_explanation=ind.plain_explanation,
        supporting_evidence=ind.supporting_evidence,
        threshold_applied=ind.threshold_applied,
        data_quality_limitations=ind.data_quality_limitations,
        detected_at=ind.detected_at,
        data_origin=ind.data_origin,
        source_ref=ind.source_ref,
        student=_build_indicator_ref(ind, db),
        reviews=reviews,
    )


# ---------------------------------------------------------------------------
# POST /api/indicators/{indicator_id}/review — transition status
# ---------------------------------------------------------------------------

@router.post("/{indicator_id}/review", response_model=dict)
def review_indicator(
    indicator_id: int,
    payload: IndicatorReviewCreate,
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    ind = (
        db.query(WarningIndicator)
        .filter(
            WarningIndicator.id == indicator_id,
            WarningIndicator.school_id == auth.school_id,
        )
        .first()
    )
    if not ind:
        raise HTTPException(status_code=404, detail="Indicator not found.")

    # Validate status transition
    allowed_next = VALID_STATUS_TRANSITIONS.get(ind.status, [])
    if payload.new_status not in allowed_next:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Cannot transition from '{ind.status}' to '{payload.new_status}'. "
                f"Allowed: {allowed_next}"
            ),
        )

    if not payload.review_notes or not payload.review_notes.strip():
        raise HTTPException(status_code=422, detail="Review notes are required.")

    review = IndicatorReview(
        indicator_id=ind.id,
        reviewer_id=auth.id,
        previous_status=ind.status,
        new_status=payload.new_status,
        review_notes=payload.review_notes.strip(),
        assigned_staff_id=payload.assigned_staff_id,
    )
    ind.status = payload.new_status
    db.add(review)
    db.commit()

    return {
        "indicator_id": ind.id,
        "new_status": ind.status,
        "message": "Review recorded successfully.",
    }


# ---------------------------------------------------------------------------
# POST /api/indicators/run-engine — trigger engine for school (admin only)
# ---------------------------------------------------------------------------

@router.post("/run-engine", response_model=dict, status_code=status.HTTP_200_OK)
def run_warning_engine(
    auth: AuthenticatedUser = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    from backend.app.services.warning_engine import run_engine_for_school
    result = run_engine_for_school(db, auth.school_id)
    return {
        "students_checked": result["students_checked"],
        "new_indicators": result["new_indicators"],
        "message": (
            f"Engine ran for {result['students_checked']} students. "
            f"{result['new_indicators']} new indicator(s) created."
        ),
    }


# ---------------------------------------------------------------------------
# GET /api/indicators/{indicator_id}/evidence-records (Feature 1 Pipeline)
# ---------------------------------------------------------------------------
@router.get("/{indicator_id}/evidence-records")
def get_indicator_evidence_records(
    indicator_id: int,
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    ind = db.query(WarningIndicator).filter(
        WarningIndicator.id == indicator_id,
        WarningIndicator.school_id == auth.school_id,
    ).first()
    if not ind:
        raise HTTPException(status_code=404, detail="Indicator not found.")

    from backend.app.models.models import AttendanceRecord, AssessmentRecord, AssignmentRecord, ReportingPeriod, DataCorrection
    records_out = []
    record_type = ind.category  # attendance, academic, assignment

    # Pre-cache reporting periods and pending corrections (eliminates in-loop queries)
    period_map = {p.id: p.name for p in db.query(ReportingPeriod).all()}
    pending_corrs = {
        (c.record_type, c.target_record_id)
        for c in db.query(DataCorrection).filter(
            DataCorrection.student_id == ind.student_id,
            DataCorrection.status == "Pending",
        ).all()
    }

    if ind.category == "attendance":
        att_records = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == ind.student_id,
            AttendanceRecord.school_id == auth.school_id,
        ).order_by(desc(AttendanceRecord.created_at)).limit(10).all()

        for a in att_records:
            period_name = period_map.get(a.reporting_period_id)
            has_pending = ("attendance", a.id) in pending_corrs
            val_str = f"{a.attendance_percentage:.1f}% ({int(a.days_present or 0)}/{int(a.total_instructional_days or 0)} days)" if a.attendance_percentage is not None else f"{a.status or 'Recorded'}"
            records_out.append({
                "id": a.id,
                "record_type": "attendance",
                "date": str(a.record_date or a.created_at.date()),
                "period": period_name or "Term II",
                "metric": val_str,
                "days_present": a.days_present,
                "total_days": a.total_instructional_days,
                "percentage": a.attendance_percentage,
                "status": a.status,
                "is_superseded": a.is_superseded,
                "superseded_by_id": a.superseded_by_id,
                "has_pending_correction": has_pending,
            })

    elif ind.category == "academic":
        asm_records = db.query(AssessmentRecord).filter(
            AssessmentRecord.student_id == ind.student_id,
            AssessmentRecord.school_id == auth.school_id,
        ).order_by(desc(AssessmentRecord.assessment_date)).limit(10).all()

        for a in asm_records:
            period_name = period_map.get(a.reporting_period_id)
            has_pending = ("assessment", a.id) in pending_corrs
            records_out.append({
                "id": a.id,
                "record_type": "assessment",
                "date": str(a.assessment_date),
                "period": period_name or "Term II",
                "subject": a.subject,
                "assessment_name": a.assessment_name,
                "metric": f"{a.marks_obtained}/{a.max_marks} ({a.percentage:.1f}%)",
                "marks_obtained": a.marks_obtained,
                "max_marks": a.max_marks,
                "percentage": a.percentage,
                "is_superseded": a.is_superseded,
                "superseded_by_id": a.superseded_by_id,
                "has_pending_correction": has_pending,
            })

    elif ind.category == "assignment":
        asg_records = db.query(AssignmentRecord).filter(
            AssignmentRecord.student_id == ind.student_id,
            AssignmentRecord.school_id == auth.school_id,
        ).order_by(desc(AssignmentRecord.assignment_date)).limit(10).all()

        for a in asg_records:
            period_name = period_map.get(a.reporting_period_id)
            has_pending = ("assignment", a.id) in pending_corrs
            records_out.append({
                "id": a.id,
                "record_type": "assignment",
                "date": str(a.assignment_date),
                "period": period_name or "Term II",
                "subject": a.subject,
                "metric": f"{a.status.capitalize()} (Score: {a.score or '-'})",
                "status": a.status,
                "score": a.score,
                "is_superseded": a.is_superseded,
                "superseded_by_id": a.superseded_by_id,
                "has_pending_correction": has_pending,
            })

    rep_period = records_out[0].get("period", "Term II") if records_out else "Term II"
    return {
        "indicator_id": ind.id,
        "rule_code": ind.rule_code,
        "rule_version": ind.rule_version,
        "threshold_applied": ind.threshold_applied,
        "rule_thresholds": {"threshold_value": ind.threshold_applied},
        "reporting_period": rep_period,
        "plain_explanation": ind.plain_explanation,
        "category": ind.category,
        "priority": ind.priority,
        "records": records_out,
        "evidence_records": records_out,
    }


