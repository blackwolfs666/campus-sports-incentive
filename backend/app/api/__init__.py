# API module
from fastapi import APIRouter
from .auth import router as auth_router
from .steps import router as steps_router
from .ranking import router as ranking_router
from .prizes import router as prizes_router
from .checkins import router as checkins_router
from .activities import router as activities_router
from .admin import router as admin_router
from .cas import router as cas_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(steps_router)
api_router.include_router(ranking_router)
api_router.include_router(prizes_router)
api_router.include_router(checkins_router)
api_router.include_router(activities_router)
api_router.include_router(admin_router)
api_router.include_router(cas_router)
