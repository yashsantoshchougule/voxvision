from abc import ABC, abstractmethod

from pydantic import ValidationError

from backend.models.common import ReportOutput


class AIProviderResponseError(RuntimeError):
    """Raised when an AI provider returns no usable report JSON."""


class AIProviderConnectionError(RuntimeError):
    """Raised when a configured local AI service cannot be reached."""


def parse_report_output(raw: object, provider_name: str) -> ReportOutput:
    """Validate the provider's JSON response before it reaches the API route."""
    if not isinstance(raw, str) or not raw.strip():
        raise AIProviderResponseError(f"{provider_name} returned an empty report response.")

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 2 and lines[-1].strip().startswith("```"):
            cleaned = "\n".join(lines[1:-1]).strip()

    try:
        return ReportOutput.model_validate_json(cleaned)
    except ValidationError as exc:
        raise AIProviderResponseError(f"{provider_name} returned an invalid report response.") from exc


class AIProvider(ABC):
    name = "base"
    @abstractmethod
    async def generate_report(self, payload: dict) -> ReportOutput:
        raise NotImplementedError
