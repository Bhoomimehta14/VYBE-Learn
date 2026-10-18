"""Intent detection (transfer learning head). Uses the real saved head and
encoder; skipped if they aren't available on this machine."""

import pytest

from app.intent import embedder, model
from web import chat as chatbot

pytestmark = pytest.mark.skipif(
    not model.HEAD_PATH.exists() or embedder.embed(["x"]) is None,
    reason="intent head or embedding model not available",
)

# Phrasings that are NOT in app/intent/examples.py.
CASES = [
    ("could you drop me a tiny clue about this column", "hint_request"),
    ("ugh nothing here makes sense and i am about to quit", "stuck_frustrated"),
    ("show me one worked example with a few numbers", "example_request"),
    ("who is the best cricket player ever", "off_topic"),
    ("why did the agent say my pick was wrong", "why_wrong"),
]


@pytest.mark.parametrize("text,expected", CASES)
def test_predicts_intent_on_unseen_phrasing(text, expected):
    result = model.predict_intent(text)
    assert result is not None and result["intent"] == expected


def test_empty_message_returns_none():
    assert model.predict_intent("   ") is None


def test_unsure_input_returns_none():
    assert model.predict_intent("zxqv blorp wug") is None


def test_chat_still_works_when_encoder_is_missing(monkeypatch):
    monkeypatch.setattr(model, "_head", None)
    monkeypatch.setattr(model, "HEAD_PATH", model.HEAD_PATH.with_name("does_not_exist.joblib"))
    assert chatbot.detect_intent("give me a hint") is None
    assert "reply" in chatbot.ask("give me a hint", "", session_id=None)


def test_offline_fallback_is_intent_aware():
    reply = chatbot._fallback("hmm", None, {"intent": "stuck_frustrated", "confidence": 0.9})
    assert "normal" in reply
