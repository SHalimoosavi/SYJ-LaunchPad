"""Core data model service layer.

Deliberately thin: these are persistence helpers that prove the domain
model works (create, relate, enforce constraints), not business logic.
Nothing here executes a sale, processes a purchase, or pays a reward —
see the module docstring in models.py.

The one piece of real logic is `_reject_if_contains_secret_like_key`,
because "don't log secrets" isn't something a database schema can enforce
by itself — it has to be checked in code, on every write path that
accepts free-form key/value data (AuditLog.context, Setting.value).
"""

import re
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ConflictError
from app.features.core_data.models import (
    AuditLog,
    Claim,
    Notification,
    Purchase,
    ReferralReward,
    Sale,
    Setting,
    Transaction,
    Whitelist,
)

# Substrings that, if found in a key (case-insensitive), indicate the
# value is likely a secret and must never be written to an audit log or
# a generic settings row. This is a defensive net, not a substitute for
# callers simply not passing secrets in the first place — see Rule in the
# module docstring: never log private keys, seed phrases, passwords, JWT
# secrets, or raw credentials.
_SECRET_KEY_MARKERS = (
    "password",
    "secret",
    "private_key",
    "privatekey",
    "seed_phrase",
    "seedphrase",
    "mnemonic",
    "jwt",
    "api_key",
    "apikey",
    "credential",
)
_SECRET_KEY_RE = re.compile("|".join(re.escape(m) for m in _SECRET_KEY_MARKERS), re.IGNORECASE)


class SecretLeakageError(ConflictError):
    """Raised when a caller tries to persist something that looks like a
    secret into audit-log context or a generic setting. Subclasses
    ConflictError (400-family) rather than a 5xx — this is a rejected
    write, not a server fault."""

    code = "SECRET_LEAKAGE_REJECTED"


def _reject_if_contains_secret_like_key(data: dict[str, object]) -> None:
    for key in data:
        if _SECRET_KEY_RE.search(key):
            raise SecretLeakageError(
                f"Refusing to store a value under key '{key}': looks like a secret. "
                "Secrets must never be written to audit logs or settings."
            )


async def create_audit_log(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID | None,
    action: str,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    context: dict[str, object] | None = None,
) -> AuditLog:
    if context:
        _reject_if_contains_secret_like_key(context)

    log = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        context=context,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def create_setting(
    db: AsyncSession, *, user_id: uuid.UUID | None, key: str, value: str | None
) -> Setting:
    _reject_if_contains_secret_like_key({key: value})

    setting = Setting(user_id=user_id, key=key, value=value)
    db.add(setting)
    await db.commit()
    await db.refresh(setting)
    return setting


async def create_sale(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    price: Decimal | None = None,
    hard_cap: Decimal | None = None,
    soft_cap: Decimal | None = None,
) -> Sale:
    sale = Sale(project_id=project_id, price=price, hard_cap=hard_cap, soft_cap=soft_cap)
    db.add(sale)
    await db.commit()
    await db.refresh(sale)
    return sale


async def create_purchase(
    db: AsyncSession,
    *,
    sale_id: uuid.UUID,
    purchaser_user_id: uuid.UUID,
    amount: Decimal | None = None,
) -> Purchase:
    purchase = Purchase(sale_id=sale_id, purchaser_user_id=purchaser_user_id, amount=amount)
    db.add(purchase)
    await db.commit()
    await db.refresh(purchase)
    return purchase


async def create_claim(
    db: AsyncSession,
    *,
    sale_id: uuid.UUID,
    user_id: uuid.UUID,
    allocated_amount: Decimal | None = None,
) -> Claim:
    claim = Claim(sale_id=sale_id, user_id=user_id, allocated_amount=allocated_amount)
    db.add(claim)
    await db.commit()
    await db.refresh(claim)
    return claim


async def create_whitelist_entry(
    db: AsyncSession, *, sale_id: uuid.UUID, user_id: uuid.UUID
) -> Whitelist:
    entry = Whitelist(sale_id=sale_id, user_id=user_id)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def create_referral_reward(
    db: AsyncSession, *, referrer_user_id: uuid.UUID, referred_user_id: uuid.UUID
) -> ReferralReward:
    reward = ReferralReward(referrer_user_id=referrer_user_id, referred_user_id=referred_user_id)
    db.add(reward)
    await db.commit()
    await db.refresh(reward)
    return reward


async def create_notification(
    db: AsyncSession, *, user_id: uuid.UUID, notification_type: str, message: str
) -> Notification:
    notification = Notification(user_id=user_id, type=notification_type, message=message)
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def create_transaction(
    db: AsyncSession, *, chain_id: int, tx_hash: str | None = None
) -> Transaction:
    transaction = Transaction(chain_id=chain_id, tx_hash=tx_hash)
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction
