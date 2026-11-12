"""Initial SkillScope AI database schema with 16 tables

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-11-11 20:45:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

from app.database.session import Base
import app.models  # noqa: F401

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
