"""Off-topic and random questions on every tier (ADK, direct Gemini, offline).
The learner should never hit a dead end or a stiff refusal."""

import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app" / "educator"))
os.environ.setdefault("ADK_BASE_URL", "http://127.0.0.1:1")

import pytest
from fastapi.testclient import TestClient

from app.intent import model
from app.intent.heldout import HELDOUT
from web import chat as chatbot
from web.api import app

client = TestClient(app)
OFF_TOPIC = HELDOUT["off_topic"]
REDIRECT = chatbot.INTENT_FALLBACK["off_topic"]


def _headers():
    sid = client.post("/api/session", json={"role": "Sales", "experience": "New to this"}).json()["session_id"]
    return {"X-Session-Id": sid}


@pytest.fixture
def offline(monkeypatch):
    """No ADK and no model: only the deterministic tier is left."""
    monkeypatch.setitem(sys.modules, "llm_client", types.SimpleNamespace(call_llm=lambda *a, **k: None))
    monkeypatch.setattr(chatbot, "ask_adk", lambda *a, **k: None)


@pytest.fixture
def direct(monkeypatch):
    """No ADK; the direct-Gemini call records what it was sent."""
    seen = {}

    def fake(system, prompt, max_tokens=300):
        seen["system"], seen["prompt"] = system, prompt
        return "a live answer"

    monkeypatch.setitem(sys.modules, "llm_client", types.SimpleNamespace(call_llm=fake))
    monkeypatch.setattr(chatbot, "ask_adk", lambda *a, **k: None)
    return seen


# ---------------------------------------------------------------- offline tier

@pytest.mark.parametrize("question", OFF_TOPIC)
def test_chat_offline_redirects_politely(offline, question):
    body = client.post("/api/chat", headers=_headers(), json={"message": question}).json()
    assert body["grounded"] is False
    assert body["reply"] == REDIRECT


@pytest.mark.parametrize("question", OFF_TOPIC)
def test_mentor_offline_redirects_politely(offline, question):
    body = client.post("/api/mentor", headers=_headers(), json={"user_message": question}).json()
    assert body["grounded"] is False
    reply = body["reply"].lower()
    assert "lesson" in reply or "step" in reply, "it should steer back to the lesson"
    assert "don't have" not in reply


def test_offline_redirect_is_not_a_dead_end():
    assert "lesson" in REDIRECT and "?" not in REDIRECT
    assert "don't have" not in REDIRECT.lower()


def test_offline_with_no_encoder_still_replies(offline, monkeypatch):
    monkeypatch.setattr(model, "_head", None)
    monkeypatch.setattr(model, "HEAD_PATH", model.HEAD_PATH.with_name("does_not_exist.joblib"))
    for path, body in (("/api/chat", {"message": OFF_TOPIC[0]}), ("/api/mentor", {"user_message": OFF_TOPIC[0]})):
        reply = client.post(path, headers=_headers(), json=body).json()["reply"]
        assert reply and isinstance(reply, str)


def test_lesson_question_is_not_treated_as_off_topic(offline):
    body = client.post("/api/mentor", headers=_headers(), json={"user_message": "what is skew"}).json()
    assert body["reply"] != REDIRECT  # the FAQ answers it instead


# ---------------------------------------------------------------- direct Gemini tier

@pytest.mark.parametrize("path,key", [("/api/chat", "message"), ("/api/mentor", "user_message")])
def test_direct_tier_is_told_to_answer_briefly_and_steer_back(direct, path, key):
    client.post(path, headers=_headers(), json={key: OFF_TOPIC[0]})
    assert "do not refuse" in direct["system"] and "stiffly" in direct["system"]


@pytest.mark.parametrize("path,key", [("/api/chat", "message"), ("/api/mentor", "user_message")])
def test_detected_off_topic_adds_the_steer_back_nudge(direct, path, key):
    client.post(path, headers=_headers(), json={key: OFF_TOPIC[0]})
    assert "unrelated to the lesson" in direct["prompt"]


def test_an_unrecognised_random_question_still_reaches_the_model(direct):
    body = client.post("/api/mentor", headers=_headers(), json={"user_message": "zzz qqq xx"}).json()
    assert body["grounded"] is True


# ---------------------------------------------------------------- ADK tier

def test_adk_tier_gets_the_steer_back_nudge(monkeypatch):
    seen = {}

    def fake_adk(prompt, session_id):
        seen["prompt"] = prompt
        return {"reply": "adk answer"}

    monkeypatch.setattr(chatbot, "ask_adk", fake_adk)
    for path, key in (("/api/chat", "message"), ("/api/mentor", "user_message")):
        body = client.post(path, headers=_headers(), json={key: OFF_TOPIC[0]}).json()
        assert body["reply"] == "adk answer" and body["grounded"] is True
        assert "unrelated to the lesson" in seen["prompt"]
