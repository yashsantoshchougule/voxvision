import pytest

from backend.config import get_settings


@pytest.fixture(autouse=True)
def use_demo_provider(monkeypatch):
    """Keep the test suite offline even when a developer has an API key locally."""
    monkeypatch.setenv("AI_PROVIDER", "demo")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
