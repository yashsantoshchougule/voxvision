from backend.config import get_settings
from backend.database.mongodb import db, utc_now
from backend.models.common import jsonable
from backend.models.screen_text_model import ScreenTextCreate
from backend.routes.meeting_routes import require_meeting
from backend.services.ocr_service import extract_text
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/api/meetings/{meeting_id}", tags=["screen"])

@router.post("/screen/analyze", status_code=201)
async def analyze_screen(meeting_id: str, file: UploadFile = File(...), change_score: float = 0.0) -> dict:
    require_meeting(meeting_id)
    settings = get_settings()
    if file.content_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(status_code=415, detail={"error": "Only PNG, JPEG, and WebP images are accepted."})
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"error": "Image exceeds the upload size limit."})
    try:
        result = extract_text(data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail={"error": f"Could not process the image: {exc.__class__.__name__}"}) from exc
    result["change_score"] = max(0.0, min(1.0, change_score))
    result["meeting_id"] = meeting_id
    result["created_at"] = utc_now()
    result["extracted_text"] = result.get("extracted_text", "")
    return jsonable({**result, "_id": db.insert("screen_text", result)})

@router.post("/screen-text", status_code=201)
def add_screen_text(meeting_id: str, payload: ScreenTextCreate) -> dict:
    require_meeting(meeting_id)
    document = payload.model_dump() | {"meeting_id": meeting_id, "frame_stored": False, "created_at": utc_now()}
    return jsonable({**document, "_id": db.insert("screen_text", document)})


@router.get("/screen-text")
def get_screen_text(meeting_id: str) -> list[dict]:
    require_meeting(meeting_id)
    return [jsonable(item) for item in db.find("screen_text", {"meeting_id": meeting_id})]
