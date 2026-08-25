"""Core data model entities (Phase 3): Sale, Purchase, Transaction, Claim,
Whitelist, ReferralReward, AuditLog, Notification, Setting.

DATA MODEL ONLY. Nothing in this module executes a sale, processes a
purchase, settles a claim, or pays a referral reward — these are
normalized tables representing domain state, most of which (sale
configuration, purchase/claim/referral records) will eventually be
*indexed from* blockchain activity, not the other way around. The database
is never the authoritative source for on-chain facts (balances, transfer
finality, ownership) — see `Transaction`, whose status fields are defined
precisely to avoid implying finality the app hasn't observed on-chain.

No business logic (execution, settlement, attribution, payout) lives here
or anywhere in this feature — that is explicitly out of scope for Phase 3
and belongs to Phase 5 (Presale), Phase 6 (Claim & Vesting), and Phase 7
(Referral System).
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Token/quote amounts are stored as arbitrary-precision decimals, never
# float, and never assumed to be the authoritative balance — they are
# configured/recorded values pending independent on-chain verification in
# later phases. 38 digits / 18 decimal places comfortably covers typical
# ERC20 `decimals` values without pretending sub-wei precision matters at
# this (pre-blockchain-integration) phase.
_AMOUNT = Numeric(38, 18)


# ---------------------------------------------------------------------------
# Sale
# ---------------------------------------------------------------------------


class SaleStatus(enum.StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"


class Sale(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Describes a configured sale. Contains no execution/settlement
    logic — see module docstring."""

    __tablename__ = "sales"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[SaleStatus] = mapped_column(
        Enum(
            SaleStatus,
            name="sale_status",
            native_enum=True,
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
        default=SaleStatus.DRAFT,
        server_default=SaleStatus.DRAFT.value,
        index=True,
    )
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hard_cap: Mapped[Decimal | None] = mapped_column(_AMOUNT, nullable=True)
    soft_cap: Mapped[Decimal | None] = mapped_column(_AMOUNT, nullable=True)
    price: Mapped[Decimal | None] = mapped_column(_AMOUNT, nullable=True)
    min_contribution: Mapped[Decimal | None] = mapped_column(_AMOUNT, nullable=True)
    max_contribution: Mapped[Decimal | None] = mapped_column(_AMOUNT, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "end_at IS NULL OR start_at IS NULL OR end_at > start_at",
            name="ck_sales_end_after_start",
        ),
    )


# ---------------------------------------------------------------------------
# Transaction (generic blockchain reference — see module docstring)
# ---------------------------------------------------------------------------


class TransactionStatus(enum.StrEnum):
    """Precise, non-overlapping meanings — never implies finality the app
    hasn't actually observed on-chain:
    - PENDING: recorded locally, not yet broadcast.
    - SUBMITTED: broadcast to the network, awaiting confirmation.
    - CONFIRMED: observed included in a block (later phases wire up the
      actual RPC verification this depends on).
    - FAILED: broadcast but did not succeed (reverted / dropped / replaced).
    """

    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Transaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transactions"

    chain_id: Mapped[int] = mapped_column(nullable=False, index=True)
    tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(
            TransactionStatus,
            name="transaction_status",
            native_enum=True,
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
        default=TransactionStatus.PENDING,
        server_default=TransactionStatus.PENDING.value,
        index=True,
    )
    related_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    __table_args__ = (
        # A given hash is unique per chain — but only once it's known
        # (tx_hash is nullable for PENDING rows created before broadcast),
        # so this is a partial unique index, not a plain unique constraint.
        Index(
            "uq_transactions_chain_id_tx_hash",
            "chain_id",
            "tx_hash",
            unique=True,
            postgresql_where=text("tx_hash IS NOT NULL"),
        ),
    )


# ---------------------------------------------------------------------------
# Purchase
# ---------------------------------------------------------------------------


class PurchaseStatus(enum.StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Purchase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "purchases"

    sale_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    purchaser_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True
    )
    amount: Mapped[Decimal | None] = mapped_column(_AMOUNT, nullable=True)
    status: Mapped[PurchaseStatus] = mapped_column(
        Enum(
            PurchaseStatus,
            name="purchase_status",
            native_enum=True,
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
        default=PurchaseStatus.PENDING,
        server_default=PurchaseStatus.PENDING.value,
        index=True,
    )


# ---------------------------------------------------------------------------
# Claim
# ---------------------------------------------------------------------------


class ClaimStatus(enum.StrEnum):
    NOT_STARTED = "not_started"
    PARTIALLY_CLAIMED = "partially_claimed"
    FULLY_CLAIMED = "fully_claimed"


class Claim(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One allocation/claim-accounting record per (sale, user). Descriptive
    only — see module docstring; claim execution is Phase 6."""

    __tablename__ = "claims"

    sale_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True
    )
    allocated_amount: Mapped[Decimal | None] = mapped_column(_AMOUNT, nullable=True)
    claimed_amount: Mapped[Decimal] = mapped_column(
        _AMOUNT, nullable=False, default=0, server_default="0"
    )
    status: Mapped[ClaimStatus] = mapped_column(
        Enum(
            ClaimStatus,
            name="claim_status",
            native_enum=True,
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
        default=ClaimStatus.NOT_STARTED,
        server_default=ClaimStatus.NOT_STARTED.value,
    )

    __table_args__ = (UniqueConstraint("sale_id", "user_id", name="uq_claims_sale_id_user_id"),)


# ---------------------------------------------------------------------------
# Whitelist
# ---------------------------------------------------------------------------


class Whitelist(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Eligibility record only — no enforcement logic (that belongs to the
    Phase 5 presale engine when it reads this table)."""

    __tablename__ = "whitelist_entries"

    sale_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    allocation_cap: Mapped[Decimal | None] = mapped_column(_AMOUNT, nullable=True)

    __table_args__ = (
        UniqueConstraint("sale_id", "user_id", name="uq_whitelist_entries_sale_id_user_id"),
    )


# ---------------------------------------------------------------------------
# ReferralReward
# ---------------------------------------------------------------------------


class ReferralRewardStatus(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"


class ReferralReward(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Reward record only — no attribution engine or payout execution
    (Phase 7)."""

    __tablename__ = "referral_rewards"

    referrer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    referred_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sale_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales.id", ondelete="SET NULL"), nullable=True
    )
    reward_amount: Mapped[Decimal | None] = mapped_column(_AMOUNT, nullable=True)
    status: Mapped[ReferralRewardStatus] = mapped_column(
        Enum(
            ReferralRewardStatus,
            name="referral_reward_status",
            native_enum=True,
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
        default=ReferralRewardStatus.PENDING,
        server_default=ReferralRewardStatus.PENDING.value,
    )

    __table_args__ = (
        CheckConstraint(
            "referrer_user_id != referred_user_id", name="ck_referral_rewards_no_self_referral"
        ),
    )


# ---------------------------------------------------------------------------
# AuditLog
# ---------------------------------------------------------------------------


class AuditLog(UUIDPrimaryKeyMixin, Base):
    """Append-only. No `updated_at` — nothing should ever update or delete
    an audit log row; that is itself a security property, not an
    oversight. `actor_user_id` is SET NULL (not CASCADE) on user deletion
    so the audit trail survives the actor being removed.

    `entity_id` is a plain UUID, not a foreign key: it can reference rows
    in different tables (project, sale, purchase, ...) depending on
    `entity_type`, and a real polymorphic FK would need a separate
    indirection table per entity type — over-engineering for what Phase 3
    needs. This is a deliberate, documented trade-off, not an oversight.
    """

    __tablename__ = "audit_logs"

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    context: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Data foundation only — no delivery infrastructure (email/push/etc).
    `is_read` is the one field expected to mutate after creation, which is
    why (unlike AuditLog) this uses the normal TimestampMixin with
    `updated_at`."""

    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text(), nullable=False)
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )


# ---------------------------------------------------------------------------
# Setting
# ---------------------------------------------------------------------------


class Setting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Generic key/value application settings — NOT environment
    configuration (that stays in app.core.config.Settings) and NEVER
    secrets (enforced in service.py, not just documented here).

    `user_id IS NULL` means a global setting; non-null means per-user.
    A plain UNIQUE(user_id, key) constraint does NOT enforce global-key
    uniqueness on its own, because Postgres treats every NULL as distinct
    from every other NULL — so two global rows with the same `key` would
    both satisfy UNIQUE(user_id, key). The partial index below closes that
    gap for the user_id IS NULL case specifically.
    """

    __tablename__ = "settings"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str | None] = mapped_column(Text(), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_settings_user_id_key"),
        Index(
            "uq_settings_global_key",
            "key",
            unique=True,
            postgresql_where=text("user_id IS NULL"),
        ),
    )
