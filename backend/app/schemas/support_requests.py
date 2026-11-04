"""Pydantic schemas for Student Support Requests (Stretch 1)."""
import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from backend.app.schemas.cases import CaseStudentRef, UserRef

class StudentSupportRequestCreate(BaseModel):
    student_id: int
    requester_type: str = "student_direct" # student_direct, staff_referred, peer_referred
    support_domain: str # academic, wellbeing, attendance_travel, resources, other
    urgency_level: str = "routine" # routine, priority, immediate
    description: str = Field(..., min_length=5)
    intake_notes: Optional[str] = None
    assigned_staff_id: Optional[int] = None

class StudentSupportRequestLinkCase(BaseModel):
    case_id: Optional[int] = None # Link to existing case or create a new case if None
    category: Optional[str] = None
    priority: Optional[str] = "Medium"
    reason: Optional[str] = None

class StudentSupportRequestOut(BaseModel):
    id: int
    tracking_number: str
    student: CaseStudentRef
    intake_staff: UserRef
    assigned_staff: Optional[UserRef] = None
    case_id: Optional[int] = None
    requester_type: str
    support_domain: str
    urgency_level: str
    status: str
    description: str
    intake_notes: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}

class StudentSupportRequestListItem(BaseModel):
    id: int
    tracking_number: str
    student: CaseStudentRef
    support_domain: str
    urgency_level: str
    status: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

class StudentSupportRequestTrackOut(BaseModel):
    """Anonymous tracking summary for student inquiry via tracking code."""
    tracking_number: str
    status: str
    support_domain: str
    urgency_level: str
    created_at: datetime.datetime
    case_linked: bool
    status_explanation: str

