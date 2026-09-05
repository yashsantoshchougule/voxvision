import httpx

from backend.config import get_settings
from backend.models.common import ReportOutput
from backend.services.ai.base_provider import (
    AIProvider,
    AIProviderConnectionError,
    AIProviderResponseError,
    parse_report_output,
)


class OllamaProvider(AIProvider):
    name = "ollama"

    async def generate_report(self, payload: dict) -> ReportOutput:
        settings = get_settings()
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("A report prompt is required.")

        base_url = settings.ollama_base_url.rstrip("/")
        url = f"{base_url}/api/chat"
        request_body = {
            "model": settings.ollama_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "think": False,
            "format": ReportOutput.model_json_schema(),
            "options": {"temperature": 0},
        }

        try:
            async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
                response = await client.post(url, json=request_body)
                response.raise_for_status()
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise AIProviderConnectionError(
                f"Ollama is not reachable at {base_url}. Start Ollama and try again."
            ) from exc
        except httpx.HTTPStatusError as exc:
            detail = _ollama_error_detail(exc.response)
            raise AIProviderResponseError(f"Ollama request failed: {detail}") from exc

        try:
            content = response.json()["message"]["content"]
        except (KeyError, TypeError, ValueError) as exc:
            raise AIProviderResponseError("Ollama returned an unexpected response.") from exc
        return parse_report_output(content, self.name)


def _ollama_error_detail(response: httpx.Response) -> str:
    try:
        detail = response.json().get("error")
    except (TypeError, ValueError):
        detail = None
    if isinstance(detail, str) and detail.strip():
        return detail.strip()
    return f"HTTP {response.status_code}"
