import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=5000)
    website_url: str | None = Field(default=None, max_length=2048)


class ProjectUpdateRequest(BaseModel):
    """Partial update. `slug` is intentionally not updatable here — see
    the immutability note on `Project.slug` in models.py."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=5000)
    website_url: str | None = Field(default=None, max_length=2048)
    is_active: bool | None = Field(default=None)


class ProjectResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    website_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
