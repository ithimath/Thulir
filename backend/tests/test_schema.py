import sqlite3
import pytest
from backend.app.config import settings
from backend.app.database import engine
from sqlalchemy import inspect

def test_database_schema_has_all_core_tables():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    
    expected_tables = {
        "schools",
        "users",
        "user_school_roles",
        "academic_years",
        "reporting_periods",
        "classes_sections",
        "students",
        "attendance_records",
        "assessment_records",
        "assignment_records",
        "warning_rules",
        "warning_indicators",
        "indicator_reviews",
        "support_cases",
        "interventions",
        "follow_ups",
        "case_notes",
        "import_batches",
        "import_row_results",
        "audit_log",
        "alembic_version",
    }
    
    for table in expected_tables:
        assert table in table_names, f"Table '{table}' missing from database schema"

def test_unique_constraints_exist():
    inspector = inspect(engine)
    # Check student uniqueness by school and emis_id
    student_unique = inspector.get_unique_constraints("students")
    unique_col_sets = [set(u["column_names"]) for u in student_unique]
    assert {"school_id", "emis_id"} in unique_col_sets

