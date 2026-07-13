"""Unified generated_contents table and data migration."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_unified_generated_content"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "generated_contents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("generation_kind", sa.String(length=32), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("intent", sa.Text(), nullable=True),
        sa.Column("key_facts_json", sa.Text(), nullable=True),
        sa.Column("tone", sa.String(length=32), nullable=True),
        sa.Column("strategy", sa.String(length=32), nullable=True),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("prompt_version", sa.String(length=32), nullable=True),
        sa.Column("scenario_id", sa.Integer(), nullable=True),
        sa.Column("purpose", sa.String(length=32), nullable=True),
        sa.Column("document_type", sa.String(length=32), nullable=True),
        sa.Column("position_description", sa.Text(), nullable=True),
        sa.Column("grounding_links_json", sa.Text(), nullable=True),
        sa.Column("cv_filenames_json", sa.Text(), nullable=True),
        sa.Column("cv_extracted_text", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("grounding_metadata_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generated_contents_user_id", "generated_contents", ["user_id"])
    op.create_index(
        "ix_generated_contents_generation_kind",
        "generated_contents",
        ["generation_kind"],
    )
    op.create_index(
        "ix_generated_contents_scenario_id", "generated_contents", ["scenario_id"]
    )
    op.create_index("ix_generated_contents_purpose", "generated_contents", ["purpose"])
    op.create_index(
        "ix_generated_contents_document_type",
        "generated_contents",
        ["document_type"],
    )
    op.create_index(
        "ix_generated_contents_created_at", "generated_contents", ["created_at"]
    )

    # Migrate existing application documents
    op.execute(
        sa.text(
            """
            INSERT INTO generated_contents (
                id, user_id, generation_kind, subject, body, created_at,
                scenario_id, purpose, document_type, position_description,
                grounding_links_json, cv_filenames_json, cv_extracted_text,
                metadata_json, grounding_metadata_json
            )
            SELECT
                id, user_id, 'application_document', subject, body, created_at,
                scenario_id, purpose, document_type, position_description,
                grounding_links_json, cv_filenames_json, cv_extracted_text,
                metadata_json, grounding_metadata_json
            FROM generated_documents
            """
        )
    )

    op.drop_index("ix_generated_documents_created_at", table_name="generated_documents")
    op.drop_index(
        "ix_generated_documents_document_type", table_name="generated_documents"
    )
    op.drop_index("ix_generated_documents_purpose", table_name="generated_documents")
    op.drop_index(
        "ix_generated_documents_scenario_id", table_name="generated_documents"
    )
    op.drop_index("ix_generated_documents_user_id", table_name="generated_documents")
    op.drop_table("generated_documents")


def downgrade() -> None:
    op.create_table(
        "generated_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("scenario_id", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("position_description", sa.Text(), nullable=False),
        sa.Column("grounding_links_json", sa.Text(), nullable=False),
        sa.Column("cv_filenames_json", sa.Text(), nullable=False),
        sa.Column("cv_extracted_text", sa.Text(), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("grounding_metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_generated_documents_user_id", "generated_documents", ["user_id"]
    )
    op.create_index(
        "ix_generated_documents_scenario_id",
        "generated_documents",
        ["scenario_id"],
    )
    op.create_index(
        "ix_generated_documents_purpose", "generated_documents", ["purpose"]
    )
    op.create_index(
        "ix_generated_documents_document_type",
        "generated_documents",
        ["document_type"],
    )
    op.create_index(
        "ix_generated_documents_created_at", "generated_documents", ["created_at"]
    )

    op.execute(
        sa.text(
            """
            INSERT INTO generated_documents (
                id, user_id, scenario_id, purpose, document_type,
                position_description, grounding_links_json, cv_filenames_json,
                cv_extracted_text, subject, body, metadata_json,
                grounding_metadata_json, created_at
            )
            SELECT
                id, user_id, scenario_id, purpose, document_type,
                position_description, grounding_links_json, cv_filenames_json,
                cv_extracted_text, subject, body, metadata_json,
                grounding_metadata_json, created_at
            FROM generated_contents
            WHERE generation_kind = 'application_document'
            """
        )
    )

    op.drop_index("ix_generated_contents_created_at", table_name="generated_contents")
    op.drop_index(
        "ix_generated_contents_document_type", table_name="generated_contents"
    )
    op.drop_index("ix_generated_contents_purpose", table_name="generated_contents")
    op.drop_index("ix_generated_contents_scenario_id", table_name="generated_contents")
    op.drop_index(
        "ix_generated_contents_generation_kind", table_name="generated_contents"
    )
    op.drop_index("ix_generated_contents_user_id", table_name="generated_contents")
    op.drop_table("generated_contents")
