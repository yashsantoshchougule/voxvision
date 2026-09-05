from fastapi import APIRouter
from backend.database.mongodb import db

router = APIRouter()

@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "VoxVision AI", "database": db.status()}
