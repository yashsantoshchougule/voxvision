from backend.models.common import ReportOutput, Task
from backend.services.ai.base_provider import AIProvider

class DemoProvider(AIProvider):
    name = "demo"
    async def generate_report(self, payload: dict) -> ReportOutput:
        transcript = payload.get("transcript", "")
        screen = payload.get("screen_text", "")
        important = payload.get("important_points", [])
        lines = [line.strip() for line in transcript.splitlines() if line.strip()]
        notes = lines[:12] or ([screen] if screen else ["No meeting text was captured."])
        return ReportOutput(notes=notes, summary=" ".join(notes[:3]), insights=["Review the captured notes for follow-up items."], decisions=[item.get("transcript_context", "") for item in important if item.get("label") == "Decision" and item.get("transcript_context")], tasks=[Task(task=item.get("user_note") or item.get("transcript_context")) for item in important if item.get("label") == "Task" and (item.get("user_note") or item.get("transcript_context"))], uncertain_information=["Demo provider output should be reviewed before sharing."])
