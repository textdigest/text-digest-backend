from fastapi import APIRouter

from api.v1.endpoints import health, library, reader

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["Health Check"])

router.include_router(library.router, prefix="/library", tags=["Library Service"])

router.include_router(reader.router, prefix="/reader", tags=["Reader Service"])