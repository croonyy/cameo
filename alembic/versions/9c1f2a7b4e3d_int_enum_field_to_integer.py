"""convert testmodel int_enum_field to integer

Revision ID: 9c1f2a7b4e3d
Revises: 5b885d8a9988
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c1f2a7b4e3d"
down_revision: Union[str, Sequence[str], None] = "5b885d8a9988"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        UPDATE testmodel
        SET int_enum_field = CASE int_enum_field
            WHEN 'ONE' THEN 1
            WHEN 'TWO' THEN 2
            WHEN 'THREE' THEN 3
            ELSE int_enum_field
        END
        WHERE int_enum_field IN ('ONE', 'TWO', 'THREE')
        """
    )
    with op.batch_alter_table("testmodel") as batch_op:
        batch_op.alter_column(
            "int_enum_field",
            existing_type=sa.Enum("ONE", "TWO", "THREE", name="intenumchoices"),
            type_=sa.Integer(),
            existing_nullable=True,
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        """
        UPDATE testmodel
        SET int_enum_field = CASE int_enum_field
            WHEN 1 THEN 'ONE'
            WHEN 2 THEN 'TWO'
            WHEN 3 THEN 'THREE'
            ELSE int_enum_field
        END
        WHERE int_enum_field IN (1, 2, 3)
        """
    )
    with op.batch_alter_table("testmodel") as batch_op:
        batch_op.alter_column(
            "int_enum_field",
            existing_type=sa.Integer(),
            type_=sa.Enum("ONE", "TWO", "THREE", name="intenumchoices"),
            existing_nullable=True,
        )
