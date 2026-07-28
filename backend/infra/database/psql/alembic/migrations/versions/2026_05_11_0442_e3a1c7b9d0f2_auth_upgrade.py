"""auth upgrade: user_email conjoint index + user.username_confirmed

Revision ID: e3a1c7b9d0f2
Revises: da347f581faa
Create Date: 2026-05-11 04:42:00.000000

Adds the ``user_email`` table — the single authority that keeps every email a
user owns (their primary + each OAuth provider's reported email) globally unique
via a unique index on the aggressively-normalized ``normalized_email`` — and the
``user.username_confirmed`` gate used by the choose-username flow.

Backfill order matters: account primaries win, then provider emails are inserted
only where their canonical form is still free (``ON CONFLICT DO NOTHING``). Any
pre-existing cross-account duplicate emails are therefore skipped rather than
failing the migration; a NOTICE reports how many primaries could not be seeded so
they can be reconciled by hand. Existing users all default ``username_confirmed``
to ``true`` (they already carry a stable handle); only fresh OAuth accounts start
``false`` until the user confirms one at onboarding.
"""

# ruff: noqa: S608 - backfill SQL interpolates only fixed column names, never user input
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e3a1c7b9d0f2"
down_revision: str | None = "da347f581faa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _canonical(column: str) -> str:
    """SQL that mirrors the aggressive runtime canonicalizer for backfill.

    Lowercase + trim, strip any ``+tag``, and for Gmail/Googlemail also strip dots
    and normalize the domain to ``gmail.com``.
    """
    lowered = f"lower(trim({column}))"
    gmail_local = f"replace(split_part(split_part({lowered}, '@', 1), '+', 1), '.', '')"
    domain = f"split_part({lowered}, '@', 2)"
    return (
        "CASE "
        f"WHEN {domain} IN ('gmail.com', 'googlemail.com') "
        f"THEN {gmail_local} || '@gmail.com' "
        f"ELSE {lowered} "
        "END"
    )


def upgrade() -> None:
    op.create_table(
        "user_email",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("normalized_email", sa.String(length=255), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk_user_email_user_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_email")),
    )
    op.create_index(
        op.f("ix_user_email_user_email_user_id"), "user_email", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_user_email_user_email_normalized_email"),
        "user_email",
        ["normalized_email"],
        unique=True,
    )

    op.add_column(
        "user",
        sa.Column(
            "username_confirmed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    # Backfill primaries first — the account's own email is authoritative.
    op.execute(
        f"""
        INSERT INTO user_email
            (id, created_at, updated_at, user_id, email, normalized_email,
             is_primary, provider, verified_at)
        SELECT gen_random_uuid(), now(), now(), u.id, u.email,
               {_canonical("u.email")}, true, NULL, u.verified_at
        FROM "user" u
        WHERE u.email IS NOT NULL
        ON CONFLICT (normalized_email) DO NOTHING
        """
    )

    # Then provider emails, only where the canonical form is still free.
    op.execute(
        f"""
        INSERT INTO user_email
            (id, created_at, updated_at, user_id, email, normalized_email,
             is_primary, provider, verified_at)
        SELECT gen_random_uuid(), now(), now(), i.user_id, i.provider_email,
               {_canonical("i.provider_email")}, false, i.provider, now()
        FROM identity i
        WHERE i.provider_email IS NOT NULL
        ON CONFLICT (normalized_email) DO NOTHING
        """
    )

    # Surface any primaries that collided and were skipped, for manual reconcile.
    op.execute(
        """
        DO $$
        DECLARE skipped integer;
        BEGIN
            SELECT count(*) INTO skipped
            FROM "user" u
            WHERE u.email IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM user_email ue
                  WHERE ue.user_id = u.id AND ue.is_primary
              );
            IF skipped > 0 THEN
                RAISE NOTICE
                    'user_email backfill: % user(s) skipped (duplicate email) — reconcile manually',
                    skipped;
            END IF;
        END $$
        """
    )


def downgrade() -> None:
    op.drop_column("user", "username_confirmed")
    op.drop_index(op.f("ix_user_email_user_email_normalized_email"), table_name="user_email")
    op.drop_index(op.f("ix_user_email_user_email_user_id"), table_name="user_email")
    op.drop_table("user_email")
