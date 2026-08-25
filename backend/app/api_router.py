"""Aggregates every feature's router under the versioned API prefix.

Adding a new feature = add one `include_router` line here. This is the only
file that needs to know every feature exists; features never import each
other's routes directly.
"""

from fastapi import APIRouter

from app.features.auth.routes import router as auth_router
from app.features.health.routes import router as health_router
from app.features.projects.routes import router as projects_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(projects_router)

# Phase 4+: token_router, presale_router, claim_router, vesting_router,
# referral_router, admin_router, dashboard_router, ...
