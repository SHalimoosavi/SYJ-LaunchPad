"""Auth business logic: nonce issuance, SIWE verification, user resolution.

Kept as a service layer (not inline in routes) so it's independently
testable and so future features (e.g. an admin "link additional wallet"
flow) can reuse `verify_siwe_and_get_user` without duplicating the
signature-checking logic.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import siwe
from sqlalchemy import func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.errors import UnauthorizedError
from app.core.config import Settings
from app.features.auth.models import SiweNonce, User, Wallet


async def issue_nonce(db: AsyncSession, settings: Settings) -> str:
    """Create and persist a single-use nonce for a SIWE sign-in attempt."""
    value = cast(str, siwe.generate_nonce())
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.siwe_nonce_ttl_seconds)
    db.add(SiweNonce(value=value, expires_at=expires_at, used=False))
    await db.commit()
    return value


async def _consume_nonce(db: AsyncSession, nonce_value: str) -> None:
    """Atomically validate and burn a nonce in a single UPDATE.

    This is a compare-and-swap against the database, not a
    SELECT-then-UPDATE: the WHERE clause (`used = false AND expires_at >
    now()`) is evaluated by Postgres under the row lock the UPDATE itself
    takes, so if two requests race to consume the same nonce, the second
    one's UPDATE simply matches zero rows once the first has committed —
    it can never observe and act on the pre-update state. No SELECT ever
    happens on the hot path, so there's nothing to race.

    `expires_at > now()` is compared using the database's own clock
    (`func.now()`) rather than app-server time, so app/DB clock skew can't
    open a window where an already-expired nonce still validates.

    Raises `UnauthorizedError` (without distinguishing unknown / already
    used / expired — those are one failure mode to the caller) if zero
    rows were affected.
    """
    stmt = (
        update(SiweNonce)
        .where(
            SiweNonce.value == nonce_value,
            SiweNonce.used.is_(False),
            SiweNonce.expires_at > func.now(),
        )
        .values(used=True)
        .execution_options(synchronize_session=False)
    )
    result = cast(CursorResult[Any], await db.execute(stmt))

    if result.rowcount != 1:
        await db.rollback()
        raise UnauthorizedError("Sign-in nonce is invalid, used, or expired")

    await db.commit()


async def _get_or_create_user_for_wallet(db: AsyncSession, address: str) -> User:
    result = await db.execute(select(Wallet).where(Wallet.address == address))
    wallet = result.scalar_one_or_none()

    if wallet is not None:
        await db.refresh(wallet, attribute_names=["user"])
        return wallet.user

    user = User()
    db.add(user)
    await db.flush()  # assign user.id before creating the wallet row

    wallet = Wallet(user_id=user.id, address=address, is_primary=True)
    db.add(wallet)
    await db.commit()
    await db.refresh(user, attribute_names=["wallets"])
    return user


async def verify_siwe_and_get_user(
    db: AsyncSession, settings: Settings, *, raw_message: str, signature: str
) -> tuple[User, str]:
    """Validate a signed SIWE message end-to-end and return (user, wallet_address).

    Order of checks matters: we parse and verify the cryptographic signature
    and message constraints (domain/expiry/nonce format) via the `siwe`
    library *before* touching the nonce store, so a malformed or forged
    message never burns a legitimate nonce.
    """
    try:
        message = siwe.SiweMessage.from_message(raw_message)
    except Exception as exc:
        raise UnauthorizedError("Malformed sign-in message") from exc

    try:
        message.verify(signature, domain=settings.siwe_domain)
    except siwe.ExpiredMessage as exc:
        raise UnauthorizedError("Sign-in message has expired") from exc
    except siwe.DomainMismatch as exc:
        raise UnauthorizedError("Sign-in message domain does not match this site") from exc
    except siwe.VerificationError as exc:
        raise UnauthorizedError("Invalid sign-in signature") from exc

    if message.chain_id not in settings.chain_ids:
        raise UnauthorizedError("Sign-in message targets an unsupported chain")

    # Nonce is only burned once the signature itself is proven valid.
    await _consume_nonce(db, message.nonce)

    user = await _get_or_create_user_for_wallet(db, message.address)
    return user, message.address


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.wallets))
    )
    return result.scalar_one_or_none()
