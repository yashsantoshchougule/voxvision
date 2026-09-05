import httpx

from backend.config import get_settings
from backend.models.common import ReportOutput
from backend.services.ai.base_provider import AIProvider, AIProviderResponseError, parse_report_output


class OpenAIProvider(AIProvider):
    name = "openai"

    async def generate_report(self, payload: dict) -> ReportOutput:
        settings = get_settings()
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("A report prompt is required.")
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": settings.openai_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise AIProviderResponseError("OpenAI returned an unexpected response.") from exc
        return parse_report_output(content, self.name)
