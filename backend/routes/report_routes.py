from backend.database.mongodb import db, utc_now
from backend.models.common import jsonable
from backend.models.report_model import ReportUpdate
from backend.routes.meeting_routes import require_meeting
from backend.services.ai.base_provider import AIProviderConnectionError, AIProviderResponseError
from backend.services.report_service import generate_report
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/meetings/{meeting_id}", tags=["reports"])

@router.post("/reports/generate")
@router.post("/generate-report")
async def create_report(meeting_id: str) -> dict:
    meeting = require_meeting(meeting_id)
    transcripts = db.find("transcripts", {"meeting_id": meeting_id})
    screen_items = db.find("screen_text", {"meeting_id": meeting_id})
    important = db.find("important_points", {"meeting_id": meeting_id})
    try:
        output, provider = await generate_report(meeting.get("selected_mode", "combined"), transcripts, screen_items, important)
    except AIProviderConnectionError as exc:
        db.update("meetings", {"_id": meeting_id}, {"status": "failed", "updated_at": utc_now()})
        raise HTTPException(status_code=503, detail={"error": str(exc)}) from exc
    except AIProviderResponseError as exc:
        db.update("meetings", {"_id": meeting_id}, {"status": "failed", "updated_at": utc_now()})
        raise HTTPException(status_code=502, detail={"error": str(exc)}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": str(exc)}) from exc
    except Exception as exc:
        db.update("meetings", {"_id": meeting_id}, {"status": "failed", "updated_at": utc_now()})
        raise HTTPException(status_code=502, detail={"error": "Report generation failed. Check the AI provider configuration."}) from exc
    now = utc_now()
    document = output.model_dump() | {"meeting_id": meeting_id, "mode": meeting.get("selected_mode", "combined"), "provider": provider, "created_at": now, "updated_at": now}
    old = db.find("reports", {"meeting_id": meeting_id})
    if old:
        db.update("reports", {"_id": old[0]["_id"]}, document)
        report = db.get("reports", str(old[0]["_id"])) or {**document, "_id": old[0]["_id"]}
    else:
        report = {**document, "_id": db.insert("reports", document)}
    db.update("meetings", {"_id": meeting_id}, {"status": "completed", "updated_at": now})
    return jsonable(report)

@router.get("/report")
def get_report(meeting_id: str) -> dict:
    require_meeting(meeting_id)
    report = db.find("reports", {"meeting_id": meeting_id})
    if not report:
        raise HTTPException(status_code=404, detail={"error": "Report has not been generated yet."})
    return jsonable(report[0])

@router.put("/report")
def update_report(meeting_id: str, payload: ReportUpdate) -> dict:
    require_meeting(meeting_id)
    report = db.find("reports", {"meeting_id": meeting_id})
    if not report:
        raise HTTPException(status_code=404, detail={"error": "Report has not been generated yet."})
    changes = payload.model_dump(exclude_unset=True, exclude_none=True) | {"updated_at": utc_now()}
    db.update("reports", {"_id": report[0]["_id"]}, changes)
    return jsonable(db.find("reports", {"meeting_id": meeting_id})[0])
