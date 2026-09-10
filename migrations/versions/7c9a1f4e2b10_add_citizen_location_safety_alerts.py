"""add citizen location and safety alert events

Revision ID: 7c9a1f4e2b10
Revises: 602a424dacbf
Create Date: 2026-09-10
"""

from alembic import op
import sqlalchemy as sa


revision = "7c9a1f4e2b10"
down_revision = "602a424dacbf"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "citizen_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("accuracy_m", sa.Float(), nullable=True),
        sa.Column("tracking_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_citizen_locations_user_id"),
    )
    op.create_index("ix_citizen_locations_user_id", "citizen_locations", ["user_id"], unique=True)
    op.create_index("ix_citizen_locations_updated_at", "citizen_locations", ["updated_at"], unique=False)

    op.create_table(
        "safety_alert_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("distance_km", sa.Float(), nullable=False),
        sa.Column("email_sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notified_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "alert_id", name="uq_safety_alert_event_user_alert"),
    )
    op.create_index("ix_safety_alert_events_user_id", "safety_alert_events", ["user_id"], unique=False)
    op.create_index("ix_safety_alert_events_alert_id", "safety_alert_events", ["alert_id"], unique=False)
    op.create_index("ix_safety_alert_events_notified_at", "safety_alert_events", ["notified_at"], unique=False)


def downgrade():
    op.drop_index("ix_safety_alert_events_notified_at", table_name="safety_alert_events")
    op.drop_index("ix_safety_alert_events_alert_id", table_name="safety_alert_events")
    op.drop_index("ix_safety_alert_events_user_id", table_name="safety_alert_events")
    op.drop_table("safety_alert_events")
    op.drop_index("ix_citizen_locations_updated_at", table_name="citizen_locations")
    op.drop_index("ix_citizen_locations_user_id", table_name="citizen_locations")
    op.drop_table("citizen_locations")
