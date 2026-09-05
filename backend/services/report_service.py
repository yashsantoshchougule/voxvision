import json
from pathlib import Path
from backend.config import get_settings
from backend.models.common import ReportOutput
from backend.services.ai.provider_factory import get_provider
from backend.services.chunking_service import chunk_text
from backend.services.text_cleaner_service import clean_entries

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "report_prompt.txt"

async def generate_report(mode: str, transcript_items: list[dict], screen_items: list[dict], important_items: list[dict]) -> tuple[ReportOutput, str]:
    settings = get_settings()
    transcript = "\n".join(clean_entries([item.get("text", "") for item in transcript_items]))
    screen_text = "\n".join(clean_entries([item.get("extracted_text", "") for item in screen_items]))
    chart_data = json.dumps([{key: item.get(key) for key in ("chart_type", "parsed_values", "basic_observation")} for item in screen_items if item.get("chart_type")])
    if not transcript and not screen_text and not important_items:
        raise ValueError("No meeting text was captured.")
    transcript = transcript[:settings.max_ai_input_characters]
    chunks = chunk_text(transcript, settings.report_chunk_size)
    transcript = "\n".join(chunks)
    prompt = PROMPT_PATH.read_text(encoding="utf-8").format(output_mode=mode, transcript=transcript, screen_text=screen_text[:settings.max_ai_input_characters], chart_data=chart_data, important_points=json.dumps(important_items, default=str))
    provider = get_provider()
    result = await provider.generate_report({"prompt": prompt, "transcript": transcript, "screen_text": screen_text, "important_points": important_items})
    return ReportOutput.model_validate(result), provider.name
