from fastapi import APIRouter

from api.v1.endpoints import health, library

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["Health Check"])

router.include_router(library.router, prefix="/library", tags=["Library Service"])