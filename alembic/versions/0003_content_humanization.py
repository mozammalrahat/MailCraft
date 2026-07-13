"""Add raw content fields for humanization comparison."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_content_humanization"
down_revision: str | None = "0002_unified_generated_content"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("generated_contents") as batch_op:
        batch_op.add_column(
            sa.Column("raw_subject", sa.String(length=500), nullable=True)
        )
        batch_op.add_column(sa.Column("raw_body", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "humanization_applied",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("generated_contents") as batch_op:
        batch_op.drop_column("humanization_applied")
        batch_op.drop_column("raw_body")
        batch_op.drop_column("raw_subject")
