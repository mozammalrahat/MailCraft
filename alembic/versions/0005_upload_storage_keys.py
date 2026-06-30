"""Add resume storage key metadata to generated contents."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_upload_storage_keys"
down_revision: str | None = "0004_humanizer_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("generated_contents") as batch_op:
        batch_op.add_column(
            sa.Column("resume_storage_keys_json", sa.Text(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("generated_contents") as batch_op:
        batch_op.drop_column("resume_storage_keys_json")
