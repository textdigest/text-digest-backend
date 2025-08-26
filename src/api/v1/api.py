from fastapi import APIRouter

from .endpoints import health, library, reader, users

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["Health Check"])

router.include_router(library.router, prefix="/library", tags=["Library Service"])

router.include_router(reader.router, prefix="/reader", tags=["eReader Service"])

router.include_router(users.router, prefix="/users", tags=["Users Service"])