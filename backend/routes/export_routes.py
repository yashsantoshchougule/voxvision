from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.database.mongodb import db
from backend.routes.meeting_routes import require_meeting
from backend.services.pdf_export_service import build_pdf
from backend.services.word_export_service import build_docx

router = APIRouter(prefix="/api/meetings/{meeting_id}/export", tags=["export"])

@router.get("/docx")
def export_docx(meeting_id: str):
    meeting = require_meeting(meeting_id)
    reports = db.find("reports", {"meeting_id": meeting_id})
    if not reports:
        raise HTTPException(status_code=404, detail={"error": "Generate a report before exporting."})
    output = build_docx(meeting, reports[0], db.find("important_points", {"meeting_id": meeting_id}), db.find("screen_text", {"meeting_id": meeting_id}))
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f'attachment; filename="voxvision-report-{meeting_id}.docx"'})


@router.get("/pdf")
def export_pdf(meeting_id: str):
    meeting = require_meeting(meeting_id)
    reports = db.find("reports", {"meeting_id": meeting_id})
    if not reports:
        raise HTTPException(status_code=404, detail={"error": "Generate a report before exporting."})
    output = build_pdf(meeting, reports[0], db.find("important_points", {"meeting_id": meeting_id}), db.find("screen_text", {"meeting_id": meeting_id}))
    return StreamingResponse(output, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="voxvision-report-{meeting_id}.pdf"'})
