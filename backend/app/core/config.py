"""Application configuration, loaded from environment variables.

All configuration lives here so that no other module reads `os.environ`
directly. This keeps secrets/config auditable in one place and makes tests
trivial (override `Settings` via dependency injection or env vars).
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Core ---
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    secret_key: str = Field(..., min_length=32)
    api_v1_prefix: str = Field(default="/api/v1")
    allowed_origins: str = Field(default="http://localhost:3000")

    # --- Database ---
    database_url: str
    database_url_sync: str

    # --- Auth ---
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)
    siwe_nonce_ttl_seconds: int = Field(default=300)

    # --- Rate limiting ---
    rate_limit_default: str = Field(default="100/minute")

    # --- Chains ---
    enabled_chain_ids: str = Field(default="1")

    @field_validator("environment")
    @classmethod
    def _validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def chain_ids(self) -> list[int]:
        return [int(c.strip()) for c in self.enabled_chain_ids.split(",") if c.strip()]

    def rpc_url_for(self, chain_id: int) -> str | None:
        import os

        return os.environ.get(f"RPC_URL_{chain_id}") or None

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton. Use as a FastAPI dependency."""
    return Settings()  # type: ignore[call-arg]
