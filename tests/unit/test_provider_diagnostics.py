import json
import sys
from types import ModuleType, SimpleNamespace

import pytest

from rag_system.generation.answering import GeminiAnswerProvider, safe_error_details


def install_fake(monkeypatch, response):
    captured = {}

    def generate(**kwargs):
        captured.update(kwargs)
        return response

    google = ModuleType("google")
    google.genai = SimpleNamespace(
        Client=lambda **_: SimpleNamespace(models=SimpleNamespace(generate_content=generate))
    )
    genai = ModuleType("google.genai")
    genai.types = SimpleNamespace(GenerateContentConfig=lambda **kw: kw)
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.genai", genai)
    return captured


def test_budget_finish_reason_and_metadata_reset(monkeypatch):
    response = SimpleNamespace(
        text='{"partial":',
        candidates=[SimpleNamespace(finish_reason=SimpleNamespace(value="MAX_TOKENS"))],
        model_version="test-model-001",
    )
    captured = install_fake(monkeypatch, response)
    provider = GeminiAnswerProvider("secret", "test-model")
    assert provider.generate("OUTPUT FORMAT OVERRIDE") == '{"partial":'
    assert captured["config"]["max_output_tokens"] == 4096
    assert provider.last_diagnostics["finish_reason"] == "MAX_TOKENS"
    assert provider.last_diagnostics["model_version"] == "test-model-001"
    response.candidates = []
    response.model_version = None
    provider.generate("text prompt")
    assert captured["config"]["max_output_tokens"] == 256
    assert "finish_reason" not in provider.last_diagnostics


def test_empty_output_is_distinguishable(monkeypatch):
    install_fake(monkeypatch, SimpleNamespace(text="  "))
    provider = GeminiAnswerProvider("secret", "test-model")
    with pytest.raises(RuntimeError, match="empty answer"):
        provider.generate("prompt")
    assert provider.last_diagnostics["error_category"] == "empty_response"


@pytest.mark.parametrize(
    "code,category",
    [
        (429, "rate_limit"),
        (503, "unavailable"),
        (401, "authentication"),
        (404, "model_or_endpoint_not_found"),
    ],
)
def test_wrapped_errors_keep_status_without_secret_messages(code, category):
    cause = RuntimeError("secret-key and private prompt")
    cause.code = code
    error = RuntimeError("wrapper contains secret-key")
    error.__cause__ = cause
    details = safe_error_details(error)
    assert details["http_status"] == code
    assert details["error_category"] == category
    assert "secret" not in json.dumps(details)


def test_unknown_and_timeout_are_not_guessed_from_messages():
    assert safe_error_details(RuntimeError("503 secret"))["error_category"] == "unknown"
    assert safe_error_details(TimeoutError("secret"))["error_category"] == "timeout"
