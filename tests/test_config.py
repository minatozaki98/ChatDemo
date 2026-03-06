# tests/test_config.py
import pytest
from backend.config import Settings


def test_settings_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    settings = Settings()
    assert settings.azure_openai_endpoint == "https://test.openai.azure.com/"
    assert settings.azure_openai_api_key == "test-key"
    assert settings.azure_openai_deployment == "gpt-4o"
    assert settings.azure_openai_api_version == "2024-02-01"
