"""Loading a dataset must be quick and must not spend model calls. The plain-language
lesson summary is only needed on the final page, and a model that cannot recover
(out of quota, bad key) must not make every request wait."""

import os
import sys
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app" / "educator"))
os.environ.setdefault("ADK_BASE_URL", "http://127.0.0.1:1")

import pytest
from fastapi.testclient import TestClient

import llm_client
from web.api import app

client = TestClient(app)


def _session():
    sid = client.post("/api/session", json={"role": "Sales", "experience": "New to this"}).json()["session_id"]
    return {"X-Session-Id": sid}


@pytest.fixture
def counted_model(monkeypatch):
    """A working model that records every call, with a key set so narration is attempted."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    calls = []

    def fake(system, prompt, max_tokens=100):
        calls.append(prompt[:40])
        return "a narrated sentence"

    # narrate_llm does `from llm_client import call_llm`, so patch the module attribute it reads.
    import narrate_llm

    monkeypatch.setattr(narrate_llm, "call_llm", fake)
    return calls


# ---------------------------------------------------------------- dataset load

def test_loading_the_sample_dataset_makes_no_model_calls(counted_model):
    started = time.time()
    r = client.post("/api/dataset", headers=_session(), data={"use_sample": "true"})
    assert r.status_code == 200
    assert counted_model == [], f"dataset load called the model {len(counted_model)} times"
    assert time.time() - started < 5


def test_the_lesson_is_written_once_when_results_are_asked_for(counted_model):
    headers = _session()
    client.post("/api/dataset", headers=headers, data={"use_sample": "true"})
    first = client.get("/api/results", headers=headers).json()
    calls_after_first = len(counted_model)
    assert calls_after_first > 0
    assert "narrated sentence" in first["lesson"]
    client.get("/api/results", headers=headers)
    assert len(counted_model) == calls_after_first, "the lesson was rewritten on a second request"


def test_lesson_keeps_its_order_when_narrated_in_parallel(counted_model):
    from narrate_llm import generate_lesson
    from fake_data import FAKE_ACTION_LOG, FAKE_MODEL_LOG

    lines = generate_lesson(FAKE_ACTION_LOG, FAKE_MODEL_LOG).splitlines()
    heads = [i for i, l in enumerate(lines) if l.startswith("##")]
    assert lines[heads[0]] == "## What happened to your data"
    assert lines[heads[1]] == "## Model selection"
    assert len(lines) == 1 + len(FAKE_ACTION_LOG) + 2 + len(FAKE_MODEL_LOG)


# ---------------------------------------------------------------- unrecoverable errors

class _ApiError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


@pytest.fixture
def fresh_breaker(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(llm_client, "_blocked_until", 0.0)
    monkeypatch.setattr(llm_client, "_blocked_reason", None)
    monkeypatch.setattr(llm_client, "_cache", {})
    monkeypatch.setattr(llm_client.time, "sleep", lambda s: None)


def _client_that_fails(monkeypatch, error):
    calls = {"n": 0}

    def generate_content(**kwargs):
        calls["n"] += 1
        raise error

    fake = types.SimpleNamespace(models=types.SimpleNamespace(generate_content=generate_content))
    monkeypatch.setattr(llm_client, "_get_client", lambda: fake)
    return calls


def test_quota_error_is_not_retried_and_blocks_later_calls(fresh_breaker, monkeypatch):
    calls = _client_that_fails(
        monkeypatch, _ApiError(429, "429 RESOURCE_EXHAUSTED {'retryDelay': '72058s'}")
    )
    assert llm_client.call_llm("s", "first") is None
    assert calls["n"] == 1, "a quota error was retried"
    assert llm_client.call_llm("s", "second") is None
    assert calls["n"] == 1, "a call went out while the model was known to be unavailable"
    status = llm_client.llm_status()
    assert status["available"] is False and status["reason"] == "quota"
    assert 0 < status["retry_in_seconds"] <= 900


@pytest.mark.parametrize("code,reason", [(402, "billing"), (403, "key"), (401, "key"), (404, "model")])
def test_other_unrecoverable_errors_are_named(fresh_breaker, monkeypatch, code, reason):
    calls = _client_that_fails(monkeypatch, _ApiError(code, f"{code} problem"))
    assert llm_client.call_llm("s", "x") is None
    assert calls["n"] == 1
    assert llm_client.llm_status()["reason"] == reason


def test_a_temporary_error_is_still_retried_and_does_not_block(fresh_breaker, monkeypatch):
    calls = _client_that_fails(monkeypatch, _ApiError(503, "503 unavailable"))
    assert llm_client.call_llm("s", "x") is None
    assert calls["n"] == llm_client.MAX_RETRIES + 1
    assert llm_client.llm_status()["available"] is True


def test_the_block_ends_so_a_recovered_model_is_used_again(fresh_breaker, monkeypatch):
    _client_that_fails(monkeypatch, _ApiError(429, "429 quota"))
    llm_client.call_llm("s", "x")
    monkeypatch.setattr(llm_client, "_blocked_until", time.time() - 1)
    assert llm_client.llm_status()["available"] is True


def test_no_key_reports_why(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    status = llm_client.llm_status()
    assert status["available"] is False and status["reason"] == "no_key"


def test_health_says_whether_live_answers_work_and_why_not(fresh_breaker, monkeypatch):
    _client_that_fails(monkeypatch, _ApiError(429, "429 quota"))
    llm_client.call_llm("s", "x")
    body = client.get("/api/health").json()
    assert body["ok"] is True
    assert body["llm_available"] is False and body["llm_issue"] == "quota"
