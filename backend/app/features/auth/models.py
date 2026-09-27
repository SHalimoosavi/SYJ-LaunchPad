"""Auth feature models: User, Wallet, SiweNonce.

These are intentionally minimal here — Phase 3 ("Core Data Model") will
extend `User`/`Wallet` with the relationships every other feature needs
(purchases, claims, referrals, ...). Auth only owns what it needs to
authenticate someone: identity, their wallet(s), and replay-protected
sign-in nonces.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(enum.StrEnum):
    """RBAC foundation. Phase 8 (Admin Dashboard) builds permission checks
    on top of this; we define the enum now so wallet auth already assigns
    a sensible default role rather than needing a later migration."""

    USER = "user"
    ADMIN = "admin"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=UserRole.USER,
        server_default=UserRole.USER.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    wallets: Mapped[list["Wallet"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Wallet(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A wallet address linked to a user.

    EVM addresses are chain-agnostic (the same address is valid across every
    EVM chain), so a wallet is stored once per address, not once per chain —
    which chain a given action happens on is context on the *transaction*,
    not the wallet.
    """

    __tablename__ = "wallets"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Stored in EIP-55 checksum form (as SIWE requires); unique so one wallet
    # can't be linked to two different user accounts.
    address: Mapped[str] = mapped_column(String(42), unique=True, index=True, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship(back_populates="wallets")


class SiweNonce(UUIDPrimaryKeyMixin, Base):
    """A one-time-use nonce issued for a SIWE sign-in attempt.

    Persisted (not in-memory) so replay protection holds across process
    restarts and multiple backend instances behind a load balancer — an
    in-memory set would let a signature be replayed against a different
    instance.
    """

    __tablename__ = "siwe_nonces"

    value: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
