from fastapi import APIRouter
from app.api.api_v1.endpoints import receipts, auth, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(receipts.router, prefix="/receipts", tags=["receipts"]) 