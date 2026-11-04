"""Pydantic schemas for student endpoints."""
import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class ClassSectionOut(BaseModel):
    id: int
    grade: int
    section: str

    model_config = {"from_attributes": True}


class AttendanceSummaryOut(BaseModel):
    period_name: str
    days_present: Optional[float]
    total_instructional_days: Optional[float]
    attendance_percentage: Optional[float]


class AssessmentSummaryOut(BaseModel):
    assessment_name: str
    subject: str
    assessment_date: datetime.date
    marks_obtained: float
    max_marks: float
    percentage: float


class StudentOut(BaseModel):
    id: int
    emis_id: str
    full_name: str
    gender: Optional[str]
    dob: Optional[datetime.date]
    class_section: Optional[ClassSectionOut]
    guardian_name: Optional[str]
    guardian_phone: Optional[str]
    address: Optional[str]
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class StudentListItem(BaseModel):
    """Lightweight student record for directory listing (no sensitive details in URL)."""
    id: int
    emis_id: str
    full_name: str
    gender: Optional[str]
    class_section: Optional[ClassSectionOut]
    is_active: bool
    # Latest attendance summary (from most recent period)
    latest_attendance_pct: Optional[float] = None
    open_indicators_count: int = 0
    open_cases_count: int = 0

    model_config = {"from_attributes": True}


class StudentListOut(BaseModel):
    items: list[StudentListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class StudentCreate(BaseModel):
    emis_id: str
    full_name: str
    gender: Optional[str] = None
    dob: Optional[datetime.date] = None
    grade: int
    section: str
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    address: Optional[str] = None

    @field_validator("emis_id")
    @classmethod
    def emis_id_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("EMIS ID cannot be empty.")
        return v

    @field_validator("full_name")
    @classmethod
    def name_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Student name cannot be empty.")
        return v

    @field_validator("grade")
    @classmethod
    def grade_range(cls, v: int) -> int:
        if not (1 <= v <= 12):
            raise ValueError("Grade must be between 1 and 12.")
        return v


class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[datetime.date] = None
    grade: Optional[int] = None
    section: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class StudentProfileOut(StudentOut):
    """Full student profile including attendance and assessment history."""
    attendance_history: list[AttendanceSummaryOut] = []
    assessment_history: list[AssessmentSummaryOut] = []
    open_indicators_count: int = 0
    open_cases_count: int = 0

