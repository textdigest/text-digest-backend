from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def health_check():
    return {"message": "API is healthy."}