"""Add humanizer metadata columns to generated_contents."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_humanizer_metadata"
down_revision: str | None = "0003_content_humanization"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("generated_contents") as batch_op:
        batch_op.add_column(
            sa.Column("humanizer_model_name", sa.String(length=120), nullable=True)
        )
        batch_op.add_column(
            sa.Column("humanizer_prompt_version", sa.String(length=32), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("generated_contents") as batch_op:
        batch_op.drop_column("humanizer_prompt_version")
        batch_op.drop_column("humanizer_model_name")
