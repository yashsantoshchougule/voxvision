from backend.database.mongodb import db, utc_now
from backend.models.common import jsonable
from backend.models.transcript_model import TranscriptBatch, TranscriptCreate
from backend.routes.meeting_routes import require_meeting
from fastapi import APIRouter

router = APIRouter(prefix="/api/meetings/{meeting_id}/transcripts", tags=["transcripts"])

def save_transcript(meeting_id: str, item: TranscriptCreate) -> dict:
    require_meeting(meeting_id)
    document = item.model_dump() | {"meeting_id": meeting_id, "processed": False, "created_at": utc_now()}
    return jsonable({**document, "_id": db.insert("transcripts", document)})

@router.post("", status_code=201)
@router.post("/transcript", status_code=201)
def add_transcript(meeting_id: str, payload: TranscriptCreate) -> dict:
    return save_transcript(meeting_id, payload)

@router.post("/batch", status_code=201)
def add_transcript_batch(meeting_id: str, payload: TranscriptBatch) -> list[dict]:
    return [save_transcript(meeting_id, item) for item in payload.items]

@router.get("")
@router.get("/transcript")
def get_transcripts(meeting_id: str) -> list[dict]:
    require_meeting(meeting_id)
    return [jsonable(item) for item in db.find("transcripts", {"meeting_id": meeting_id})]
