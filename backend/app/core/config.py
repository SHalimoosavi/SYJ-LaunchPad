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
    siwe_domain: str = Field(default="localhost:3000")
    siwe_uri: str = Field(default="http://localhost:3000")

    # --- Rate limiting ---
    rate_limit_default: str = Field(default="100/minute")

    # --- Chains ---
    enabled_chain_ids: str = Field(default="1")

    # Per-chain RPC URLs. Declared explicitly (rather than read from
    # os.environ ad hoc) so every config value in the app flows through
    # this one Settings model — matches the module-level contract stated
    # above. One field per chain in `app.core.chains.SUPPORTED_CHAINS`;
    # pydantic-settings maps each to its `RPC_URL_<id>` env var by name.
    rpc_url_1: str | None = Field(default=None)
    rpc_url_56: str | None = Field(default=None)
    rpc_url_137: str | None = Field(default=None)
    rpc_url_8453: str | None = Field(default=None)
    rpc_url_42161: str | None = Field(default=None)
    rpc_url_10: str | None = Field(default=None)
    rpc_url_43114: str | None = Field(default=None)
    rpc_url_11155111: str | None = Field(default=None)
    rpc_url_97: str | None = Field(default=None)

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
        """Look up the configured RPC URL for a chain, if any is set.

        Reads only from this Settings instance's own declared fields —
        never from `os.environ` directly — so RPC configuration goes
        through the same single, auditable, type-checked path as every
        other setting in this module.
        """
        rpc_urls_by_chain_id: dict[int, str | None] = {
            1: self.rpc_url_1,
            56: self.rpc_url_56,
            137: self.rpc_url_137,
            8453: self.rpc_url_8453,
            42161: self.rpc_url_42161,
            10: self.rpc_url_10,
            43114: self.rpc_url_43114,
            11155111: self.rpc_url_11155111,
            97: self.rpc_url_97,
        }
        return rpc_urls_by_chain_id.get(chain_id) or None

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton. Use as a FastAPI dependency."""
    return Settings()  # type: ignore[call-arg]
