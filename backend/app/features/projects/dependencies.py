"""Ownership-enforcement dependency for project routes.

`get_owned_project` is the single place cross-user access is denied — every
route that reads or mutates a specific project depends on this rather than
re-implementing the ownership check inline, so there's exactly one place to
audit for this security boundary.
"""

import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import NotFoundError
from app.db.session import get_db
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.projects.models import Project
from app.features.projects.service import get_project_by_id


async def get_owned_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    project = await get_project_by_id(db, project_id)

    # A project that doesn't exist and a project that exists but belongs
    # to someone else get the IDENTICAL response: 404. Returning 403 for
    # the latter would let a caller enumerate valid project IDs by
    # distinguishing "not found" from "not yours" — the same reasoning
    # already applied to nonce validation in Phase 2 (see
    # auth/service.py's _consume_nonce), applied here to project IDs.
    if project is None or project.owner_id != user.id:
        raise NotFoundError("Project not found")

    return project
