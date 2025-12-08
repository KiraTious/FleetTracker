"""expand password length for user passwords

Revision ID: 1c64bf2e2e4a
Revises: b73bdc69f02e
Create Date: 2025-12-08 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1c64bf2e2e4a'
down_revision = 'b73bdc69f02e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('password', existing_type=sa.String(length=100), type_=sa.String(length=255), nullable=False)


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('password', existing_type=sa.String(length=255), type_=sa.String(length=100), nullable=False)
