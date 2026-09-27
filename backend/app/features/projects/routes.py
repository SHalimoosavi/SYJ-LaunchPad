from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.projects.dependencies import get_owned_project
from app.features.projects.models import Project
from app.features.projects.schemas import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.features.projects.service import (
    create_project,
    list_projects_for_owner,
    update_project,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def register_project(
    body: ProjectCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Register a new project. The owner is always the authenticated
    caller — nothing in the request body can assign a different owner."""
    return await create_project(db, owner_id=user.id, data=body)


@router.get("/me", response_model=list[ProjectResponse])
async def list_my_projects(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Project]:
    """List every project owned by the authenticated caller."""
    return await list_projects_for_owner(db, user.id)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_my_project(project: Project = Depends(get_owned_project)) -> Project:
    """Fetch a single project. Returns 404 for both a nonexistent project
    and a project owned by someone else — see dependencies.py for why."""
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_my_project(
    body: ProjectUpdateRequest,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Partially update a project. Only reachable for the owning user —
    `get_owned_project` already rejected anyone else before this runs."""
    return await update_project(db, project=project, data=body)
