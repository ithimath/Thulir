"""Pydantic schemas for Indicator Verification & Correction Centre (Feature 2)."""
import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class CorrectionProposalCreate(BaseModel):
    record_type: str = Field(..., description="'attendance', 'assessment', or 'assignment'")
    target_record_id: int = Field(..., description="ID of original record to correct")
    proposed_data: Dict[str, Any] = Field(..., description="Proposed replacement values")
    reason: str = Field(..., min_length=5, description="Auditable, contextual reason for correction")


class CorrectionDecisionRequest(BaseModel):
    action: str = Field(..., description="'approve' or 'reject'")
    rejection_reason: Optional[str] = Field(None, description="Reason if rejected")


class CorrectionItemOut(BaseModel):
    id: int
    school_id: int
    student_id: int
    student_name: str
    emis_id: str
    grade: Optional[int] = None
    section: Optional[str] = None
    record_type: str
    target_record_id: int
    superseding_record_id: Optional[int] = None
    status: str
    original_data: Dict[str, Any]
    proposed_data: Dict[str, Any]
    reason: str
    proposer_id: int
    proposer_name: str
    proposer_designation: Optional[str] = None
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    approved_at: Optional[datetime.datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class CorrectionListOut(BaseModel):
    items: List[CorrectionItemOut]
    total: int
    pending_count: int
    approved_count: int
    rejected_count: int

