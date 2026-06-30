"""Add generation_jobs table for async generation."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_generation_jobs"
down_revision: str | None = "0005_upload_storage_keys"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column(
            "result_generation_id",
            sa.Integer(),
            sa.ForeignKey("generated_contents.id"),
            nullable=True,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_generation_jobs_user_id", "generation_jobs", ["user_id"])
    op.create_index("ix_generation_jobs_status", "generation_jobs", ["status"])
    op.create_index("ix_generation_jobs_kind", "generation_jobs", ["kind"])
    op.create_index("ix_generation_jobs_created_at", "generation_jobs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_generation_jobs_created_at", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_kind", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_status", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_user_id", table_name="generation_jobs")
    op.drop_table("generation_jobs")
