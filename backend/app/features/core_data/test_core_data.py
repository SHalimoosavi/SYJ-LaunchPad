"""Core data model (Phase 3) tests.

Data-model tests, not API tests — there is no HTTP surface for these 9
entities in this phase (see module docstring in models.py for why). Every
test here talks to a real Postgres instance directly via SQLAlchemy, and
deliberately includes integrity-FAILURE cases (bad FKs, duplicate unique
values, self-referral), not just "insert worked" happy paths.
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.features.auth.models import User
from app.features.core_data.models import (
    Claim,
    ClaimStatus,
    Notification,
    Purchase,
    Sale,
    SaleStatus,
    Setting,
    Transaction,
    TransactionStatus,
    Whitelist,
)
from app.features.core_data.service import (
    SecretLeakageError,
    create_audit_log,
    create_claim,
    create_notification,
    create_purchase,
    create_referral_reward,
    create_sale,
    create_setting,
    create_transaction,
    create_whitelist_entry,
)
from app.features.projects.models import Project


async def _make_user(session: AsyncSession) -> User:
    user = User()
    session.add(user)
    await session.flush()
    return user


async def _make_project(session: AsyncSession, owner_id: uuid.UUID) -> Project:
    project = Project(
        owner_id=owner_id, name=f"Test Project {uuid.uuid4().hex[:8]}", slug=uuid.uuid4().hex
    )
    session.add(project)
    await session.flush()
    return project


async def _make_sale(session: AsyncSession, project_id: uuid.UUID) -> Sale:
    sale = Sale(project_id=project_id)
    session.add(sale)
    await session.flush()
    return sale


# ---------------------------------------------------------------------------
# Sale
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sale_creation_and_defaults() -> None:
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        project = await _make_project(session, user.id)
        sale = await create_sale(session, project_id=project.id, price=Decimal("1.5"))

        assert sale.status == SaleStatus.DRAFT
        assert sale.project_id == project.id
        assert sale.price == Decimal("1.5")


@pytest.mark.asyncio
async def test_sale_rejects_invalid_project_id() -> None:
    """FK integrity: a Sale cannot reference a nonexistent project."""
    async with AsyncSessionLocal() as session:
        with pytest.raises(IntegrityError):
            await create_sale(session, project_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_sale_end_before_start_is_rejected() -> None:
    """CheckConstraint: end_at must be after start_at when both are set."""
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        project = await _make_project(session, user.id)
        now = datetime.now(UTC)

        bad_sale = Sale(
            project_id=project.id,
            start_at=now,
            end_at=now - timedelta(days=1),
        )
        session.add(bad_sale)
        with pytest.raises(IntegrityError):
            await session.commit()


@pytest.mark.asyncio
async def test_deleting_project_cascades_to_sale() -> None:
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        project = await _make_project(session, user.id)
        sale = await _make_sale(session, project.id)
        sale_id = sale.id

        await session.delete(project)
        await session.commit()

    # A fresh session, not the one that had `sale` cached in its identity
    # map, so this genuinely re-queries Postgres instead of returning a
    # stale in-memory object (expire_on_commit=False on this session
    # factory means the original session wouldn't re-query on its own).
    async with AsyncSessionLocal() as verify_session:
        result = await verify_session.get(Sale, sale_id)
        assert result is None


# ---------------------------------------------------------------------------
# Transaction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transaction_creation_and_status_default() -> None:
    async with AsyncSessionLocal() as session:
        tx = await create_transaction(session, chain_id=1)
        assert tx.status == TransactionStatus.PENDING
        assert tx.tx_hash is None


@pytest.mark.asyncio
async def test_duplicate_tx_hash_on_same_chain_is_rejected() -> None:
    """Partial unique index: (chain_id, tx_hash) must be unique when
    tx_hash is not null."""
    async with AsyncSessionLocal() as session:
        hash_value = "0x" + uuid.uuid4().hex + uuid.uuid4().hex[:24]
        await create_transaction(session, chain_id=1, tx_hash=hash_value)

        with pytest.raises(IntegrityError):
            tx2 = Transaction(chain_id=1, tx_hash=hash_value)
            session.add(tx2)
            await session.commit()


@pytest.mark.asyncio
async def test_multiple_null_tx_hashes_are_allowed() -> None:
    """The partial index only applies when tx_hash IS NOT NULL — multiple
    PENDING transactions with no hash yet must NOT collide."""
    async with AsyncSessionLocal() as session:
        tx1 = await create_transaction(session, chain_id=1, tx_hash=None)
        tx2 = await create_transaction(session, chain_id=1, tx_hash=None)
        assert tx1.id != tx2.id


@pytest.mark.asyncio
async def test_same_hash_on_different_chains_is_allowed() -> None:
    """Uniqueness is scoped per chain_id, not global."""
    async with AsyncSessionLocal() as session:
        hash_value = "0x" + uuid.uuid4().hex + uuid.uuid4().hex[:24]
        tx1 = await create_transaction(session, chain_id=1, tx_hash=hash_value)
        tx2 = await create_transaction(session, chain_id=56, tx_hash=hash_value)
        assert tx1.id != tx2.id


# ---------------------------------------------------------------------------
# Purchase
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_purchase_creation_and_relationships() -> None:
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        project = await _make_project(session, user.id)
        sale = await _make_sale(session, project.id)

        purchase = await create_purchase(
            session, sale_id=sale.id, purchaser_user_id=user.id, amount=Decimal("100")
        )
        assert purchase.sale_id == sale.id
        assert purchase.purchaser_user_id == user.id
        assert purchase.amount == Decimal("100")


@pytest.mark.asyncio
async def test_purchase_survives_transaction_deletion() -> None:
    """transaction_id is SET NULL on transaction deletion — the purchase
    record itself must not be destroyed."""
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        project = await _make_project(session, user.id)
        sale = await _make_sale(session, project.id)
        tx = await create_transaction(session, chain_id=1)

        purchase = Purchase(sale_id=sale.id, purchaser_user_id=user.id, transaction_id=tx.id)
        session.add(purchase)
        await session.commit()
        purchase_id = purchase.id

        await session.delete(tx)
        await session.commit()

    async with AsyncSessionLocal() as verify_session:
        result = await verify_session.get(Purchase, purchase_id)
        assert result is not None
        assert result.transaction_id is None


@pytest.mark.asyncio
async def test_deleting_sale_cascades_to_purchase() -> None:
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        project = await _make_project(session, user.id)
        sale = await _make_sale(session, project.id)
        purchase = await create_purchase(session, sale_id=sale.id, purchaser_user_id=user.id)
        purchase_id = purchase.id

        await session.delete(sale)
        await session.commit()

    async with AsyncSessionLocal() as verify_session:
        assert await verify_session.get(Purchase, purchase_id) is None


# ---------------------------------------------------------------------------
# Claim
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_claim_creation_defaults() -> None:
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        project = await _make_project(session, user.id)
        sale = await _make_sale(session, project.id)

        claim = await create_claim(session, sale_id=sale.id, user_id=user.id)
        assert claim.status == ClaimStatus.NOT_STARTED
        assert claim.claimed_amount == Decimal("0")


@pytest.mark.asyncio
async def test_duplicate_claim_for_same_sale_and_user_is_rejected() -> None:
    """UniqueConstraint(sale_id, user_id): one claim record per user per sale."""
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        project = await _make_project(session, user.id)
        sale = await _make_sale(session, project.id)
        await create_claim(session, sale_id=sale.id, user_id=user.id)

        with pytest.raises(IntegrityError):
            dup = Claim(sale_id=sale.id, user_id=user.id)
            session.add(dup)
            await session.commit()


# ---------------------------------------------------------------------------
# Whitelist
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_whitelist_entry_creation() -> None:
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        project = await _make_project(session, user.id)
        sale = await _make_sale(session, project.id)

        entry = await create_whitelist_entry(session, sale_id=sale.id, user_id=user.id)
        assert entry.sale_id == sale.id
        assert entry.user_id == user.id


@pytest.mark.asyncio
async def test_duplicate_whitelist_entry_is_rejected() -> None:
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        project = await _make_project(session, user.id)
        sale = await _make_sale(session, project.id)
        await create_whitelist_entry(session, sale_id=sale.id, user_id=user.id)

        with pytest.raises(IntegrityError):
            dup = Whitelist(sale_id=sale.id, user_id=user.id)
            session.add(dup)
            await session.commit()


# ---------------------------------------------------------------------------
# ReferralReward
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_referral_reward_creation() -> None:
    async with AsyncSessionLocal() as session:
        referrer = await _make_user(session)
        referred = await _make_user(session)

        reward = await create_referral_reward(
            session, referrer_user_id=referrer.id, referred_user_id=referred.id
        )
        assert reward.referrer_user_id == referrer.id
        assert reward.referred_user_id == referred.id


@pytest.mark.asyncio
async def test_self_referral_is_rejected() -> None:
    """CheckConstraint: referrer_user_id != referred_user_id."""
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        with pytest.raises(IntegrityError):
            await create_referral_reward(
                session, referrer_user_id=user.id, referred_user_id=user.id
            )


# ---------------------------------------------------------------------------
# AuditLog
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_log_creation_and_persistence() -> None:
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        log = await create_audit_log(
            session,
            actor_user_id=user.id,
            action="project.created",
            entity_type="project",
            entity_id=uuid.uuid4(),
            context={"name": "Example"},
        )
        assert log.action == "project.created"
        assert log.context == {"name": "Example"}


@pytest.mark.asyncio
async def test_audit_log_survives_actor_deletion() -> None:
    """actor_user_id is SET NULL, not CASCADE -- the audit trail must
    outlive the actor being deleted."""
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        log = await create_audit_log(session, actor_user_id=user.id, action="user.test_action")
        log_id = log.id

        await session.delete(user)
        await session.commit()

    async with AsyncSessionLocal() as verify_session:
        result = await verify_session.get(type(log), log_id)
        assert result is not None
        assert result.actor_user_id is None


@pytest.mark.parametrize(
    "bad_key",
    ["password", "PRIVATE_KEY", "seed_phrase", "api_key", "user_jwt_token", "credentials"],
)
@pytest.mark.asyncio
async def test_audit_log_rejects_secret_like_keys(bad_key: str) -> None:
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        with pytest.raises(SecretLeakageError):
            await create_audit_log(
                session,
                actor_user_id=user.id,
                action="suspicious.write",
                context={bad_key: "should-not-be-stored"},
            )


@pytest.mark.asyncio
async def test_audit_log_allows_benign_keys() -> None:
    """The secret-leakage guard must not be so broad it rejects normal
    audit context."""
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        log = await create_audit_log(
            session,
            actor_user_id=user.id,
            action="project.renamed",
            context={"old_name": "Foo", "new_name": "Bar"},
        )
        assert log.context == {"old_name": "Foo", "new_name": "Bar"}


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_notification_creation_defaults() -> None:
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        notification = await create_notification(
            session, user_id=user.id, notification_type="project.registered", message="Hello"
        )
        assert notification.is_read is False


@pytest.mark.asyncio
async def test_deleting_user_cascades_to_notification() -> None:
    async with AsyncSessionLocal() as session:
        user = await _make_user(session)
        notification = await create_notification(
            session, user_id=user.id, notification_type="test", message="test"
        )
        notification_id = notification.id

        await session.delete(user)
        await session.commit()

    async with AsyncSessionLocal() as verify_session:
        assert await verify_session.get(Notification, notification_id) is None


# ---------------------------------------------------------------------------
# Setting
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_global_setting_creation() -> None:
    async with AsyncSessionLocal() as session:
        setting = await create_setting(
            session, user_id=None, key=f"feature.flag.{uuid.uuid4().hex[:8]}", value="true"
        )
        assert setting.user_id is None


@pytest.mark.asyncio
async def test_duplicate_global_setting_key_is_rejected() -> None:
    """The partial unique index on key WHERE user_id IS NULL — this is
    the specific case a plain UNIQUE(user_id, key) constraint would NOT
    catch, since Postgres treats every NULL as distinct."""
    async with AsyncSessionLocal() as session:
        key = f"feature.flag.{uuid.uuid4().hex[:8]}"
        await create_setting(session, user_id=None, key=key, value="on")

        with pytest.raises(IntegrityError):
            dup = Setting(user_id=None, key=key, value="off")
            session.add(dup)
            await session.commit()


@pytest.mark.asyncio
async def test_same_key_allowed_for_different_users() -> None:
    async with AsyncSessionLocal() as session:
        user_a = await _make_user(session)
        user_b = await _make_user(session)
        key = f"theme.{uuid.uuid4().hex[:8]}"

        setting_a = await create_setting(session, user_id=user_a.id, key=key, value="dark")
        setting_b = await create_setting(session, user_id=user_b.id, key=key, value="light")
        assert setting_a.id != setting_b.id


@pytest.mark.parametrize("bad_key", ["password", "SECRET", "private_key"])
@pytest.mark.asyncio
async def test_setting_rejects_secret_like_keys(bad_key: str) -> None:
    async with AsyncSessionLocal() as session:
        with pytest.raises(SecretLeakageError):
            await create_setting(session, user_id=None, key=bad_key, value="should-not-persist")
