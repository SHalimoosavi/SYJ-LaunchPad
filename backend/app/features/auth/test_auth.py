"""End-to-end auth tests.

These don't mock the crypto: we generate a real EOA with eth-account, build
a real EIP-4361 message, sign it for real, and drive it through the actual
HTTP routes. If this passes, wallet sign-in genuinely works — not just
"the mocks were satisfied."
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
import siwe
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_account.signers.local import LocalAccount
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.common.errors import ForbiddenError
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.features.auth.dependencies import require_role
from app.features.auth.models import SiweNonce, User, UserRole
from app.main import app

settings = get_settings()


def _build_siwe_message(*, address: str, nonce: str, chain_id: int = 1) -> str:
    message = siwe.SiweMessage(
        domain=settings.siwe_domain,
        address=address,
        uri=settings.siwe_uri,
        version="1",
        chain_id=chain_id,
        nonce=nonce,
        issued_at=siwe.ISO8601Datetime.from_datetime(datetime.now(UTC)),
        statement="Sign in to SYJ LaunchPad.",
    )
    return cast(str, message.prepare_message())


def _sign(message: str, private_key: str) -> str:
    signable = encode_defunct(text=message)
    signed = Account.sign_message(signable, private_key=private_key)
    return "0x" + cast(bytes, signed.signature).hex()


@pytest.fixture
def wallet() -> LocalAccount:
    return cast(LocalAccount, Account.create())


async def _get_nonce(client: AsyncClient) -> str:
    response = await client.get("/api/v1/auth/nonce")
    assert response.status_code == 200
    return str(response.json()["nonce"])


@pytest.mark.asyncio
async def test_full_siwe_login_flow_and_me(wallet: LocalAccount) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        nonce = await _get_nonce(client)
        message = _build_siwe_message(address=wallet.address, nonce=nonce)
        signature = _sign(message, wallet.key.hex())

        verify_response = await client.post(
            "/api/v1/auth/verify", json={"message": message, "signature": signature}
        )
        assert verify_response.status_code == 200, verify_response.text
        body = verify_response.json()
        assert body["user"]["wallet_address"] == wallet.address
        assert body["user"]["role"] == "user"
        assert body["token_type"] == "bearer"
        token = body["access_token"]

        me_response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["wallet_address"] == wallet.address


@pytest.mark.asyncio
async def test_me_without_token_is_unauthorized() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_nonce_cannot_be_replayed(wallet: LocalAccount) -> None:
    """The same signed message must not be accepted twice — this is the
    replay-protection guarantee the nonce store exists to provide."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        nonce = await _get_nonce(client)
        message = _build_siwe_message(address=wallet.address, nonce=nonce)
        signature = _sign(message, wallet.key.hex())

        first = await client.post(
            "/api/v1/auth/verify", json={"message": message, "signature": signature}
        )
        assert first.status_code == 200

        second = await client.post(
            "/api/v1/auth/verify", json={"message": message, "signature": signature}
        )
        assert second.status_code == 401
        assert second.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_unknown_nonce_is_rejected(wallet: LocalAccount) -> None:
    """A message signed with a nonce we never issued must be rejected —
    otherwise the nonce check is decorative."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        forged_nonce = siwe.generate_nonce()
        message = _build_siwe_message(address=wallet.address, nonce=forged_nonce)
        signature = _sign(message, wallet.key.hex())

        response = await client.post(
            "/api/v1/auth/verify", json={"message": message, "signature": signature}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_tampered_signature_is_rejected(wallet: LocalAccount) -> None:
    """A message signed by one wallet but claiming another wallet's address
    must fail signature recovery — this is the core anti-spoofing check."""
    transport = ASGITransport(app=app)
    other_wallet: LocalAccount = cast(LocalAccount, Account.create())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        nonce = await _get_nonce(client)
        # Message claims `wallet`'s address...
        message = _build_siwe_message(address=wallet.address, nonce=nonce)
        # ...but is signed by a completely different key.
        signature = _sign(message, other_wallet.key.hex())

        response = await client.post(
            "/api/v1/auth/verify", json={"message": message, "signature": signature}
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_expired_nonce_is_rejected(wallet: LocalAccount) -> None:
    """A nonce older than SIWE_NONCE_TTL_SECONDS must be rejected even if
    the signature itself is perfectly valid."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        nonce = await _get_nonce(client)

        # Force the nonce we just issued into the past so it reads as expired.
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(SiweNonce).where(SiweNonce.value == nonce))
            row = result.scalar_one()
            row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
            await session.commit()

        message = _build_siwe_message(address=wallet.address, nonce=nonce)
        signature = _sign(message, wallet.key.hex())

        response = await client.post(
            "/api/v1/auth/verify", json={"message": message, "signature": signature}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_concurrent_verify_requests_only_one_succeeds(wallet: LocalAccount) -> None:
    """Two concurrent requests racing to consume the SAME nonce must result
    in exactly one success and one rejection — this is what proves the
    UPDATE...WHERE consumption is atomic under real concurrency against a
    real Postgres instance, not just correct in single-threaded review."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        nonce = await _get_nonce(client)
        message = _build_siwe_message(address=wallet.address, nonce=nonce)
        signature = _sign(message, wallet.key.hex())

        async def attempt() -> int:
            response = await client.post(
                "/api/v1/auth/verify", json={"message": message, "signature": signature}
            )
            return response.status_code

        results = await asyncio.gather(attempt(), attempt(), attempt(), attempt(), attempt())

        assert results.count(200) == 1, f"expected exactly one success, got {results}"
        assert results.count(401) == len(results) - 1


@pytest.mark.asyncio
async def test_invalid_signature_does_not_burn_a_valid_nonce(wallet: LocalAccount) -> None:
    """An attacker submitting a bad signature against a real nonce must not
    be able to invalidate that nonce for the legitimate wallet owner."""
    transport = ASGITransport(app=app)
    other_wallet: LocalAccount = cast(LocalAccount, Account.create())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        nonce = await _get_nonce(client)
        message = _build_siwe_message(address=wallet.address, nonce=nonce)

        # First: an invalid signature (wrong key) against this nonce.
        bad_signature = _sign(message, other_wallet.key.hex())
        bad_response = await client.post(
            "/api/v1/auth/verify", json={"message": message, "signature": bad_signature}
        )
        assert bad_response.status_code == 401

        # Then: the legitimate signature against the SAME nonce must still work.
        good_signature = _sign(message, wallet.key.hex())
        good_response = await client.post(
            "/api/v1/auth/verify", json={"message": message, "signature": good_signature}
        )
        assert good_response.status_code == 200, good_response.text


@pytest.mark.asyncio
async def test_unsupported_chain_is_rejected(wallet: LocalAccount) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        nonce = await _get_nonce(client)
        # chain_id 999999 is not in ENABLED_CHAIN_IDS.
        message = _build_siwe_message(address=wallet.address, nonce=nonce, chain_id=999999)
        signature = _sign(message, wallet.key.hex())

        response = await client.post(
            "/api/v1/auth/verify", json={"message": message, "signature": signature}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_is_rejected(wallet: LocalAccount) -> None:
    """A deactivated account's still-valid JWT must not grant access —
    `get_current_user` checks `user.is_active` on every request, not just
    at sign-in time."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        nonce = await _get_nonce(client)
        message = _build_siwe_message(address=wallet.address, nonce=nonce)
        signature = _sign(message, wallet.key.hex())

        verify_response = await client.post(
            "/api/v1/auth/verify", json={"message": message, "signature": signature}
        )
        assert verify_response.status_code == 200
        token = verify_response.json()["access_token"]
        user_id = verify_response.json()["user"]["id"]

        # Confirm the token works while the account is active.
        me_response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200

        # Deactivate the account directly (simulating an admin action from
        # a future phase) and confirm the SAME still-unexpired token is
        # now rejected.
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.id == uuid.UUID(user_id)))
            user = result.scalar_one()
            user.is_active = False
            await session.commit()

        me_after_deactivation = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_after_deactivation.status_code == 401
        assert me_after_deactivation.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_require_role_dependency_allows_and_denies_correctly() -> None:
    """Unit-level check of the RBAC dependency itself: no route currently
    uses `require_role` (that lands with the Admin Dashboard in Phase 8),
    so this exercises the dependency function directly against real User
    instances rather than leaving it unverified until a future phase."""
    admin_user = User(role=UserRole.ADMIN, is_active=True)
    regular_user = User(role=UserRole.USER, is_active=True)

    admin_only = require_role(UserRole.ADMIN)

    # Admin passes through and the same user object is returned.
    result = await admin_only(user=admin_user)
    assert result is admin_user

    # Non-admin is rejected with ForbiddenError (mapped to HTTP 403).
    with pytest.raises(ForbiddenError):
        await admin_only(user=regular_user)
