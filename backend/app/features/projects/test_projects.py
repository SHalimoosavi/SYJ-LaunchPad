"""Project Registration (Phase 3) integration tests.

Reuses the exact real-signature SIWE login flow from
app/features/auth/test_auth.py to obtain genuine authenticated sessions —
project ownership is meaningless to test against a fake/mocked user, so
every test here goes through the real `/auth/verify` route first.
"""

import uuid
from datetime import UTC, datetime
from typing import cast

import pytest
import siwe
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_account.signers.local import LocalAccount
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.features.auth.models import User
from app.features.projects.models import Project
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


async def _login(client: AsyncClient) -> tuple[str, str]:
    """Real SIWE login. Returns (bearer_token, wallet_address)."""
    wallet: LocalAccount = cast(LocalAccount, Account.create())
    nonce_response = await client.get("/api/v1/auth/nonce")
    nonce = nonce_response.json()["nonce"]
    message = _build_siwe_message(address=wallet.address, nonce=nonce)
    signature = _sign(message, wallet.key.hex())
    verify_response = await client.post(
        "/api/v1/auth/verify", json={"message": message, "signature": signature}
    )
    assert verify_response.status_code == 200, verify_response.text
    return verify_response.json()["access_token"], wallet.address


def _unique_name(base: str) -> str:
    """Append a short random suffix so repeated test runs against a
    persistent (non-truncated-between-runs) database never collide on the
    slug-uniqueness constraint — the same principle the auth tests already
    use by generating a fresh random wallet on every run instead of a
    fixed address."""
    return f"{base} {uuid.uuid4().hex[:8]}"


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_unauthenticated_create_is_rejected() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/projects", json={"name": "No Auth Project"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_authenticated_create_assigns_owner_from_jwt() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, _wallet = await _login(client)

        project_name = _unique_name("Genuine Project")
        response = await client.post(
            "/api/v1/projects",
            json={"name": project_name, "description": "A real project."},
            headers=_auth_headers(token),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["name"] == project_name
        assert body["is_active"] is True

        # owner_id in the response must match the authenticated user, not
        # anything the client could have supplied (the request body above
        # contained no owner/user field at all).
        me_response = await client.get("/api/v1/auth/me", headers=_auth_headers(token))
        assert body["owner_id"] == me_response.json()["id"]


@pytest.mark.asyncio
async def test_client_supplied_owner_field_is_ignored() -> None:
    """Even if a client stuffs extra fields into the body trying to spoof
    ownership, the schema doesn't accept them and the owner is still
    server-derived from the JWT."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, _wallet = await _login(client)
        forged_owner_id = str(uuid.uuid4())

        response = await client.post(
            "/api/v1/projects",
            json={
                "name": _unique_name("Spoof Attempt"),
                "owner_id": forged_owner_id,
                "user_id": forged_owner_id,
            },
            headers=_auth_headers(token),
        )
        assert response.status_code == 201, response.text
        assert response.json()["owner_id"] != forged_owner_id


@pytest.mark.asyncio
async def test_owner_can_retrieve_and_update_own_project() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, _wallet = await _login(client)

        project_name = _unique_name("Owned Project")
        create_response = await client.post(
            "/api/v1/projects", json={"name": project_name}, headers=_auth_headers(token)
        )
        project_id = create_response.json()["id"]
        original_slug = create_response.json()["slug"]

        get_response = await client.get(
            f"/api/v1/projects/{project_id}", headers=_auth_headers(token)
        )
        assert get_response.status_code == 200
        assert get_response.json()["id"] == project_id

        update_response = await client.patch(
            f"/api/v1/projects/{project_id}",
            json={"description": "Updated description."},
            headers=_auth_headers(token),
        )
        assert update_response.status_code == 200
        assert update_response.json()["description"] == "Updated description."
        # slug must NOT change on update (immutability guarantee).
        assert update_response.json()["slug"] == original_slug


@pytest.mark.asyncio
async def test_list_my_projects_returns_only_own_projects() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token_a, _ = await _login(client)
        token_b, _ = await _login(client)

        name_one = _unique_name("Alice Project One")
        name_two = _unique_name("Alice Project Two")
        name_bob = _unique_name("Bob Project")
        await client.post(
            "/api/v1/projects", json={"name": name_one}, headers=_auth_headers(token_a)
        )
        await client.post(
            "/api/v1/projects", json={"name": name_two}, headers=_auth_headers(token_a)
        )
        await client.post(
            "/api/v1/projects", json={"name": name_bob}, headers=_auth_headers(token_b)
        )

        list_response = await client.get("/api/v1/projects/me", headers=_auth_headers(token_a))
        assert list_response.status_code == 200
        names = {p["name"] for p in list_response.json()}
        assert names == {name_one, name_two}


@pytest.mark.asyncio
async def test_cross_user_read_is_rejected_as_not_found() -> None:
    """User B must not be able to read User A's project — and gets 404,
    not 403, so cross-user probing can't distinguish 'doesn't exist' from
    'exists but isn't yours'."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token_a, _ = await _login(client)
        token_b, _ = await _login(client)

        create_response = await client.post(
            "/api/v1/projects",
            json={"name": _unique_name("Alice Private Project")},
            headers=_auth_headers(token_a),
        )
        project_id = create_response.json()["id"]

        cross_read = await client.get(
            f"/api/v1/projects/{project_id}", headers=_auth_headers(token_b)
        )
        assert cross_read.status_code == 404
        assert cross_read.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_cross_user_update_is_rejected() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token_a, _ = await _login(client)
        token_b, _ = await _login(client)

        create_response = await client.post(
            "/api/v1/projects",
            json={"name": _unique_name("Alice Update Target")},
            headers=_auth_headers(token_a),
        )
        project_id = create_response.json()["id"]

        cross_update = await client.patch(
            f"/api/v1/projects/{project_id}",
            json={"name": "Hijacked Name"},
            headers=_auth_headers(token_b),
        )
        assert cross_update.status_code == 404

        # Prove the project was genuinely untouched, not just that the
        # response was 404 — the owner still sees the original name.
        owner_view = await client.get(
            f"/api/v1/projects/{project_id}", headers=_auth_headers(token_a)
        )
        assert owner_view.json()["name"] != "Hijacked Name"


@pytest.mark.asyncio
async def test_nonexistent_project_is_not_found() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, _ = await _login(client)
        response = await client.get(
            f"/api/v1/projects/{uuid.uuid4()}", headers=_auth_headers(token)
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_payload_is_rejected() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, _ = await _login(client)

        # Empty name violates min_length=1.
        response = await client.post(
            "/api/v1/projects", json={"name": ""}, headers=_auth_headers(token)
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

        # Missing required field entirely.
        response2 = await client.post(
            "/api/v1/projects", json={"description": "no name field"}, headers=_auth_headers(token)
        )
        assert response2.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_slug_is_rejected_with_conflict() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, _ = await _login(client)

        dup_name = _unique_name("Unique Name Here")
        first = await client.post(
            "/api/v1/projects", json={"name": dup_name}, headers=_auth_headers(token)
        )
        assert first.status_code == 201

        # Same name from the SAME user must still be rejected — uniqueness
        # is global, not per-owner.
        second = await client.post(
            "/api/v1/projects", json={"name": dup_name}, headers=_auth_headers(token)
        )
        assert second.status_code == 409
        assert second.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_inactive_user_cannot_create_project() -> None:
    """Phase 2's inactive-user rejection must still hold for Phase 3
    routes — they all depend on the same get_current_user."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token, wallet_address = await _login(client)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.wallets.any(address=wallet_address))
            )
            user = result.scalar_one()
            user.is_active = False
            await session.commit()

        blocked_name = _unique_name("Should Not Be Created")
        response = await client.post(
            "/api/v1/projects", json={"name": blocked_name}, headers=_auth_headers(token)
        )
        assert response.status_code == 401

        # Confirm no project was actually created despite the attempt.
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Project).where(Project.name == blocked_name))
            assert result.scalar_one_or_none() is None
