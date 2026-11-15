"""Router for Data Import Pipeline (Phase 4)."""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.middleware.auth_middleware import AuthenticatedUser, require_role
from backend.app.models.models import ImportBatch, ImportRowResult
from backend.app.schemas.import_data import (
    ImportPreviewOut,
    ImportBatchListItem,
    ImportCommitResponse,
    ImportRowResultOut,
)
from backend.app.services.import_service import (
    parse_file_to_dataframe,
    validate_student_rows,
    commit_student_import,
    validate_attendance_rows,
    commit_attendance_import,
    validate_marks_rows,
    commit_marks_import,
)

router = APIRouter(prefix="/api/import", tags=["Data Import"])

# Temporary in-memory cache for parsed rows awaiting confirmation
# {batch_id: rows_analysis}
_PENDING_BATCHES = {}

# ---------------------------------------------------------------------------
# 1. UPLOAD & PREVIEW (POST /api/import/upload)
# ---------------------------------------------------------------------------
@router.post("/upload", response_model=ImportPreviewOut)
async def upload_import_file(
    file: UploadFile = File(...),
    import_type: str = Form("students"), # students, attendance, marks
    auth: AuthenticatedUser = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    filename = file.filename or "upload.csv"
    ext = "xlsx" if filename.lower().endswith(('.xlsx', '.xls')) else "csv"
    content = await file.read()

    try:
        df = parse_file_to_dataframe(content, filename)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse {ext.upper()} file: {str(e)}"
        )

    if import_type == "students":
        try:
            rows_analysis, stats = validate_student_rows(df, auth.school_id, db)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    elif import_type == "attendance":
        try:
            rows_analysis, stats = validate_attendance_rows(df, auth.school_id, db)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    elif import_type == "marks":
        try:
            rows_analysis, stats = validate_marks_rows(df, auth.school_id, db)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported import type: '{import_type}'. Supported: students, attendance, marks.")

    # Create batch in 'validated' status
    batch = ImportBatch(
        school_id=auth.school_id,
        uploaded_by_id=auth.id,
        file_name=filename,
        file_type=ext,
        import_type=import_type,
        total_rows=len(df),
        imported_count=0,
        warnings_count=stats["warnings"],
        rejected_count=stats["rejected"],
        duplicates_count=stats["duplicates"],
        status="validated",
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Cache row analysis in memory for immediate confirmation
    _PENDING_BATCHES[batch.id] = rows_analysis

    # Prepare preview of first 5 rows and any issues
    sample = [r["raw_data"] for r in rows_analysis[:5]]
    issues = [
        {"row_number": r["row_number"], "category": r["category"], "message": r["message"]}
        for r in rows_analysis if r["category"] != "imported"
    ][:10]

    return ImportPreviewOut(
        batch_id=batch.id,
        file_name=batch.file_name,
        file_type=batch.file_type,
        import_type=batch.import_type,
        total_rows=batch.total_rows,
        valid_count=stats["valid"],
        warnings_count=stats["warnings"],
        rejected_count=stats["rejected"],
        duplicates_count=stats["duplicates"],
        sample_preview=sample,
        row_issues=issues,
    )

# ---------------------------------------------------------------------------
# 2. CONFIRM COMMIT (POST /api/import/{batch_id}/confirm)
# ---------------------------------------------------------------------------
@router.post("/{batch_id}/confirm", response_model=ImportCommitResponse)
def confirm_import(
    batch_id: int,
    auth: AuthenticatedUser = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    batch = db.query(ImportBatch).filter(
        ImportBatch.id == batch_id,
        ImportBatch.school_id == auth.school_id
    ).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found.")

    if batch.status == "committed":
        raise HTTPException(status_code=400, detail="This batch has already been committed.")

    rows_analysis = _PENDING_BATCHES.get(batch_id)
    if not rows_analysis:
        raise HTTPException(
            status_code=400,
            detail="Batch validation data expired or not found. Please re-upload the file."
        )

    if batch.import_type == "students":
        results = commit_student_import(batch, rows_analysis, auth.school_id, db)
    elif batch.import_type == "attendance":
        results = commit_attendance_import(batch, rows_analysis, auth.school_id, db)
    elif batch.import_type == "marks":
        results = commit_marks_import(batch, rows_analysis, auth.school_id, db)
    else:
        raise HTTPException(status_code=400, detail="Unsupported import type.")

    # Evict from in-memory pending cache
    _PENDING_BATCHES.pop(batch_id, None)

    return ImportCommitResponse(
        batch_id=batch.id,
        status=batch.status,
        total_rows=batch.total_rows,
        imported_count=results["imported"],
        duplicates_count=results["duplicates"],
        rejected_count=results["rejected"],
        message=(
            f"Import committed successfully: {results['imported']} new records created, "
            f"{results['duplicates']} updated, {results['rejected']} rejected."
        ),
    )

# ---------------------------------------------------------------------------
# 3. IMPORT HISTORY (GET /api/import/history)
# ---------------------------------------------------------------------------
@router.get("/history", response_model=List[ImportBatchListItem])
def list_import_history(
    auth: AuthenticatedUser = Depends(require_role(["admin", "teacher", "counsellor"])),
    db: Session = Depends(get_db),
):
    batches = db.query(ImportBatch).filter(
        ImportBatch.school_id == auth.school_id
    ).order_by(desc(ImportBatch.created_at)).limit(50).all()

    return batches

# ---------------------------------------------------------------------------
# 4. BATCH ROW RESULTS (GET /api/import/{batch_id}/results)
# ---------------------------------------------------------------------------
@router.get("/{batch_id}/results", response_model=List[ImportRowResultOut])
def get_batch_row_results(
    batch_id: int,
    auth: AuthenticatedUser = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    batch = db.query(ImportBatch).filter(
        ImportBatch.id == batch_id,
        ImportBatch.school_id == auth.school_id
    ).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found.")

    rows = db.query(ImportRowResult).filter(
        ImportRowResult.batch_id == batch.id
    ).order_by(ImportRowResult.row_number).all()

    return rows

