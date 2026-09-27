from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.auth.schemas import (
    NonceResponse,
    TokenResponse,
    UserResponse,
    VerifyRequest,
)
from app.features.auth.security import create_access_token
from app.features.auth.service import issue_nonce, verify_siwe_and_get_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/nonce", response_model=NonceResponse)
async def get_nonce(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> NonceResponse:
    """Issue a single-use nonce for a wallet to sign into a SIWE message."""
    nonce = await issue_nonce(db, settings)
    return NonceResponse(nonce=nonce)


@router.post("/verify", response_model=TokenResponse)
async def verify_signature(
    body: VerifyRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Verify a signed SIWE message and issue a JWT session on success."""
    user, wallet_address = await verify_siwe_and_get_user(
        db, settings, raw_message=body.message, signature=body.signature
    )
    token = create_access_token(user_id=user.id, wallet_address=wallet_address, settings=settings)
    return TokenResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse(id=user.id, wallet_address=wallet_address, role=user.role.value),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    """Return the currently authenticated user, resolved from the JWT."""
    primary_wallet = next((w for w in user.wallets if w.is_primary), None)
    return UserResponse(
        id=user.id,
        wallet_address=primary_wallet.address if primary_wallet else "",
        role=user.role.value,
    )
