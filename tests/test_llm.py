import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import llm  # noqa: E402


class Reply(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def fake(monkeypatch, replies):
    """Replace urlopen; `replies` is a list of dicts (returned) or exceptions (raised). Records each request."""
    seen = []

    def urlopen(req, timeout=None):
        seen.append((req.full_url, json.loads(req.data or b"null"), dict(req.header_items())))
        r = replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return Reply(json.dumps(r).encode())

    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen)
    return seen


def http_error(code):
    return urllib.error.HTTPError("http://x", code, "err", {}, io.BytesIO(b'{"error": "bad"}'))


def test_settings_precedence_and_legacy_names():
    assert llm.settings(env={})["backend"] == "ollama"
    assert llm.settings(env={})["base_url"] == "http://localhost:11434"
    s = llm.settings(env={"OLLAMA_HOST": "http://h:1/", "OLLAMA_MODEL": "m1"})
    assert (s["backend"], s["base_url"], s["model"]) == ("ollama", "http://h:1", "m1")
    s = llm.settings(env={"LLM_BACKEND": "openai", "LLM_BASE_URL": "http://s/v1", "LLM_MODEL": "m2", "OLLAMA_MODEL": "old"})
    assert (s["backend"], s["model"]) == ("openai", "m2")
    assert llm.settings(model="cli", env={"LLM_MODEL": "env"})["model"] == "cli"
    assert llm.settings(env={"OLLAMA_VERIFY_MODEL": "v"}, model_env="LLM_VERIFY_MODEL")["model"] == "v"
    with pytest.raises(llm.LLMError):
        llm.settings(backend="nope", env={})


def test_ollama_request_shape(monkeypatch):
    seen = fake(monkeypatch, [{"message": {"content": "hi"}}])
    cfg = llm.settings("ollama", "http://h:11434", "m", env={})
    assert llm.chat("p", cfg, max_tokens=99, num_ctx=4096) == "hi"
    url, body, _ = seen[0]
    assert url == "http://h:11434/api/chat" and body["format"] == "json" and body["options"]["num_ctx"] == 4096 and body["options"]["num_predict"] == 99


def test_openai_sends_key_and_retries_without_json_mode(monkeypatch):
    seen = fake(monkeypatch, [http_error(400), {"choices": [{"message": {"content": "ok"}}]}])
    cfg = llm.settings("openai", "http://s/v1", "m", env={"LLM_API_KEY": "secret"})
    assert llm.chat("p", cfg) == "ok"
    assert "response_format" in seen[0][1] and "response_format" not in seen[1][1]
    assert seen[0][0] == "http://s/v1/chat/completions" and seen[0][2]["Authorization"] == "Bearer secret"


def test_openai_does_not_retry_on_other_errors(monkeypatch):
    fake(monkeypatch, [http_error(401)])
    with pytest.raises(llm.LLMError, match="401"):
        llm.chat("p", llm.settings("openai", "http://s/v1", "m", env={}))


def test_anthropic_needs_a_key_and_joins_text_blocks(monkeypatch):
    cfg = llm.settings("anthropic", None, "m", env={})
    with pytest.raises(llm.LLMError, match="LLM_API_KEY"):
        llm.chat("p", cfg)
    seen = fake(monkeypatch, [{"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}])
    cfg = llm.settings("anthropic", None, "m", env={"LLM_API_KEY": "k"})
    assert llm.chat("p", cfg) == "ab"
    assert seen[0][0] == "https://api.anthropic.com/v1/messages" and seen[0][2]["X-api-key"] == "k"


def test_unreachable_and_missing_model_are_readable(monkeypatch):
    fake(monkeypatch, [urllib.error.URLError("refused")])
    with pytest.raises(llm.LLMError, match="could not reach"):
        llm.chat("p", llm.settings("ollama", "http://h", "m", env={}))
    with pytest.raises(llm.LLMError, match="no model"):
        llm.chat("p", llm.settings("ollama", "http://h", "", env={}))
