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


def test_heldout_accuracy_and_no_confident_wrong_labels():
    from app.intent.heldout import HELDOUT

    total = correct = wrong = 0
    for intent, rows in HELDOUT.items():
        for text in rows:
            total += 1
            result = model.predict_intent(text)
            if result is None:
                continue  # abstaining is acceptable; guessing wrong is not
            if result["intent"] == intent:
                correct += 1
            else:
                wrong += 1
    assert wrong == 0, f"{wrong} held-out messages got a confident wrong label"
    assert correct / total >= 0.90, f"held-out accuracy {correct}/{total}"


def test_heldout_set_is_not_in_training_data():
    from app.intent.examples import EXAMPLES
    from app.intent.heldout import HELDOUT

    train = {t.lower() for rows in EXAMPLES.values() for t in rows}
    leaked = [t for rows in HELDOUT.values() for t in rows if t.lower() in train]
    assert not leaked, f"held-out rows leaked into training: {leaked}"


def test_empty_message_returns_none():
    assert model.predict_intent("   ") is None


@pytest.mark.parametrize("text", ["asdf qwerty", "hmm", "???"])
def test_unsure_input_returns_none(text):
    # Known limit: some nonsense words ("la la la", "lorem ipsum") still land on
    # off_topic with moderate confidence. Raising the threshold to catch them
    # costs correct answers on the held-out set, so we don't.
    assert model.predict_intent(text) is None


def test_chat_still_works_when_encoder_is_missing(monkeypatch):
    monkeypatch.setattr(model, "_head", None)
    monkeypatch.setattr(model, "HEAD_PATH", model.HEAD_PATH.with_name("does_not_exist.joblib"))
    assert chatbot.detect_intent("give me a hint") is None
    assert "reply" in chatbot.ask("give me a hint", "", session_id=None)


def test_offline_fallback_is_intent_aware():
    reply = chatbot._fallback("hmm", None, {"intent": "stuck_frustrated", "confidence": 0.9})
    assert "normal" in reply
