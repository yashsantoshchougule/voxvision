from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_meeting_transcript_report_flow():
    meeting = client.post("/api/meetings", json={"title": "Demo", "platform": "example.com", "selected_mode": "combined"}).json()
    meeting_id = meeting["id"]
    assert meeting["platform"] == "example.com"
    assert client.post(f"/api/meetings/{meeting_id}/transcripts", json={"text": "Frontend is due Friday."}).status_code == 201
    assert client.post(f"/api/meetings/{meeting_id}/important-points", json={"label": "Task", "transcript_context": "Frontend is due Friday."}).status_code == 201
    assert client.post(f"/api/meetings/{meeting_id}/stop").status_code == 200
    report = client.post(f"/api/meetings/{meeting_id}/reports/generate")
    assert report.status_code == 200
    assert report.json()["summary"]
    original_notes = report.json()["notes"]
    updated = client.put(f"/api/meetings/{meeting_id}/report", json={"summary": "Edited summary"})
    assert updated.status_code == 200
    assert updated.json()["summary"] == "Edited summary"
    assert updated.json()["notes"] == original_notes
    export = client.get(f"/api/meetings/{meeting_id}/export/docx")
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("application/vnd.openxmlformats")
    pdf_export = client.get(f"/api/meetings/{meeting_id}/export/pdf")
    assert pdf_export.status_code == 200
    assert pdf_export.headers["content-type"].startswith("application/pdf")
    assert pdf_export.content.startswith(b"%PDF-")
    assert ".pdf" in pdf_export.headers["content-disposition"]


def test_delete_missing_meeting_returns_not_found():
    response = client.delete("/api/meetings/does-not-exist")
    assert response.status_code == 404
