from backend.config import get_settings
from backend.services.ai.demo_provider import DemoProvider
from backend.services.ai.gemini_provider import GeminiProvider
from backend.services.ai.ollama_provider import OllamaProvider
from backend.services.ai.openai_provider import OpenAIProvider
from backend.services.ai.openrouter_provider import OpenRouterProvider


class ProviderConfigurationError(ValueError):
    """Raised for an unsupported provider or a provider missing its API key."""


def get_provider():
    settings = get_settings()
    provider = settings.ai_provider.strip().casefold() or "auto"

    if provider == "auto":
        if settings.openai_api_key:
            return OpenAIProvider()
        if settings.gemini_api_key:
            return GeminiProvider()
        if settings.openrouter_api_key:
            return OpenRouterProvider()
        return DemoProvider()

    if provider == "demo":
        return DemoProvider()
    if provider == "ollama":
        return OllamaProvider()

    providers = {
        "gemini": (settings.gemini_api_key, GeminiProvider),
        "openai": (settings.openai_api_key, OpenAIProvider),
        "openrouter": (settings.openrouter_api_key, OpenRouterProvider),
    }
    if provider not in providers:
        supported = ", ".join(("auto", "demo", "ollama", *providers))
        raise ProviderConfigurationError(f"Unsupported AI_PROVIDER '{provider}'. Use one of: {supported}.")

    api_key, provider_class = providers[provider]
    if not api_key:
        env_name = f"{provider.upper()}_API_KEY"
        raise ProviderConfigurationError(f"AI_PROVIDER='{provider}' requires {env_name}.")
    return provider_class()
