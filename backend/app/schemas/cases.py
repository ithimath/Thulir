"""Pydantic schemas for Support Cases, Interventions, Follow-ups, and Case Notes."""
import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# User reference
class UserRef(BaseModel):
    id: int
    full_name: str
    designation: Optional[str] = None
    role: Optional[str] = None

    model_config = {"from_attributes": True}

# Student reference
class CaseStudentRef(BaseModel):
    id: int
    emis_id: str
    full_name: str
    grade: Optional[int] = None
    section: Optional[str] = None

    model_config = {"from_attributes": True}

# Case Notes
class CaseNoteCreate(BaseModel):
    note_text: str = Field(..., min_length=1)
    is_sensitive: bool = False

class CaseNoteOut(BaseModel):
    id: int
    case_id: int
    author: Optional[UserRef] = None
    is_sensitive: bool
    note_text: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

# Follow-ups
class FollowUpCreate(BaseModel):
    intervention_id: Optional[int] = None
    assigned_staff_id: int
    due_date: datetime.date
    notes: Optional[str] = None

class FollowUpUpdate(BaseModel):
    status: Optional[str] = None # Pending, Completed, Cancelled
    completion_date: Optional[datetime.date] = None
    notes: Optional[str] = None

class FollowUpOut(BaseModel):
    id: int
    case_id: int
    intervention_id: Optional[int] = None
    assigned_staff: Optional[UserRef] = None
    due_date: datetime.date
    completion_date: Optional[datetime.date] = None
    status: str
    notes: Optional[str] = None
    is_overdue: bool = False
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

# Interventions
class InterventionCreate(BaseModel):
    intervention_type: str # academic_guidance, remedial_support, assignment_planning, attendance_followup, teacher_discussion, counsellor_referral
    title: str = Field(..., min_length=3, max_length=255)
    description: str
    assigned_staff_id: Optional[int] = None
    start_date: datetime.date
    target_date: Optional[datetime.date] = None

class InterventionUpdate(BaseModel):
    status: Optional[str] = None # Planned, Active, Completed, Discontinued
    completion_date: Optional[datetime.date] = None
    outcome_notes: Optional[str] = None

class InterventionOut(BaseModel):
    id: int
    case_id: int
    intervention_type: str
    title: str
    description: str
    status: str
    assigned_staff: Optional[UserRef] = None
    start_date: datetime.date
    target_date: Optional[datetime.date] = None
    completion_date: Optional[datetime.date] = None
    outcome_notes: Optional[str] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

# Support Cases
class SupportCaseCreate(BaseModel):
    student_id: int
    indicator_id: Optional[int] = None
    assigned_staff_id: int
    category: str # academic, attendance, socio_welfare, behavioral
    priority: str = "Medium" # High, Medium, Low
    reason: str = Field(..., min_length=3)
    observations: Optional[str] = None
    review_date: Optional[datetime.date] = None

class SupportCaseUpdate(BaseModel):
    status: Optional[str] = None # Open, In Progress, Under Observation, Resolved, Closed
    priority: Optional[str] = None
    assigned_staff_id: Optional[int] = None
    observations: Optional[str] = None
    review_date: Optional[datetime.date] = None

class SupportCaseListItem(BaseModel):
    id: int
    case_number: str
    student: CaseStudentRef
    assigned_staff: Optional[UserRef] = None
    category: str
    status: str
    priority: str
    reason: str
    review_date: Optional[datetime.date] = None
    open_follow_ups_count: int = 0
    overdue_follow_ups_count: int = 0
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

class SupportCaseListOut(BaseModel):
    items: List[SupportCaseListItem]
    total: int
    page: int
    page_size: int
    total_pages: int

class SupportCaseDetailOut(BaseModel):
    id: int
    case_number: str
    student: CaseStudentRef
    creator: Optional[UserRef] = None
    assigned_staff: Optional[UserRef] = None
    category: str
    status: str
    priority: str
    reason: str
    observations: Optional[str] = None
    review_date: Optional[datetime.date] = None
    indicator_id: Optional[int] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    interventions: List[InterventionOut] = []
    follow_ups: List[FollowUpOut] = []
    case_notes: List[CaseNoteOut] = []

    model_config = {"from_attributes": True}

