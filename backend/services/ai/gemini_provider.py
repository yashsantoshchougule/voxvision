import httpx

from backend.config import get_settings
from backend.models.common import ReportOutput
from backend.services.ai.base_provider import AIProvider, AIProviderResponseError, parse_report_output

class GeminiProvider(AIProvider):
    name = "gemini"

    async def generate_report(self, payload: dict) -> ReportOutput:
        settings = get_settings()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, params={"key": settings.gemini_api_key}, json={"contents": [{"parts": [{"text": payload["prompt"]}]}]})
            response.raise_for_status()
        try:
            raw = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise AIProviderResponseError("Gemini returned an unexpected response.") from exc
        return parse_report_output(raw, self.name)
