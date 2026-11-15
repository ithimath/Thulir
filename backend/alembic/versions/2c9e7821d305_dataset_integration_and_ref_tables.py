"""dataset_integration_and_ref_tables

Revision ID: 2c9e7821d305
Revises: 1b7f5832a104
Create Date: 2026-11-05 23:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c9e7821d305'
down_revision: Union[str, None] = '1b7f5832a104'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------
    # 1. Reference Table: ref_student_performance
    # -------------------------------------------------------------
    op.create_table(
        'ref_student_performance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=32), nullable=False),
        sa.Column('school', sa.String(length=32), nullable=True),
        sa.Column('gender', sa.String(length=16), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('address', sa.String(length=16), nullable=True),
        sa.Column('family_size', sa.String(length=16), nullable=True),
        sa.Column('parents_status', sa.String(length=16), nullable=True),
        sa.Column('mother_edu', sa.Integer(), nullable=True),
        sa.Column('father_edu', sa.Integer(), nullable=True),
        sa.Column('mother_job', sa.String(length=64), nullable=True),
        sa.Column('father_job', sa.String(length=64), nullable=True),
        sa.Column('reason', sa.String(length=64), nullable=True),
        sa.Column('guardian', sa.String(length=32), nullable=True),
        sa.Column('travel_time', sa.Integer(), nullable=True),
        sa.Column('study_time', sa.Integer(), nullable=True),
        sa.Column('failures', sa.Integer(), nullable=True),
        sa.Column('school_support', sa.Integer(), nullable=True),
        sa.Column('family_support', sa.Integer(), nullable=True),
        sa.Column('paid_classes', sa.Integer(), nullable=True),
        sa.Column('activities', sa.Integer(), nullable=True),
        sa.Column('nursery', sa.Integer(), nullable=True),
        sa.Column('wants_higher_edu', sa.Integer(), nullable=True),
        sa.Column('internet', sa.Integer(), nullable=True),
        sa.Column('romantic', sa.Integer(), nullable=True),
        sa.Column('family_relationship', sa.Integer(), nullable=True),
        sa.Column('free_time', sa.Integer(), nullable=True),
        sa.Column('go_out', sa.Integer(), nullable=True),
        sa.Column('workday_alcohol', sa.Integer(), nullable=True),
        sa.Column('weekend_alcohol', sa.Integer(), nullable=True),
        sa.Column('health', sa.Integer(), nullable=True),
        sa.Column('absences', sa.Integer(), nullable=True),
        sa.Column('grade_p1', sa.Float(), nullable=True),
        sa.Column('grade_p2', sa.Float(), nullable=True),
        sa.Column('grade_final', sa.Float(), nullable=True),
        sa.Column('passed', sa.Integer(), nullable=True),
        sa.Column('grade_final_pct', sa.Float(), nullable=True),
        sa.Column('zero_final_flag', sa.Integer(), nullable=True),
        sa.Column('grade_trend', sa.Integer(), nullable=True),
        sa.Column('source_file', sa.String(length=128), nullable=False),
        sa.Column('imported_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('ref_student_performance', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ref_student_performance_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_ref_student_performance_record_id'), ['record_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_ref_student_performance_subject'), ['subject'], unique=False)

    # -------------------------------------------------------------
    # 2. Reference Table: ref_lms_engagement
    # -------------------------------------------------------------
    op.create_table(
        'ref_lms_engagement',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=False),
        sa.Column('gender', sa.String(length=16), nullable=True),
        sa.Column('nationality', sa.String(length=64), nullable=True),
        sa.Column('place_of_birth', sa.String(length=64), nullable=True),
        sa.Column('stage', sa.String(length=64), nullable=True),
        sa.Column('grade', sa.String(length=16), nullable=True),
        sa.Column('section', sa.String(length=16), nullable=True),
        sa.Column('topic', sa.String(length=64), nullable=True),
        sa.Column('semester', sa.String(length=32), nullable=True),
        sa.Column('relation', sa.String(length=32), nullable=True),
        sa.Column('raised_hands', sa.Integer(), nullable=True),
        sa.Column('visited_resources', sa.Integer(), nullable=True),
        sa.Column('announcements_view', sa.Integer(), nullable=True),
        sa.Column('discussion', sa.Integer(), nullable=True),
        sa.Column('parent_answered_survey', sa.String(length=16), nullable=True),
        sa.Column('parent_school_satisfaction', sa.String(length=32), nullable=True),
        sa.Column('absence_band', sa.String(length=32), nullable=True),
        sa.Column('performance_class', sa.String(length=16), nullable=True),
        sa.Column('source_file', sa.String(length=128), nullable=False),
        sa.Column('imported_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('ref_lms_engagement', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ref_lms_engagement_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_ref_lms_engagement_record_id'), ['record_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_ref_lms_engagement_performance_class'), ['performance_class'], unique=False)

    # -------------------------------------------------------------
    # 3. Reference Table: ref_higher_ed_dropout
    # -------------------------------------------------------------
    op.create_table(
        'ref_higher_ed_dropout',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=False),
        sa.Column('marital_status', sa.String(length=32), nullable=True),
        sa.Column('application_mode', sa.Integer(), nullable=True),
        sa.Column('application_order', sa.Integer(), nullable=True),
        sa.Column('course', sa.Integer(), nullable=True),
        sa.Column('daytime_attendance', sa.String(length=32), nullable=True),
        sa.Column('previous_qualification', sa.Integer(), nullable=True),
        sa.Column('nationality', sa.Integer(), nullable=True),
        sa.Column('mother_qualification', sa.Integer(), nullable=True),
        sa.Column('father_qualification', sa.Integer(), nullable=True),
        sa.Column('mother_occupation', sa.Integer(), nullable=True),
        sa.Column('father_occupation', sa.Integer(), nullable=True),
        sa.Column('displaced', sa.Integer(), nullable=True),
        sa.Column('educational_special_needs', sa.Integer(), nullable=True),
        sa.Column('debtor', sa.Integer(), nullable=True),
        sa.Column('tuition_fees_up_to_date', sa.Integer(), nullable=True),
        sa.Column('gender', sa.String(length=16), nullable=True),
        sa.Column('scholarship_holder', sa.Integer(), nullable=True),
        sa.Column('age_at_enrollment', sa.Integer(), nullable=True),
        sa.Column('international', sa.Integer(), nullable=True),
        sa.Column('sem1_credited', sa.Float(), nullable=True),
        sa.Column('sem1_enrolled', sa.Float(), nullable=True),
        sa.Column('sem1_evaluations', sa.Float(), nullable=True),
        sa.Column('sem1_approved', sa.Float(), nullable=True),
        sa.Column('sem1_grade', sa.Float(), nullable=True),
        sa.Column('sem1_without_eval', sa.Float(), nullable=True),
        sa.Column('sem2_credited', sa.Float(), nullable=True),
        sa.Column('sem2_enrolled', sa.Float(), nullable=True),
        sa.Column('sem2_evaluations', sa.Float(), nullable=True),
        sa.Column('sem2_approved', sa.Float(), nullable=True),
        sa.Column('sem2_grade', sa.Float(), nullable=True),
        sa.Column('sem2_without_eval', sa.Float(), nullable=True),
        sa.Column('unemployment_rate', sa.Float(), nullable=True),
        sa.Column('inflation_rate', sa.Float(), nullable=True),
        sa.Column('gdp', sa.Float(), nullable=True),
        sa.Column('outcome', sa.String(length=32), nullable=True),
        sa.Column('sem1_pass_rate', sa.Float(), nullable=True),
        sa.Column('sem2_pass_rate', sa.Float(), nullable=True),
        sa.Column('pass_rate_change', sa.Float(), nullable=True),
        sa.Column('grade_change', sa.Float(), nullable=True),
        sa.Column('dropout_flag', sa.Integer(), nullable=True),
        sa.Column('source_file', sa.String(length=128), nullable=False),
        sa.Column('imported_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('ref_higher_ed_dropout', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ref_higher_ed_dropout_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_ref_higher_ed_dropout_record_id'), ['record_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_ref_higher_ed_dropout_outcome'), ['outcome'], unique=False)

    # -------------------------------------------------------------
    # 4. Side Table: student_profiles
    # -------------------------------------------------------------
    op.create_table(
        'student_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('address', sa.String(length=32), nullable=True),
        sa.Column('family_size', sa.String(length=16), nullable=True),
        sa.Column('parents_status', sa.String(length=16), nullable=True),
        sa.Column('mother_edu', sa.Integer(), nullable=True),
        sa.Column('father_edu', sa.Integer(), nullable=True),
        sa.Column('mother_job', sa.String(length=64), nullable=True),
        sa.Column('father_job', sa.String(length=64), nullable=True),
        sa.Column('reason', sa.String(length=64), nullable=True),
        sa.Column('guardian', sa.String(length=32), nullable=True),
        sa.Column('travel_time', sa.Integer(), nullable=True),
        sa.Column('study_time', sa.Integer(), nullable=True),
        sa.Column('failures', sa.Integer(), nullable=True),
        sa.Column('school_support', sa.Integer(), nullable=True),
        sa.Column('family_support', sa.Integer(), nullable=True),
        sa.Column('paid_classes', sa.Integer(), nullable=True),
        sa.Column('activities', sa.Integer(), nullable=True),
        sa.Column('nursery', sa.Integer(), nullable=True),
        sa.Column('wants_higher_edu', sa.Integer(), nullable=True),
        sa.Column('internet', sa.Integer(), nullable=True),
        sa.Column('romantic', sa.Integer(), nullable=True),
        sa.Column('family_relationship', sa.Integer(), nullable=True),
        sa.Column('free_time', sa.Integer(), nullable=True),
        sa.Column('go_out', sa.Integer(), nullable=True),
        sa.Column('workday_alcohol', sa.Integer(), nullable=True),
        sa.Column('weekend_alcohol', sa.Integer(), nullable=True),
        sa.Column('health', sa.Integer(), nullable=True),
        sa.Column('raw_profile_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('student_profiles', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_student_profiles_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_profiles_student_id'), ['student_id'], unique=True)

    # -------------------------------------------------------------
    # 5. Side Table: student_engagement_metrics
    # -------------------------------------------------------------
    op.create_table(
        'student_engagement_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('stage', sa.String(length=64), nullable=True),
        sa.Column('topic', sa.String(length=64), nullable=True),
        sa.Column('semester', sa.String(length=32), nullable=True),
        sa.Column('relation', sa.String(length=32), nullable=True),
        sa.Column('raised_hands', sa.Integer(), nullable=True),
        sa.Column('visited_resources', sa.Integer(), nullable=True),
        sa.Column('announcements_view', sa.Integer(), nullable=True),
        sa.Column('discussion', sa.Integer(), nullable=True),
        sa.Column('parent_answered_survey', sa.String(length=16), nullable=True),
        sa.Column('parent_school_satisfaction', sa.String(length=32), nullable=True),
        sa.Column('absence_band', sa.String(length=32), nullable=True),
        sa.Column('performance_class', sa.String(length=16), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('student_engagement_metrics', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_student_engagement_metrics_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_student_engagement_metrics_student_id'), ['student_id'], unique=False)

    # -------------------------------------------------------------
    # 6. Add data_origin and source_ref to Operational Tables
    # -------------------------------------------------------------
    operational_tables = [
        'schools',
        'users',
        'classes_sections',
        'students',
        'attendance_records',
        'assessment_records',
        'assignment_records',
        'warning_indicators',
        'support_cases',
        'interventions',
        'student_support_requests',
        'import_batches',
        'data_corrections',
    ]

    for table_name in operational_tables:
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.add_column(sa.Column('data_origin', sa.String(length=16), server_default='user', nullable=False))
            batch_op.add_column(sa.Column('source_ref', sa.String(length=128), nullable=True))
            batch_op.create_index(batch_op.f(f'ix_{table_name}_data_origin'), ['data_origin'], unique=False)


def downgrade() -> None:
    operational_tables = [
        'data_corrections',
        'import_batches',
        'student_support_requests',
        'interventions',
        'support_cases',
        'warning_indicators',
        'assignment_records',
        'assessment_records',
        'attendance_records',
        'students',
        'classes_sections',
        'users',
        'schools',
    ]

    for table_name in operational_tables:
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.drop_index(batch_op.f(f'ix_{table_name}_data_origin'))
            batch_op.drop_column('source_ref')
            batch_op.drop_column('data_origin')

    op.drop_table('student_engagement_metrics')
    op.drop_table('student_profiles')
    op.drop_table('ref_higher_ed_dropout')
    op.drop_table('ref_lms_engagement')
    op.drop_table('ref_student_performance')
