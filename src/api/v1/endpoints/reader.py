from fastapi import APIRouter

router = APIRouter()

# BOILERPLATE

@router.get("/")
async def route():
    return {}