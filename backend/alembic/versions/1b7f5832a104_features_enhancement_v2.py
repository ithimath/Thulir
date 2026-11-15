"""features_enhancement_v2

Revision ID: 1b7f5832a104
Revises: 0a6e44527093
Create Date: 2026-11-04 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b7f5832a104'
down_revision: Union[str, None] = '0a6e44527093'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create data_corrections table
    op.create_table(
        'data_corrections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('school_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('record_type', sa.String(length=32), nullable=False),
        sa.Column('target_record_id', sa.Integer(), nullable=False),
        sa.Column('superseding_record_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='Pending'),
        sa.Column('original_data', sa.JSON(), nullable=False),
        sa.Column('proposed_data', sa.JSON(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('proposed_by_id', sa.Integer(), nullable=False),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['proposed_by_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('data_corrections', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_data_corrections_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_data_corrections_school_id'), ['school_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_data_corrections_student_id'), ['student_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_data_corrections_record_type'), ['record_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_data_corrections_target_record_id'), ['target_record_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_data_corrections_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_data_corrections_proposed_by_id'), ['proposed_by_id'], unique=False)

    # 2. Add superseding columns to attendance_records
    with op.batch_alter_table('attendance_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_superseded', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('superseded_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('correction_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_att_correction', 'data_corrections', ['correction_id'], ['id'], ondelete='SET NULL')

    # 3. Add superseding columns to assessment_records
    with op.batch_alter_table('assessment_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_superseded', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('superseded_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('correction_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_asm_correction', 'data_corrections', ['correction_id'], ['id'], ondelete='SET NULL')

    # 4. Add superseding columns to assignment_records
    with op.batch_alter_table('assignment_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_superseded', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('superseded_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('correction_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_asg_correction', 'data_corrections', ['correction_id'], ['id'], ondelete='SET NULL')

    # 5. Add superseding columns to warning_indicators
    with op.batch_alter_table('warning_indicators', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_superseded', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('superseded_by_id', sa.Integer(), nullable=True))

    # 6. Add baseline_snapshot to interventions
    with op.batch_alter_table('interventions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('baseline_snapshot', sa.JSON(), nullable=True))

    # 7. Add rule configuration & version tracking columns to warning_rules
    with op.batch_alter_table('warning_rules', schema=None) as batch_op:
        batch_op.add_column(sa.Column('effective_from', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('change_reason', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('created_by_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_rule_creator', 'users', ['created_by_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    with op.batch_alter_table('warning_rules', schema=None) as batch_op:
        batch_op.drop_constraint('fk_rule_creator', type_='foreignkey')
        batch_op.drop_column('created_by_id')
        batch_op.drop_column('change_reason')
        batch_op.drop_column('effective_from')

    with op.batch_alter_table('interventions', schema=None) as batch_op:
        batch_op.drop_column('baseline_snapshot')

    with op.batch_alter_table('warning_indicators', schema=None) as batch_op:
        batch_op.drop_column('superseded_by_id')
        batch_op.drop_column('is_superseded')

    with op.batch_alter_table('assignment_records', schema=None) as batch_op:
        batch_op.drop_constraint('fk_asg_correction', type_='foreignkey')
        batch_op.drop_column('correction_id')
        batch_op.drop_column('superseded_by_id')
        batch_op.drop_column('is_superseded')

    with op.batch_alter_table('assessment_records', schema=None) as batch_op:
        batch_op.drop_constraint('fk_asm_correction', type_='foreignkey')
        batch_op.drop_column('correction_id')
        batch_op.drop_column('superseded_by_id')
        batch_op.drop_column('is_superseded')

    with op.batch_alter_table('attendance_records', schema=None) as batch_op:
        batch_op.drop_constraint('fk_att_correction', type_='foreignkey')
        batch_op.drop_column('correction_id')
        batch_op.drop_column('superseded_by_id')
        batch_op.drop_column('is_superseded')

    with op.batch_alter_table('data_corrections', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_data_corrections_proposed_by_id'))
        batch_op.drop_index(batch_op.f('ix_data_corrections_status'))
        batch_op.drop_index(batch_op.f('ix_data_corrections_target_record_id'))
        batch_op.drop_index(batch_op.f('ix_data_corrections_record_type'))
        batch_op.drop_index(batch_op.f('ix_data_corrections_student_id'))
        batch_op.drop_index(batch_op.f('ix_data_corrections_school_id'))
        batch_op.drop_index(batch_op.f('ix_data_corrections_id'))

    op.drop_table('data_corrections')

