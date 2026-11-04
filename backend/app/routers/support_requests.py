"""Router for Student Support Requests (Stretch 1)."""
import datetime
import random
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.middleware.auth_middleware import AuthenticatedUser, get_current_user, require_role
from backend.app.models.models import (
    StudentSupportRequest,
    Student,
    SupportCase,
    User,
)
from backend.app.schemas.support_requests import (
    StudentSupportRequestCreate,
    StudentSupportRequestOut,
    StudentSupportRequestListItem,
    StudentSupportRequestLinkCase,
    StudentSupportRequestTrackOut,
)
from backend.app.schemas.cases import CaseStudentRef, UserRef

router = APIRouter(prefix="/api/support-requests", tags=["Student Support Requests"])

def _student_to_ref(s: Student) -> CaseStudentRef:
    cs = s.class_section
    return CaseStudentRef(
        id=s.id,
        emis_id=s.emis_id,
        full_name=s.full_name,
        grade=cs.grade if cs else None,
        section=cs.section if cs else None,
    )

def _user_to_ref(u: Optional[User]) -> Optional[UserRef]:
    if not u:
        return None
    return UserRef(
        id=u.id,
        full_name=u.full_name,
        designation=u.designation,
    )

def _generate_tracking_number(db: Session, school_id: int) -> str:
    count = db.query(func.count(StudentSupportRequest.id)).filter(StudentSupportRequest.school_id == school_id).scalar() or 0
    year = datetime.datetime.now().year
    rand = random.randint(100, 999)
    return f"SSR-{year}-{school_id:02d}-{count + 1:04d}-{rand}"

# ---------------------------------------------------------------------------
# 1. CREATE SUPPORT REQUEST (POST /api/support-requests)
# ---------------------------------------------------------------------------
@router.post("", response_model=StudentSupportRequestOut, status_code=status.HTTP_201_CREATED)
def create_support_request(
    payload: StudentSupportRequestCreate,
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(
        Student.id == payload.student_id,
        Student.school_id == auth.school_id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    tracking_num = _generate_tracking_number(db, auth.school_id)
    ssr = StudentSupportRequest(
        tracking_number=tracking_num,
        school_id=auth.school_id,
        student_id=student.id,
        intake_staff_id=auth.id,
        assigned_staff_id=payload.assigned_staff_id,
        requester_type=payload.requester_type,
        support_domain=payload.support_domain,
        urgency_level=payload.urgency_level,
        status="Submitted",
        description=payload.description.strip(),
        intake_notes=payload.intake_notes.strip() if payload.intake_notes else None,
    )
    db.add(ssr)
    db.commit()
    db.refresh(ssr)

    return StudentSupportRequestOut(
        id=ssr.id,
        tracking_number=ssr.tracking_number,
        student=_student_to_ref(ssr.student),
        intake_staff=_user_to_ref(ssr.intake_staff),
        assigned_staff=_user_to_ref(ssr.assigned_staff),
        case_id=ssr.case_id,
        requester_type=ssr.requester_type,
        support_domain=ssr.support_domain,
        urgency_level=ssr.urgency_level,
        status=ssr.status,
        description=ssr.description,
        intake_notes=ssr.intake_notes,
        created_at=ssr.created_at,
        updated_at=ssr.updated_at,
    )

# ---------------------------------------------------------------------------
# 2. LIST SUPPORT REQUESTS (GET /api/support-requests)
# ---------------------------------------------------------------------------
@router.get("", response_model=List[StudentSupportRequestListItem])
def list_support_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    auth: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(StudentSupportRequest).filter(StudentSupportRequest.school_id == auth.school_id)
    if status_filter:
        q = q.filter(StudentSupportRequest.status == status_filter)

    items = q.order_by(desc(StudentSupportRequest.created_at)).all()
    return [
        StudentSupportRequestListItem(
            id=item.id,
            tracking_number=item.tracking_number,
            student=_student_to_ref(item.student),
            support_domain=item.support_domain,
            urgency_level=item.urgency_level,
            status=item.status,
            created_at=item.created_at,
        )
        for item in items
    ]

# ---------------------------------------------------------------------------
# 3. GET DETAIL (GET /api/support-requests/{id})
# ---------------------------------------------------------------------------
@router.get("/{id}", response_model=StudentSupportRequestOut)
def get_support_request(
    id: int,
    auth: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ssr = db.query(StudentSupportRequest).filter(
        StudentSupportRequest.id == id,
        StudentSupportRequest.school_id == auth.school_id
    ).first()
    if not ssr:
        raise HTTPException(status_code=404, detail="Support request not found.")

    return StudentSupportRequestOut(
        id=ssr.id,
        tracking_number=ssr.tracking_number,
        student=_student_to_ref(ssr.student),
        intake_staff=_user_to_ref(ssr.intake_staff),
        assigned_staff=_user_to_ref(ssr.assigned_staff),
        case_id=ssr.case_id,
        requester_type=ssr.requester_type,
        support_domain=ssr.support_domain,
        urgency_level=ssr.urgency_level,
        status=ssr.status,
        description=ssr.description,
        intake_notes=ssr.intake_notes,
        created_at=ssr.created_at,
        updated_at=ssr.updated_at,
    )

# ---------------------------------------------------------------------------
# 4. TRACK REQUEST ANONYMOUSLY (GET /api/support-requests/track/{tracking_code})
# ---------------------------------------------------------------------------
@router.get("/track/{tracking_code}", response_model=StudentSupportRequestTrackOut)
def track_support_request_public(
    tracking_code: str,
    db: Session = Depends(get_db),
):
    ssr = db.query(StudentSupportRequest).filter(
        StudentSupportRequest.tracking_number == tracking_code.strip()
    ).first()
    if not ssr:
        raise HTTPException(status_code=404, detail="Invalid tracking code. No matching request found.")

    status_explanations = {
        "Submitted": "Your request has been received by the school support team and is queued for staff review.",
        "Acknowledged": "A designated teacher or school counsellor has reviewed your request and is preparing guidance.",
        "Linked to Case": "An active support case has been created. A staff member will connect with you.",
        "Resolved": "This support request has been concluded.",
    }

    return StudentSupportRequestTrackOut(
        tracking_number=ssr.tracking_number,
        status=ssr.status,
        support_domain=ssr.support_domain,
        urgency_level=ssr.urgency_level,
        created_at=ssr.created_at,
        case_linked=bool(ssr.case_id),
        status_explanation=status_explanations.get(ssr.status, "In progress."),
    )

# ---------------------------------------------------------------------------
# 5. LINK TO CASE OR ESCALATE (POST /api/support-requests/{id}/link-case)
# ---------------------------------------------------------------------------
@router.post("/{id}/link-case", response_model=dict)
def link_request_to_case(
    id: int,
    payload: StudentSupportRequestLinkCase,
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    ssr = db.query(StudentSupportRequest).filter(
        StudentSupportRequest.id == id,
        StudentSupportRequest.school_id == auth.school_id
    ).first()
    if not ssr:
        raise HTTPException(status_code=404, detail="Support request not found.")

    if payload.case_id:
        case = db.query(SupportCase).filter(
            SupportCase.id == payload.case_id,
            SupportCase.school_id == auth.school_id
        ).first()
        if not case:
            raise HTTPException(status_code=404, detail="Support case not found.")
        ssr.case_id = case.id
        ssr.status = "Linked to Case"
    else:
        # Create a new SupportCase from this request
        from backend.app.routers.cases import _generate_case_number
        case_num = _generate_case_number(db, auth.school_id)
        new_case = SupportCase(
            case_number=case_num,
            school_id=auth.school_id,
            student_id=ssr.student_id,
            created_by_id=auth.id,
            assigned_staff_id=ssr.assigned_staff_id or auth.id,
            category=payload.category or "socio_welfare",
            priority=payload.priority or "Medium",
            status="Open",
            reason=payload.reason or f"Initiated from Student Support Request {ssr.tracking_number}: {ssr.description}",
        )
        db.add(new_case)
        db.flush()
        ssr.case_id = new_case.id
        ssr.status = "Linked to Case"

    db.commit()
    return {
        "message": "Support request successfully linked to case.",
        "case_id": ssr.case_id,
        "status": ssr.status,
    }

