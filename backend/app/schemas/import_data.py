"""Pydantic schemas for Data Import pipeline (Phase 4)."""
import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel

class ImportRowResultOut(BaseModel):
    id: int
    row_number: int
    raw_data: Dict[str, Any]
    category: str # imported, imported_with_warnings, rejected, skipped_duplicate, updated_existing
    message: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

class ImportPreviewOut(BaseModel):
    batch_id: int
    file_name: str
    file_type: str
    import_type: str
    total_rows: int
    valid_count: int
    warnings_count: int
    rejected_count: int
    duplicates_count: int
    sample_preview: List[Dict[str, Any]]
    row_issues: List[Dict[str, Any]]

class ImportBatchListItem(BaseModel):
    id: int
    file_name: str
    file_type: str
    import_type: str
    total_rows: int
    imported_count: int
    warnings_count: int
    rejected_count: int
    duplicates_count: int
    status: str # uploaded, validated, committed, failed
    error_summary: Optional[str] = None
    created_at: datetime.datetime
    committed_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True}

class ImportCommitResponse(BaseModel):
    batch_id: int
    status: str
    total_rows: int
    imported_count: int
    duplicates_count: int
    rejected_count: int
    message: str

