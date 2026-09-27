"""Project business logic.

Ownership is enforced here and in `dependencies.py`, never trusting
anything the client sends for identity — `owner_id` always comes from the
authenticated `User` the caller passes in, not from request bodies.
"""

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ConflictError
from app.features.projects.models import Project
from app.features.projects.schemas import ProjectCreateRequest, ProjectUpdateRequest

_SLUG_COLLAPSE_RE = re.compile(r"[^a-z0-9]+")
_SLUG_MAX_LEN = 120


def _slugify(name: str) -> str:
    """Deterministically derive a URL-safe slug from a project name.

    Server-side only — never accepts a client-supplied slug (see the note
    on `Project.slug`). Not a cryptographic function, just a plain
    normalization; collisions are handled by the caller via the unique
    index + `ConflictError`, not by trying to make this function perfect.
    """
    lowered = name.strip().lower()
    collapsed = _SLUG_COLLAPSE_RE.sub("-", lowered).strip("-")
    if not collapsed:
        # A name made entirely of symbols/whitespace still needs a valid,
        # non-empty slug — fall back to a short random suffix rather than
        # reject a name the ProjectCreateRequest schema already accepted.
        collapsed = f"project-{uuid.uuid4().hex[:8]}"
    return collapsed[:_SLUG_MAX_LEN]


async def create_project(
    db: AsyncSession, *, owner_id: uuid.UUID, data: ProjectCreateRequest
) -> Project:
    slug = _slugify(data.name)

    existing = await db.execute(select(Project).where(Project.slug == slug))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(
            "A project with a very similar name already exists. Please choose a different name."
        )

    project = Project(
        owner_id=owner_id,
        name=data.name,
        slug=slug,
        description=data.description,
        website_url=data.website_url,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def get_project_by_id(db: AsyncSession, project_id: uuid.UUID) -> Project | None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def list_projects_for_owner(db: AsyncSession, owner_id: uuid.UUID) -> list[Project]:
    result = await db.execute(
        select(Project).where(Project.owner_id == owner_id).order_by(Project.created_at.desc())
    )
    return list(result.scalars().all())


async def update_project(
    db: AsyncSession, *, project: Project, data: ProjectUpdateRequest
) -> Project:
    """Apply a partial update. Caller (the route, via
    `dependencies.get_owned_project`) is responsible for having already
    verified the requester owns `project` — this function does not
    re-check ownership, it only applies field changes."""
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project
