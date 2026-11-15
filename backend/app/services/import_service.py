"""Data Import validation and transactional commit service (Phase 4)."""
import io
import datetime
from typing import Dict, Any, List, Tuple
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models.models import (
    ImportBatch,
    ImportRowResult,
    Student,
    AttendanceRecord,
    AssessmentRecord,
    ClassSection,
    AcademicYear,
    ReportingPeriod,
)

# Common header aliases used across government school CSV/XLSX records
HEADER_ALIASES = {
    "emis_id": ["emis_id", "emis", "emis id", "emis_no", "emis no", "student_emis", "student emis"],
    "full_name": ["full_name", "student_name", "student name", "name", "pupil_name", "pupil name"],
    "grade": ["grade", "class", "std", "standard"],
    "section": ["section", "sec"],
    "dob": ["dob", "date_of_birth", "date of birth", "birth_date"],
    "gender": ["gender", "sex"],
    "academic_year": ["academic_year", "year", "session"],
    "reporting_period": ["reporting_period", "period", "term", "month"],
    "total_days": ["total_days", "working_days", "total working days", "total days"],
    "attended_days": ["attended_days", "present_days", "days present", "attended days"],
    "subject": ["subject", "subject_name", "course"],
    "marks_obtained": ["marks_obtained", "marks", "score", "mark"],
    "max_marks": ["max_marks", "total_marks", "maximum marks", "max marks", "out_of"],
    "assessment_type": ["assessment_type", "exam_type", "type", "test_type"],
}

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize DataFrame column names using standard aliases and trimming."""
    col_mapping = {}
    for col in df.columns:
        clean = str(col).strip().lower().replace("-", "_")
        matched = False
        for standard_key, aliases in HEADER_ALIASES.items():
            if clean in aliases:
                col_mapping[col] = standard_key
                matched = True
                break
        if not matched:
            col_mapping[col] = clean
    return df.rename(columns=col_mapping)

def parse_file_to_dataframe(content: bytes, filename: str) -> pd.DataFrame:
    """Parse raw bytes into pandas DataFrame from CSV or XLSX with multi-sheet support."""
    if filename.lower().endswith(('.xlsx', '.xls')):
        excel_file = pd.ExcelFile(io.BytesIO(content))
        # If multi-sheet, search for relevant sheet name or pick the first sheet
        target_sheet = excel_file.sheet_names[0]
        for name in excel_file.sheet_names:
            if any(k in name.lower() for k in ["student", "attendance", "mark", "data", "sheet1"]):
                target_sheet = name
                break
        df = pd.read_excel(excel_file, sheet_name=target_sheet)
    else:
        # Default to CSV
        try:
            df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(content), encoding='latin1')
    
    # Normalize headers
    df = normalize_columns(df)

    # Strip whitespace from string cells cleanly without deprecated select_dtypes behavior
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].astype(str).str.strip()
    return df

def validate_student_rows(
    df: pd.DataFrame,
    school_id: int,
    db: Session,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Validate student import rows and detect duplicates/errors."""
    required_cols = {"emis_id", "full_name", "grade", "section"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in student file: {', '.join(missing)}")

    # Fetch existing EMIS IDs in this school
    existing_emis = set(
        r[0] for r in db.query(Student.emis_id).filter(Student.school_id == school_id).all()
    )

    seen_in_file = set()
    rows_analysis = []
    stats = {"valid": 0, "warnings": 0, "rejected": 0, "duplicates": 0}

    for idx, row in df.iterrows():
        row_num = idx + 1
        raw_data = row.to_dict()
        emis = str(row.get("emis_id", "")).strip()
        name = str(row.get("full_name", "")).strip()
        grade_str = str(row.get("grade", "")).strip()
        sec = str(row.get("section", "")).strip().upper()

        if not emis or emis.lower() == 'nan':
            category = "rejected"
            message = "EMIS ID is missing or empty."
            stats["rejected"] += 1
        elif not name or name.lower() == 'nan':
            category = "rejected"
            message = "Student name is missing or empty."
            stats["rejected"] += 1
        elif emis in seen_in_file:
            category = "skipped_duplicate"
            message = f"Duplicate EMIS ID '{emis}' in same upload file; row skipped."
            stats["duplicates"] += 1
        elif emis in existing_emis:
            category = "updated_existing"
            message = f"Student with EMIS '{emis}' already exists in school; existing record will be updated."
            stats["warnings"] += 1
        else:
            try:
                g = int(float(grade_str))
                if not (1 <= g <= 12):
                    category = "rejected"
                    message = f"Invalid grade {g}. Must be between 1 and 12."
                    stats["rejected"] += 1
                else:
                    category = "imported"
                    message = "Valid student record ready for import."
                    stats["valid"] += 1
                    seen_in_file.add(emis)
            except (ValueError, TypeError):
                category = "rejected"
                message = f"Invalid grade value '{grade_str}'."
                stats["rejected"] += 1

        rows_analysis.append({
            "row_number": row_num,
            "raw_data": raw_data,
            "category": category,
            "message": message,
        })

    return rows_analysis, stats

def commit_student_import(
    batch: ImportBatch,
    rows_analysis: List[Dict[str, Any]],
    school_id: int,
    db: Session,
) -> Dict[str, int]:
    """Execute transactional commit for validated student records."""
    # Find or resolve academic year
    ay = db.query(AcademicYear).filter(
        AcademicYear.school_id == school_id,
        AcademicYear.is_current == True
    ).first()

    imported = 0
    duplicates = 0
    rejected = 0

    try:
        for r in rows_analysis:
            category = r["category"]
            raw = r["raw_data"]
            row_num = r["row_number"]
            msg = r["message"]

            if category in ["imported", "updated_existing"]:
                emis = str(raw["emis_id"]).strip()
                name = str(raw["full_name"]).strip()
                grade = int(float(raw["grade"]))
                sec = str(raw["section"]).strip().upper()
                gender = str(raw.get("gender", "")).strip() or None
                guardian = str(raw.get("guardian_name", "")).strip() or None
                phone = str(raw.get("guardian_phone", "")).strip() or None

                # Resolve or create ClassSection if needed
                cs = None
                if ay:
                    cs = db.query(ClassSection).filter(
                        ClassSection.school_id == school_id,
                        ClassSection.academic_year_id == ay.id,
                        ClassSection.grade == grade,
                        ClassSection.section == sec,
                    ).first()
                    if not cs:
                        cs = ClassSection(
                            school_id=school_id,
                            academic_year_id=ay.id,
                            grade=grade,
                            section=sec,
                        )
                        db.add(cs)
                        db.flush()

                st = db.query(Student).filter(
                    Student.school_id == school_id,
                    Student.emis_id == emis
                ).first()

                if not st:
                    st = Student(
                        school_id=school_id,
                        emis_id=emis,
                        full_name=name,
                        gender=gender,
                        current_class_section_id=cs.id if cs else None,
                        guardian_name=guardian,
                        guardian_phone=phone,
                        is_active=True,
                    )
                    db.add(st)
                    imported += 1
                else:
                    # Update fields
                    st.full_name = name
                    if cs:
                        st.current_class_section_id = cs.id
                    if gender:
                        st.gender = gender
                    if guardian:
                        st.guardian_name = guardian
                    if phone:
                        st.guardian_phone = phone
                    duplicates += 1
            else:
                rejected += 1

            # Log row-level audit record
            row_res = ImportRowResult(
                batch_id=batch.id,
                row_number=row_num,
                raw_data=raw,
                category=category,
                message=msg,
            )
            db.add(row_res)

        batch.status = "committed"
        batch.imported_count = imported
        batch.duplicates_count = duplicates
        batch.rejected_count = rejected
        batch.committed_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()

        return {
            "imported": imported,
            "duplicates": duplicates,
            "rejected": rejected,
        }
    except Exception as e:
        db.rollback()
        batch.status = "failed"
        batch.error_summary = str(e)
        db.commit()
        raise e


def validate_attendance_rows(
    df: pd.DataFrame,
    school_id: int,
    db: Session,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Validate attendance import rows and verify student references."""
    required_cols = {"emis_id", "total_days", "attended_days"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in attendance file: {', '.join(missing)}")

    # Fetch existing EMIS to student_id map
    student_map = {
        s.emis_id: s.id for s in db.query(Student.emis_id, Student.id).filter(
            Student.school_id == school_id, Student.is_active == True
        ).all()
    }

    rows_analysis = []
    stats = {"valid": 0, "warnings": 0, "rejected": 0, "duplicates": 0}

    for idx, row in df.iterrows():
        row_num = idx + 1
        raw_data = row.to_dict()
        emis = str(row.get("emis_id", "")).strip()

        if not emis or emis.lower() == 'nan':
            category = "rejected"
            message = "EMIS ID is missing."
            stats["rejected"] += 1
        elif emis not in student_map:
            category = "rejected"
            message = f"Student with EMIS '{emis}' not found in school directory."
            stats["rejected"] += 1
        else:
            try:
                tot = float(row.get("total_days", 0))
                att = float(row.get("attended_days", 0))
                if tot <= 0:
                    category = "rejected"
                    message = f"Total instructional days must be greater than 0 (got {tot})."
                    stats["rejected"] += 1
                elif att < 0 or att > tot:
                    category = "rejected"
                    message = f"Attended days ({att}) must be between 0 and total days ({tot})."
                    stats["rejected"] += 1
                else:
                    category = "imported"
                    pct = round((att / tot) * 100, 1)
                    message = f"Valid attendance: {att}/{tot} days ({pct}%)."
                    stats["valid"] += 1
            except (ValueError, TypeError):
                category = "rejected"
                message = "Invalid numeric values for total_days or attended_days."
                stats["rejected"] += 1

        rows_analysis.append({
            "row_number": row_num,
            "raw_data": raw_data,
            "category": category,
            "message": message,
        })

    return rows_analysis, stats


def commit_attendance_import(
    batch: ImportBatch,
    rows_analysis: List[Dict[str, Any]],
    school_id: int,
    db: Session,
) -> Dict[str, int]:
    """Execute transactional commit for attendance records."""
    from backend.app.services.warning_engine import run_student_indicators

    # Resolve active reporting period
    curr_period = db.query(ReportingPeriod).join(
        AcademicYear, ReportingPeriod.academic_year_id == AcademicYear.id
    ).filter(
        AcademicYear.school_id == school_id,
        ReportingPeriod.is_current == True
    ).first()

    # Fallback to latest reporting period if is_current not flagged
    if not curr_period:
        curr_period = db.query(ReportingPeriod).join(
            AcademicYear, ReportingPeriod.academic_year_id == AcademicYear.id
        ).filter(AcademicYear.school_id == school_id).order_by(ReportingPeriod.id.desc()).first()

    student_map = {
        s.emis_id: s.id for s in db.query(Student.emis_id, Student.id).filter(
            Student.school_id == school_id
        ).all()
    }

    imported = 0
    duplicates = 0
    rejected = 0
    affected_students = set()

    try:
        for r in rows_analysis:
            if r["category"] != "imported":
                rejected += 1
                continue

            raw = r["raw_data"]
            emis = str(raw["emis_id"]).strip()
            student_id = student_map[emis]
            tot = float(raw["total_days"])
            att = float(raw["attended_days"])
            pct = round((att / tot) * 100, 2)
            period_name = str(raw.get("reporting_period", "")).strip()

            target_period = curr_period
            if period_name:
                custom_period = db.query(ReportingPeriod).join(
                    AcademicYear, ReportingPeriod.academic_year_id == AcademicYear.id
                ).filter(
                    AcademicYear.school_id == school_id,
                    ReportingPeriod.name.ilike(period_name)
                ).first()
                if custom_period:
                    target_period = custom_period

            period_id = target_period.id if target_period else None

            # Check if record already exists for this period
            existing = None
            if period_id:
                existing = db.query(AttendanceRecord).filter(
                    AttendanceRecord.student_id == student_id,
                    AttendanceRecord.reporting_period_id == period_id,
                    AttendanceRecord.record_date == None,
                ).first()

            if existing:
                existing.days_present = att
                existing.total_instructional_days = tot
                existing.attendance_percentage = pct
                existing.data_origin = "user"
                existing.source_ref = f"import_batch_{batch.id}"
                duplicates += 1
            else:
                new_rec = AttendanceRecord(
                    student_id=student_id,
                    school_id=school_id,
                    reporting_period_id=period_id,
                    days_present=att,
                    total_instructional_days=tot,
                    attendance_percentage=pct,
                    data_origin="user",
                    source_ref=f"import_batch_{batch.id}",
                )
                db.add(new_rec)
                imported += 1

            affected_students.add(student_id)

            row_res = ImportRowResult(
                batch_id=batch.id,
                row_number=r["row_number"],
                raw_data=raw,
                category=r["category"],
                message=r["message"],
            )
            db.add(row_res)

        batch.status = "committed"
        batch.imported_count = imported
        batch.duplicates_count = duplicates
        batch.rejected_count = rejected
        batch.committed_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()

        # Recalculate early-warning indicators for all updated students
        for sid in affected_students:
            run_student_indicators(db, sid, school_id)

        return {
            "imported": imported,
            "duplicates": duplicates,
            "rejected": rejected,
        }
    except Exception as e:
        db.rollback()
        batch.status = "failed"
        batch.error_summary = str(e)
        db.commit()
        raise e


def validate_marks_rows(
    df: pd.DataFrame,
    school_id: int,
    db: Session,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Validate assessment/exam marks import rows."""
    required_cols = {"emis_id", "subject", "marks_obtained"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in assessment file: {', '.join(missing)}")

    student_map = {
        s.emis_id: s.id for s in db.query(Student.emis_id, Student.id).filter(
            Student.school_id == school_id, Student.is_active == True
        ).all()
    }

    rows_analysis = []
    stats = {"valid": 0, "warnings": 0, "rejected": 0, "duplicates": 0}

    for idx, row in df.iterrows():
        row_num = idx + 1
        raw_data = row.to_dict()
        emis = str(row.get("emis_id", "")).strip()
        subj = str(row.get("subject", "")).strip()

        if not emis or emis.lower() == 'nan':
            category = "rejected"
            message = "EMIS ID is missing."
            stats["rejected"] += 1
        elif emis not in student_map:
            category = "rejected"
            message = f"Student with EMIS '{emis}' not found in school directory."
            stats["rejected"] += 1
        elif not subj or subj.lower() == 'nan':
            category = "rejected"
            message = "Subject name is missing."
            stats["rejected"] += 1
        else:
            try:
                obt = float(row.get("marks_obtained", 0))
                mx = float(row.get("max_marks", 100))
                if mx <= 0:
                    category = "rejected"
                    message = f"Max marks must be greater than 0 (got {mx})."
                    stats["rejected"] += 1
                elif obt < 0 or obt > mx:
                    category = "rejected"
                    message = f"Marks obtained ({obt}) must be between 0 and maximum marks ({mx})."
                    stats["rejected"] += 1
                else:
                    category = "imported"
                    pct = round((obt / mx) * 100, 1)
                    message = f"Valid score: {obt}/{mx} in {subj} ({pct}%)."
                    stats["valid"] += 1
            except (ValueError, TypeError):
                category = "rejected"
                message = "Invalid numeric marks_obtained or max_marks."
                stats["rejected"] += 1

        rows_analysis.append({
            "row_number": row_num,
            "raw_data": raw_data,
            "category": category,
            "message": message,
        })

    return rows_analysis, stats


def commit_marks_import(
    batch: ImportBatch,
    rows_analysis: List[Dict[str, Any]],
    school_id: int,
    db: Session,
) -> Dict[str, int]:
    """Execute transactional commit for assessment marks."""
    from backend.app.services.warning_engine import run_student_indicators

    curr_period = db.query(ReportingPeriod).join(
        AcademicYear, ReportingPeriod.academic_year_id == AcademicYear.id
    ).filter(
        AcademicYear.school_id == school_id,
        ReportingPeriod.is_current == True
    ).first()

    if not curr_period:
        curr_period = db.query(ReportingPeriod).join(
            AcademicYear, ReportingPeriod.academic_year_id == AcademicYear.id
        ).filter(AcademicYear.school_id == school_id).order_by(ReportingPeriod.id.desc()).first()

    student_map = {
        s.emis_id: s.id for s in db.query(Student.emis_id, Student.id).filter(
            Student.school_id == school_id
        ).all()
    }

    imported = 0
    duplicates = 0
    rejected = 0
    affected_students = set()

    try:
        for r in rows_analysis:
            if r["category"] != "imported":
                rejected += 1
                continue

            raw = r["raw_data"]
            emis = str(raw["emis_id"]).strip()
            student_id = student_map[emis]
            subj = str(raw["subject"]).strip()
            obt = float(raw["marks_obtained"])
            mx = float(raw.get("max_marks", 100))
            pct = round((obt / mx) * 100, 2)
            exam_name = str(raw.get("assessment_type", raw.get("assessment_name", "Assessment"))).strip()
            period_name = str(raw.get("reporting_period", "")).strip()

            target_period = curr_period
            if period_name:
                custom_period = db.query(ReportingPeriod).join(
                    AcademicYear, ReportingPeriod.academic_year_id == AcademicYear.id
                ).filter(
                    AcademicYear.school_id == school_id,
                    ReportingPeriod.name.ilike(period_name)
                ).first()
                if custom_period:
                    target_period = custom_period

            period_id = target_period.id if target_period else None

            # Check if record already exists for student, subject, and exam_name
            existing = db.query(AssessmentRecord).filter(
                AssessmentRecord.student_id == student_id,
                AssessmentRecord.subject == subj,
                AssessmentRecord.assessment_name == exam_name,
            ).first()

            if existing:
                existing.marks_obtained = obt
                existing.max_marks = mx
                existing.percentage = pct
                existing.reporting_period_id = period_id
                existing.data_origin = "user"
                existing.source_ref = f"import_batch_{batch.id}"
                duplicates += 1
            else:
                new_rec = AssessmentRecord(
                    student_id=student_id,
                    school_id=school_id,
                    reporting_period_id=period_id,
                    subject=subj,
                    assessment_name=exam_name,
                    assessment_date=datetime.date.today(),
                    marks_obtained=obt,
                    max_marks=mx,
                    percentage=pct,
                    data_origin="user",
                    source_ref=f"import_batch_{batch.id}",
                )
                db.add(new_rec)
                imported += 1

            affected_students.add(student_id)

            row_res = ImportRowResult(
                batch_id=batch.id,
                row_number=r["row_number"],
                raw_data=raw,
                category=r["category"],
                message=r["message"],
            )
            db.add(row_res)

        batch.status = "committed"
        batch.imported_count = imported
        batch.duplicates_count = duplicates
        batch.rejected_count = rejected
        batch.committed_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()

        # Recalculate indicators for updated students
        for sid in affected_students:
            run_student_indicators(db, sid, school_id)

        return {
            "imported": imported,
            "duplicates": duplicates,
            "rejected": rejected,
        }
    except Exception as e:
        db.rollback()
        batch.status = "failed"
        batch.error_summary = str(e)
        db.commit()
        raise e

