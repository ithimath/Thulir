"""Router for Support Cases, Interventions, Follow-ups, and Case Notes (Phase 7)."""
import datetime
import math
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_, and_
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.middleware.auth_middleware import (
    AuthenticatedUser,
    get_current_user,
    require_role,
)
from backend.app.models.models import (
    SupportCase,
    Intervention,
    FollowUp,
    CaseNote,
    Student,
    User,
    UserSchoolRole,
    ClassSection,
    WarningIndicator,
)
from backend.app.schemas.cases import (
    SupportCaseCreate,
    SupportCaseUpdate,
    SupportCaseListItem,
    SupportCaseListOut,
    SupportCaseDetailOut,
    InterventionCreate,
    InterventionUpdate,
    InterventionOut,
    FollowUpCreate,
    FollowUpUpdate,
    FollowUpOut,
    CaseNoteCreate,
    CaseNoteOut,
    CaseStudentRef,
    UserRef,
)

router = APIRouter(prefix="/api/cases", tags=["Support Cases"])

def _user_to_ref(user: Optional[User]) -> Optional[UserRef]:
    if not user:
        return None
    return UserRef(
        id=user.id,
        full_name=user.full_name,
        designation=user.designation,
    )

def _student_to_ref(student: Student) -> CaseStudentRef:
    cs = student.class_section
    return CaseStudentRef(
        id=student.id,
        emis_id=student.emis_id,
        full_name=student.full_name,
        grade=cs.grade if cs else None,
        section=cs.section if cs else None,
    )

def _get_case_or_404(db: Session, case_id: int, school_id: int) -> SupportCase:
    case = db.query(SupportCase).filter(
        SupportCase.id == case_id,
        SupportCase.school_id == school_id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Support case not found.")
    return case

def _check_case_access(auth: AuthenticatedUser, case: SupportCase, for_write: bool = False):
    """Enforce RBAC on case access."""
    if auth.role_name == "admin":
        return
    if auth.role_name == "teacher":
        # Teacher can view/update only cases they created or are assigned to
        if case.assigned_staff_id != auth.id and case.created_by_id != auth.id:
            raise HTTPException(status_code=403, detail="Access denied: you are not assigned to this case.")
    elif auth.role_name == "counsellor":
        # Counsellor can view/update assigned cases
        if case.assigned_staff_id != auth.id and case.created_by_id != auth.id:
            raise HTTPException(status_code=403, detail="Access denied: you are not assigned to this case.")

def _generate_case_number(db: Session, school_id: int) -> str:
    max_id = db.query(func.max(SupportCase.id)).scalar() or 0
    total = db.query(func.count(SupportCase.id)).scalar() or 0
    seq = max(max_id, total) + 1
    year = datetime.datetime.now().year
    candidate = f"CAS-{year}-{school_id:02d}-{seq:04d}"
    while db.query(SupportCase).filter(SupportCase.case_number == candidate).first():
        seq += 1
        candidate = f"CAS-{year}-{school_id:02d}-{seq:04d}"
    return candidate

# ---------------------------------------------------------------------------
# 1. LIST CASES (GET /api/cases)
# ---------------------------------------------------------------------------
@router.get("", response_model=SupportCaseListOut)
def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    student_id: Optional[int] = Query(None),
    auth: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base_q = db.query(SupportCase).filter(SupportCase.school_id == auth.school_id)

    # Scoping
    if auth.role_name in ["teacher", "counsellor"]:
        base_q = base_q.filter(
            or_(
                SupportCase.assigned_staff_id == auth.id,
                SupportCase.created_by_id == auth.id
            )
        )

    if status_filter:
        base_q = base_q.filter(SupportCase.status == status_filter)
    if category:
        base_q = base_q.filter(SupportCase.category == category)
    if priority:
        base_q = base_q.filter(SupportCase.priority == priority)
    if student_id:
        base_q = base_q.filter(SupportCase.student_id == student_id)

    base_q = base_q.order_by(desc(SupportCase.created_at))

    total = base_q.count()
    total_pages = max(1, math.ceil(total / page_size))
    cases = base_q.offset((page - 1) * page_size).limit(page_size).all()

    today = datetime.date.today()
    items = []
    for c in cases:
        open_fu = db.query(func.count(FollowUp.id)).filter(
            FollowUp.case_id == c.id,
            FollowUp.status == "Pending"
        ).scalar() or 0
        overdue_fu = db.query(func.count(FollowUp.id)).filter(
            FollowUp.case_id == c.id,
            FollowUp.status == "Pending",
            FollowUp.due_date < today
        ).scalar() or 0

        items.append(
            SupportCaseListItem(
                id=c.id,
                case_number=c.case_number,
                student=_student_to_ref(c.student),
                assigned_staff=_user_to_ref(c.assigned_staff),
                category=c.category,
                status=c.status,
                priority=c.priority,
                reason=c.reason,
                review_date=c.review_date,
                open_follow_ups_count=open_fu,
                overdue_follow_ups_count=overdue_fu,
                created_at=c.created_at,
            )
        )

    return SupportCaseListOut(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

# ---------------------------------------------------------------------------
# 2. CREATE CASE (POST /api/cases)
# ---------------------------------------------------------------------------
@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: SupportCaseCreate,
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(
        Student.id == payload.student_id,
        Student.school_id == auth.school_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    # If teacher, verify class assignment
    if auth.role_name == "teacher":
        allowed = auth.assigned_classes_list
        cs = student.class_section
        if not cs or f"{cs.grade}-{cs.section}" not in allowed:
            raise HTTPException(status_code=403, detail="Cannot create case for a student not in your assigned classes.")

    # Prevent duplicate cases for the same indicator (Feature 1 Pipeline requirement)
    if payload.indicator_id:
        existing_case = db.query(SupportCase).filter(
            SupportCase.indicator_id == payload.indicator_id,
            SupportCase.school_id == auth.school_id
        ).first()
        if existing_case:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A support case ({existing_case.case_number}) already exists for this indicator. Creating duplicate cases for the same indicator is blocked."
            )

    case_number = _generate_case_number(db, auth.school_id)
    case = SupportCase(
        case_number=case_number,
        school_id=auth.school_id,
        student_id=student.id,
        indicator_id=payload.indicator_id,
        created_by_id=auth.id,
        assigned_staff_id=payload.assigned_staff_id,
        category=payload.category,
        priority=payload.priority,
        status="Open",
        reason=payload.reason,
        observations=payload.observations,
        review_date=payload.review_date,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    # If linked to an indicator, update its status
    if payload.indicator_id:
        ind = db.query(WarningIndicator).filter(WarningIndicator.id == payload.indicator_id).first()
        if ind and ind.status not in ["Closed", "Reviewed - No Action"]:
            ind.status = "Support Recommended"
            db.commit()

    return {
        "id": case.id,
        "case_number": case.case_number,
        "message": "Support case created successfully.",
    }

# ---------------------------------------------------------------------------
# 3. GET CASE DETAIL (GET /api/cases/{case_id})
# ---------------------------------------------------------------------------
@router.get("/{case_id}", response_model=SupportCaseDetailOut)
def get_case(
    case_id: int,
    auth: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    case = _get_case_or_404(db, case_id, auth.school_id)
    _check_case_access(auth, case)

    today = datetime.date.today()
    # Interventions
    interventions_out = [
        InterventionOut(
            id=i.id,
            case_id=i.case_id,
            intervention_type=i.intervention_type,
            title=i.title,
            description=i.description,
            status=i.status,
            assigned_staff=_user_to_ref(i.assigned_staff),
            start_date=i.start_date,
            target_date=i.target_date,
            completion_date=i.completion_date,
            outcome_notes=i.outcome_notes,
            created_at=i.created_at,
        )
        for i in case.interventions
    ]

    # Follow-ups
    follow_ups_out = [
        FollowUpOut(
            id=f.id,
            case_id=f.case_id,
            intervention_id=f.intervention_id,
            assigned_staff=_user_to_ref(f.assigned_staff),
            due_date=f.due_date,
            completion_date=f.completion_date,
            status=f.status,
            notes=f.notes,
            is_overdue=(f.status == "Pending" and f.due_date < today),
            created_at=f.created_at,
        )
        for f in case.follow_ups
    ]

    # Notes with confidentiality filtering:
    # Rule: Counsellor can see sensitive notes for assigned cases. Admin and teacher CANNOT see sensitive notes.
    can_see_sensitive = (auth.role_name == "counsellor" and case.assigned_staff_id == auth.id)
    case_notes_out = []
    for n in case.case_notes:
        if n.is_sensitive and not can_see_sensitive:
            continue
        case_notes_out.append(
            CaseNoteOut(
                id=n.id,
                case_id=n.case_id,
                author=_user_to_ref(n.author),
                is_sensitive=n.is_sensitive,
                note_text=n.note_text,
                created_at=n.created_at,
            )
        )

    return SupportCaseDetailOut(
        id=case.id,
        case_number=case.case_number,
        student=_student_to_ref(case.student),
        creator=_user_to_ref(case.creator),
        assigned_staff=_user_to_ref(case.assigned_staff),
        category=case.category,
        status=case.status,
        priority=case.priority,
        reason=case.reason,
        observations=case.observations,
        review_date=case.review_date,
        indicator_id=case.indicator_id,
        created_at=case.created_at,
        updated_at=case.updated_at,
        interventions=interventions_out,
        follow_ups=follow_ups_out,
        case_notes=case_notes_out,
    )

# ---------------------------------------------------------------------------
# 4. UPDATE CASE (PUT /api/cases/{case_id})
# ---------------------------------------------------------------------------
@router.put("/{case_id}", response_model=dict)
def update_case(
    case_id: int,
    payload: SupportCaseUpdate,
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    case = _get_case_or_404(db, case_id, auth.school_id)
    _check_case_access(auth, case, for_write=True)

    if payload.status is not None:
        case.status = payload.status
    if payload.priority is not None:
        case.priority = payload.priority
    if payload.observations is not None:
        case.observations = payload.observations
    if payload.review_date is not None:
        case.review_date = payload.review_date
    if payload.assigned_staff_id is not None and auth.role_name == "admin":
        case.assigned_staff_id = payload.assigned_staff_id

    case.updated_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    return {"message": "Case updated successfully."}

# ---------------------------------------------------------------------------
# 5. INTERVENTIONS (POST /api/cases/{case_id}/interventions)
# ---------------------------------------------------------------------------
@router.post("/{case_id}/interventions", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_intervention(
    case_id: int,
    payload: InterventionCreate,
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    case = _get_case_or_404(db, case_id, auth.school_id)
    _check_case_access(auth, case, for_write=True)

    staff_id = payload.assigned_staff_id or auth.id

    # Feature 4: Capture baseline snapshot at intervention start
    from backend.app.services.intervention_service import capture_baseline_snapshot
    baseline_snap = capture_baseline_snapshot(db, case.student_id, auth.school_id)

    intervention = Intervention(
        case_id=case.id,
        intervention_type=payload.intervention_type,
        title=payload.title,
        description=payload.description,
        status="Planned",
        assigned_staff_id=staff_id,
        start_date=payload.start_date,
        target_date=payload.target_date,
        baseline_snapshot=baseline_snap,
    )
    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    return {
        "id": intervention.id,
        "message": "Intervention added successfully.",
        "has_baseline": bool(baseline_snap),
    }

# ---------------------------------------------------------------------------
# 6. FOLLOW-UPS (POST /api/cases/{case_id}/follow-ups)
# ---------------------------------------------------------------------------
@router.post("/{case_id}/follow-ups", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_follow_up(
    case_id: int,
    payload: FollowUpCreate,
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    case = _get_case_or_404(db, case_id, auth.school_id)
    _check_case_access(auth, case, for_write=True)

    follow_up = FollowUp(
        case_id=case.id,
        intervention_id=payload.intervention_id,
        assigned_staff_id=payload.assigned_staff_id,
        due_date=payload.due_date,
        status="Pending",
        notes=payload.notes,
    )
    db.add(follow_up)
    db.commit()
    db.refresh(follow_up)
    return {"id": follow_up.id, "message": "Follow-up scheduled successfully."}

# ---------------------------------------------------------------------------
# 7. CASE NOTES (POST /api/cases/{case_id}/notes)
# ---------------------------------------------------------------------------
@router.post("/{case_id}/notes", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_case_note(
    case_id: int,
    payload: CaseNoteCreate,
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    case = _get_case_or_404(db, case_id, auth.school_id)
    _check_case_access(auth, case, for_write=True)

    # Only counsellors can create sensitive notes
    is_sensitive = payload.is_sensitive
    if is_sensitive and auth.role_name != "counsellor":
        is_sensitive = False

    note = CaseNote(
        case_id=case.id,
        author_id=auth.id,
        is_sensitive=is_sensitive,
        note_text=payload.note_text,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"id": note.id, "message": "Case note added successfully."}


# ---------------------------------------------------------------------------
# 8. SHARED CASE TIMELINE (GET /api/cases/{case_id}/timeline)
# ---------------------------------------------------------------------------
@router.get("/{case_id}/timeline")
def get_case_timeline(
    case_id: int,
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    case = _get_case_or_404(db, case_id, auth.school_id)
    _check_case_access(auth, case, for_write=False)

    from backend.app.services.timeline_service import build_student_timeline
    events = build_student_timeline(db, case.student_id, auth.school_id, auth, case_id=case.id)
    return {
        "case_id": case.id,
        "case_number": case.case_number,
        "student_id": case.student_id,
        "events": events,
        "total_events": len(events),
    }


# ---------------------------------------------------------------------------
# 9. INTERVENTION EFFECTIVENESS COMPARISON (GET /api/cases/{case_id}/interventions/{inv_id}/effectiveness)
# ---------------------------------------------------------------------------
@router.get("/{case_id}/interventions/{intervention_id}/effectiveness")
def get_intervention_effectiveness(
    case_id: int,
    intervention_id: int,
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    case = _get_case_or_404(db, case_id, auth.school_id)
    _check_case_access(auth, case, for_write=False)

    inv = db.query(Intervention).filter(
        Intervention.id == intervention_id,
        Intervention.case_id == case.id
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Intervention not found.")

    from backend.app.services.intervention_service import compute_intervention_comparison
    return compute_intervention_comparison(db, inv)


