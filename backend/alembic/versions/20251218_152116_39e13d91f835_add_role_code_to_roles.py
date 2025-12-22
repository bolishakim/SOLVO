"""add_role_code_to_roles

Revision ID: 39e13d91f835
Revises: e1c4956ec992
Create Date: 2025-12-18 15:21:16.714058+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39e13d91f835'
down_revision: Union[str, None] = 'e1c4956ec992'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Step 1: Add column as nullable first
    op.add_column('roles', sa.Column('role_code', sa.String(length=50), nullable=True), schema='core_app')

    # Step 2: Update existing roles with role_code values
    op.execute("""
        UPDATE core_app.roles
        SET role_code = CASE
            WHEN role_name = 'Admin' THEN 'admin'
            WHEN role_name = 'Standard User' THEN 'standard_user'
            WHEN role_name = 'Viewer' THEN 'viewer'
            ELSE LOWER(REPLACE(role_name, ' ', '_'))
        END
    """)

    # Step 3: Make column non-nullable
    op.alter_column('roles', 'role_code', nullable=False, schema='core_app')

    # Step 4: Create unique index
    op.create_index(op.f('ix_core_app_roles_role_code'), 'roles', ['role_code'], unique=True, schema='core_app')


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index(op.f('ix_core_app_roles_role_code'), table_name='roles', schema='core_app')
    op.drop_column('roles', 'role_code', schema='core_app')
