"""installations table + repository sync columns

Revision ID: c7d9e1f3a5b2
Revises: 61b8c3f28b29
Create Date: 2026-07-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7d9e1f3a5b2"
down_revision: Union[str, Sequence[str], None] = "61b8c3f28b29"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- installations table ---
    op.create_table(
        "installations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("github_installation_id", sa.Integer(), nullable=False),
        sa.Column("account_login", sa.String(), nullable=True),
        sa.Column("account_type", sa.String(), nullable=True),
        sa.Column("target_type", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_installations_id"), "installations", ["id"], unique=False)
    op.create_index(
        op.f("ix_installations_user_id"), "installations", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_installations_github_installation_id"),
        "installations",
        ["github_installation_id"],
        unique=True,
    )

    # --- repository sync columns ---
    op.add_column("repositories", sa.Column("github_id", sa.Integer(), nullable=True))
    op.add_column("repositories", sa.Column("private", sa.Boolean(), nullable=True))
    op.add_column(
        "repositories",
        sa.Column(
            "active", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
    )
    op.create_index(
        op.f("ix_repositories_github_id"), "repositories", ["github_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_repositories_github_id"), table_name="repositories")
    op.drop_column("repositories", "active")
    op.drop_column("repositories", "private")
    op.drop_column("repositories", "github_id")

    op.drop_index(
        op.f("ix_installations_github_installation_id"), table_name="installations"
    )
    op.drop_index(op.f("ix_installations_user_id"), table_name="installations")
    op.drop_index(op.f("ix_installations_id"), table_name="installations")
    op.drop_table("installations")
