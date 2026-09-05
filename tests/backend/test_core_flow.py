from fastapi.testclient import TestClient

from backend.main import app
from backend.services.text_cleaner_service import clean_entries


client = TestClient(app)


def test_meeting_transcript_and_demo_report_flow() -> None:
    meeting = client.post("/api/meetings", json={"title": "Sprint planning", "selected_mode": "combined"})
    assert meeting.status_code == 201
    meeting_id = meeting.json()["id"]

    transcript = client.post(
        f"/api/meetings/{meeting_id}/transcripts/batch",
        json={"items": [{"text": "Yash will complete the frontend by Friday.", "source": "microphone"}]},
    )
    assert transcript.status_code == 201
    assert len(client.get(f"/api/meetings/{meeting_id}/transcripts").json()) == 1

    assert client.post(f"/api/meetings/{meeting_id}/important-points", json={"label": "Task", "user_note": "Complete frontend"}).status_code == 201
    assert client.post(f"/api/meetings/{meeting_id}/stop").status_code == 200
    report = client.post(f"/api/meetings/{meeting_id}/reports/generate")
    assert report.status_code == 200
    assert report.json()["summary"]
    assert client.get(f"/api/meetings/{meeting_id}/export/docx").status_code == 200


def test_text_cleaning_preserves_meaningful_content() -> None:
    result = clean_entries(["Okay", "Hello", "The frontend is due Friday.", "the frontend is due friday", "The frontend is due Friday and needs review."])
    assert result == ["The frontend is due Friday and needs review."]
