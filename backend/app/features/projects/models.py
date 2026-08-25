"""Project feature model: the minimum schema Phase 3 (Project Registration)
requires and nothing more.

Deliberately excluded (belongs to later phases, per docs/ROADMAP.md and
docs/FUTURE_NOT_IN_SCOPE.md): token symbol/supply/decimals, presale
configuration, vesting configuration, liquidity configuration. Adding those
now would mean guessing at a schema before the phase that actually defines
their requirements exists — better to add a migration later than carry
speculative, possibly-wrong columns now.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.features.auth.models import User


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A registered LaunchPad project.

    Ownership is the security boundary for this whole feature: `owner_id`
    is set exactly once, at creation, from the authenticated user's id —
    never from client input (see `service.create_project`) — and every
    route that reads or writes a specific project must verify the
    authenticated user is that owner (see `dependencies.get_owned_project`).
    """

    __tablename__ = "projects"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Server-derived from `name` at creation time (see service.py) — never
    # accepted as client input, so it can't be used to squat/collide with
    # another project's identity or inject unexpected characters into a
    # value that may end up in URLs later. Immutable after creation:
    # renaming a project does not change its slug, so nothing that already
    # referenced this project by slug breaks.
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)

    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Mirrors the `is_active` convention already established on `User`
    # (see app/features/auth/models.py) rather than introducing a new
    # status-enum pattern for what is, at this phase, a simple on/off
    # lifecycle flag. A richer status model (e.g. draft/review/live) can
    # be added in a later migration once a later phase actually needs one
    # — there is no current requirement calling for it.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    owner: Mapped["User"] = relationship()
