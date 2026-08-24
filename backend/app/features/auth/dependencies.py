"""Dependencies for protecting routes with JWT auth.

`get_current_user` is what every protected route in every future feature
should depend on — it's the single place that turns a bearer token into a
loaded `User`, so authorization logic (e.g. role checks) can be layered on
top consistently instead of re-implemented per route.
"""

import uuid
from collections.abc import Awaitable, Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ForbiddenError, UnauthorizedError
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.features.auth.models import User, UserRole
from app.features.auth.security import TokenError, decode_access_token
from app.features.auth.service import get_user_by_id

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token")

    try:
        claims = decode_access_token(credentials.credentials, settings)
        user_id = uuid.UUID(claims["sub"])
    except (TokenError, KeyError, ValueError) as exc:
        raise UnauthorizedError("Invalid or expired token") from exc

    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    return user


def require_role(*allowed_roles: UserRole) -> Callable[..., Awaitable[User]]:
    """Dependency factory for role-gated routes, e.g.:
    `Depends(require_role(UserRole.ADMIN))`. Real permission granularity
    (per-project roles, etc.) lands with the Admin Dashboard in Phase 8;
    this is the minimal hook future features attach to.
    """

    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise ForbiddenError("You do not have permission to perform this action")
        return user

    return _check
