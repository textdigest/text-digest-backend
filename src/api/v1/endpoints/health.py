from fastapi import APIRouter, Request, HTTPException
from util.tokens.verifyIdToken import verify_token

router = APIRouter()

@router.get("/")
async def health_check(request: Request):
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return {"message": "API is healthy."}

    user_id = verify_token(auth_header)

    return {"message": "API is healthy.", "user_id": user_id}