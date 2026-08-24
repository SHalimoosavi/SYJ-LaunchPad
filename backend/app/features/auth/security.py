"""JWT access token creation and verification.

Access tokens carry the user id (`sub`) and wallet address (`wallet`) as
claims. We deliberately keep tokens short-lived (see
`Settings.access_token_expire_minutes`) and stateless — no server-side
session store — because the wallet-based sign-in flow makes re-authenticating
cheap (sign a new SIWE message) compared to the complexity of a refresh-token
rotation scheme. That trade-off should be revisited in Phase 10 if product
requirements call for longer-lived sessions.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from jose import JWTError, jwt

from app.core.config import Settings


class TokenError(Exception):
    """Raised when a token is missing, malformed, expired, or invalid."""


def create_access_token(*, user_id: uuid.UUID, wallet_address: str, settings: Settings) -> str:
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    claims: dict[str, Any] = {
        "sub": str(user_id),
        "wallet": wallet_address,
        "iat": now,
        "exp": expires_at,
    }
    # python-jose's stubs type `encode` as returning Any; per its docs this
    # is always a `str` (compact JWS serialization).
    return cast(str, jwt.encode(claims, settings.secret_key, algorithm=settings.jwt_algorithm))


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        # Same stub gap as above: `decode` returns Any but is documented to
        # always return the claims dict on success.
        return cast(
            dict[str, Any],
            jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm]),
        )
    except JWTError as exc:
        raise TokenError("Invalid or expired token") from exc
