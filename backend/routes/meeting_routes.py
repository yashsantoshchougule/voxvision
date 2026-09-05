from backend.database.mongodb import db, utc_now
from backend.models.common import jsonable
from backend.models.meeting_model import MeetingCreate, MeetingPatch
from backend.utils.response_helper import not_found
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/meetings", tags=["meetings"])

def require_meeting(meeting_id: str) -> dict:
    meeting = db.get("meetings", meeting_id)
    if not meeting:
        raise not_found("Meeting not found")
    return meeting

@router.post("", status_code=201)
@router.post("/start", status_code=201)
def create_meeting(payload: MeetingCreate) -> dict:
    now = utc_now()
    document = payload.model_dump() | {"status": "active", "started_at": now, "ended_at": None, "created_at": now, "updated_at": now}
    return jsonable({**document, "_id": db.insert("meetings", document)})

@router.get("")
def list_meetings() -> list[dict]:
    return [jsonable(item) for item in db.find("meetings")]

@router.get("/{meeting_id}")
def get_meeting(meeting_id: str) -> dict:
    return jsonable(require_meeting(meeting_id))

@router.patch("/{meeting_id}")
def patch_meeting(meeting_id: str, payload: MeetingPatch) -> dict:
    require_meeting(meeting_id)
    changes = {key: value for key, value in payload.model_dump().items() if value is not None} | {"updated_at": utc_now()}
    db.update("meetings", {"_id": meeting_id}, changes)
    return jsonable(require_meeting(meeting_id))

@router.post("/{meeting_id}/pause")
def pause_meeting(meeting_id: str) -> dict:
    require_meeting(meeting_id)
    db.update("meetings", {"_id": meeting_id}, {"status": "paused", "updated_at": utc_now()})
    return jsonable(require_meeting(meeting_id))

@router.post("/{meeting_id}/resume")
def resume_meeting(meeting_id: str) -> dict:
    require_meeting(meeting_id)
    db.update("meetings", {"_id": meeting_id}, {"status": "active", "updated_at": utc_now()})
    return jsonable(require_meeting(meeting_id))

@router.post("/{meeting_id}/stop")
def stop_meeting(meeting_id: str) -> dict:
    require_meeting(meeting_id)
    db.update("meetings", {"_id": meeting_id}, {"status": "processing", "ended_at": utc_now(), "updated_at": utc_now()})
    return jsonable(require_meeting(meeting_id))

@router.delete("/{meeting_id}")
def delete_meeting(meeting_id: str) -> dict:
    if not db.delete_meeting(meeting_id):
        raise not_found("Meeting not found")
    return {"deleted": True, "id": meeting_id}
