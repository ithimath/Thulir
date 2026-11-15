"""Pydantic schemas for warning indicator endpoints."""
import datetime
from typing import Optional, Any
from pydantic import BaseModel


class IndicatorStudentRef(BaseModel):
    id: int
    emis_id: str
    full_name: str
    grade: Optional[int] = None
    section: Optional[str] = None

    model_config = {"from_attributes": True}


class IndicatorReviewOut(BaseModel):
    id: int
    reviewer_name: str
    previous_status: str
    new_status: str
    review_notes: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class IndicatorOut(BaseModel):
    id: int
    rule_code: str
    rule_version: int
    category: str
    priority: str
    status: str
    plain_explanation: str
    supporting_evidence: Any
    threshold_applied: float
    data_quality_limitations: Optional[str]
    detected_at: datetime.datetime
    data_origin: Optional[str] = "user"
    source_ref: Optional[str] = None
    student: IndicatorStudentRef
    reviews: list[IndicatorReviewOut] = []

    model_config = {"from_attributes": True}


class IndicatorListItem(BaseModel):
    id: int
    rule_code: str
    category: str
    priority: str
    status: str
    plain_explanation: str
    detected_at: datetime.datetime
    data_origin: Optional[str] = "user"
    source_ref: Optional[str] = None
    student: IndicatorStudentRef

    model_config = {"from_attributes": True}


class IndicatorListOut(BaseModel):
    items: list[IndicatorListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


VALID_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "Needs Review": ["Under Review", "Reviewed - No Action"],
    "Under Review": ["Support Recommended", "Referred for Support", "Reviewed - No Action"],
    "Support Recommended": ["Closed"],
    "Referred for Support": ["Closed"],
    "Reviewed - No Action": ["Closed"],
    "Closed": [],
}


class IndicatorReviewCreate(BaseModel):
    new_status: str
    review_notes: str
    assigned_staff_id: Optional[int] = None

    def validate_transition(self, current_status: str) -> None:
        allowed = VALID_STATUS_TRANSITIONS.get(current_status, [])
        if self.new_status not in allowed:
            raise ValueError(
                f"Cannot transition from '{current_status}' to '{self.new_status}'. "
                f"Allowed transitions: {allowed}"
            )

