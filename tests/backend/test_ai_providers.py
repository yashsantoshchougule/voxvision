import httpx
import pytest

from backend.config import get_settings
from backend.models.common import ReportOutput
from backend.services.ai.base_provider import AIProviderConnectionError, AIProviderResponseError, parse_report_output
from backend.services.ai.ollama_provider import OllamaProvider
from backend.services.ai.openai_provider import OpenAIProvider
from backend.services.ai.provider_factory import ProviderConfigurationError, get_provider


def test_auto_provider_prefers_openai_when_its_key_is_available(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "auto")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    get_settings.cache_clear()

    assert get_provider().name == "openai"


def test_explicit_provider_without_a_key_is_actionable(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()

    with pytest.raises(ProviderConfigurationError, match="OPENAI_API_KEY"):
        get_provider()


def test_ollama_provider_requires_no_api_key(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    get_settings.cache_clear()

    assert get_provider().name == "ollama"


def test_invalid_ai_json_is_rejected():
    with pytest.raises(AIProviderResponseError, match="invalid report"):
        parse_report_output("not JSON", "OpenAI")


@pytest.mark.asyncio
async def test_openai_provider_sends_json_mode_and_validates_response(monkeypatch):
    class FakeClient:
        def __init__(self):
            self.calls = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, **kwargs):
            self.calls.append((url, kwargs))
            request = httpx.Request("POST", url)
            return httpx.Response(200, request=request, json={"choices": [{"message": {"content": '{"summary": "Ready"}'}}]})

    fake_client = FakeClient()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr("backend.services.ai.openai_provider.httpx.AsyncClient", lambda **kwargs: fake_client)

    result = await OpenAIProvider().generate_report({"prompt": "Return a JSON report."})

    assert result.summary == "Ready"
    assert fake_client.calls[0][0] == "https://api.openai.com/v1/chat/completions"
    assert fake_client.calls[0][1]["json"]["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_ollama_provider_uses_local_structured_output(monkeypatch):
    class FakeClient:
        def __init__(self):
            self.calls = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, **kwargs):
            self.calls.append((url, kwargs))
            request = httpx.Request("POST", url)
            return httpx.Response(200, request=request, json={"message": {"content": '{"summary": "Local"}'}})

    fake_client = FakeClient()
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/")
    monkeypatch.setenv("OLLAMA_MODEL", "test-model")
    get_settings.cache_clear()
    monkeypatch.setattr("backend.services.ai.ollama_provider.httpx.AsyncClient", lambda **kwargs: fake_client)

    result = await OllamaProvider().generate_report({"prompt": "Return a JSON report."})

    assert result.summary == "Local"
    assert fake_client.calls[0][0] == "http://127.0.0.1:11434/api/chat"
    request_body = fake_client.calls[0][1]["json"]
    assert request_body["model"] == "test-model"
    assert request_body["stream"] is False
    assert request_body["think"] is False
    assert request_body["format"] == ReportOutput.model_json_schema()
    assert request_body["options"] == {"temperature": 0}


@pytest.mark.asyncio
async def test_ollama_provider_reports_connection_failures(monkeypatch):
    class OfflineClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, **kwargs):
            request = httpx.Request("POST", url)
            raise httpx.ConnectError("offline", request=request)

    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    get_settings.cache_clear()
    monkeypatch.setattr("backend.services.ai.ollama_provider.httpx.AsyncClient", lambda **kwargs: OfflineClient())

    with pytest.raises(AIProviderConnectionError, match="Start Ollama"):
        await OllamaProvider().generate_report({"prompt": "Return a JSON report."})
