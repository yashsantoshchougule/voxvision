from backend.database.mongodb import db, utc_now
from backend.models.common import jsonable
from backend.models.important_point_model import ImportantPointCreate
from backend.routes.meeting_routes import require_meeting
from fastapi import APIRouter

router = APIRouter(prefix="/api/meetings/{meeting_id}", tags=["important-points"])

@router.post("/important-points", status_code=201)
@router.post("/important", status_code=201)
def add_important_point(meeting_id: str, payload: ImportantPointCreate) -> dict:
    require_meeting(meeting_id)
    document = payload.model_dump() | {"meeting_id": meeting_id, "created_at": utc_now()}
    document["content"] = document["content"] or document["user_note"] or document["transcript_context"] or document["screen_context"]
    return jsonable({**document, "_id": db.insert("important_points", document)})

@router.get("/important-points")
@router.get("/important")
def get_important_points(meeting_id: str) -> list[dict]:
    require_meeting(meeting_id)
    return [jsonable(item) for item in db.find("important_points", {"meeting_id": meeting_id})]
