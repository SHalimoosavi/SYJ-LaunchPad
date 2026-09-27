import uuid

from pydantic import BaseModel, Field


class NonceResponse(BaseModel):
    nonce: str


class VerifyRequest(BaseModel):
    message: str = Field(..., description="The raw EIP-4361 SIWE message the wallet signed")
    signature: str = Field(..., description="The signature produced by the wallet")


class UserResponse(BaseModel):
    id: uuid.UUID
    wallet_address: str
    role: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
