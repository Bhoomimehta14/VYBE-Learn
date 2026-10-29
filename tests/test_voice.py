"""The mentor's small talk and role voice: greetings get an answer, off-topic gets a friendly one."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app" / "educator"))
os.environ.setdefault("ADK_BASE_URL", "http://127.0.0.1:1")

import pytest

from web import chat, persona


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    import types

    monkeypatch.setitem(sys.modules, "llm_client", types.SimpleNamespace(call_llm=lambda *a, **k: None))
    monkeypatch.setattr(chat, "ask_adk", lambda *a, **k: None)


def ask(message, role):
    return chat.mentor_ask({"user_message": message, "learner": {"role": role, "experience": "new to this"}})


@pytest.mark.parametrize("text", ["hi", "Hello!", "hey there", "good morning", "yo", "HELLO"])
def test_greetings_are_recognised_and_answered(text):
    assert chat.detect_smalltalk(text) == "greeting"
    out = ask(text, "student")
    assert out["intent"]["intent"] == "smalltalk"
    assert out["reply"] and "lesson" in out["reply"].lower()


@pytest.mark.parametrize(
    "text,kind",
    [("how are you?", "how_are_you"), ("thanks!", "thanks"), ("thank you", "thanks"), ("bye", "bye"), ("ok cool", None), ("cool", "ack")],
)
def test_other_small_talk_kinds(text, kind):
    assert chat.detect_smalltalk(text) == kind


@pytest.mark.parametrize("text", ["hi can you explain missing values", "what is a histogram", "hello, why was my answer wrong"])
def test_a_real_question_that_starts_with_hi_is_not_small_talk(text):
    assert chat.detect_smalltalk(text) is None


def test_replies_sound_like_the_learner_s_role():
    student = ask("hi", "student")["reply"]
    sales = ask("hi", "sales")["reply"]
    assert student != sales
    assert "numbers" in sales.lower()


def test_off_topic_echoes_what_they_asked_for_and_steers_back():
    reply = ask("get me a pizza", "student")["reply"].lower()
    assert "pizza" in reply and "lesson" in reply
    assert "syllabus" in reply  # student's own words
    sales = ask("get me a pizza", "sales")["reply"].lower()
    assert "pizza" in sales and "quota" in sales


def test_off_topic_with_no_clear_ask_is_still_a_real_reply():
    reply = ask("who won the cricket match yesterday?", "student")["reply"]
    assert len(reply) > 40 and "lesson" in reply.lower()


def test_an_unknown_role_gets_a_friendly_generic_voice():
    reply = ask("get me a pizza", "teacher")["reply"].lower()
    assert "pizza" in reply and "lesson" in reply


@pytest.mark.parametrize("text,thing", [("get me a pizza", "a pizza"), ("Can you order me a coffee?", "a coffee"), ("i want ice cream", "ice cream"), ("i want to learn pandas", None)])
def test_the_thing_they_asked_for_is_picked_out(text, thing):
    assert chat._wanted_thing(text) == thing


def test_the_llm_prompt_carries_the_role_tone_and_the_smalltalk_guidance(monkeypatch):
    import types

    seen = {}

    def fake(system, prompt, max_tokens=300):
        seen["system"], seen["prompt"] = system, prompt
        return "live"

    monkeypatch.setitem(sys.modules, "llm_client", types.SimpleNamespace(call_llm=fake))
    out = ask("hello", "student")
    assert out["grounded"] and "study buddy" in seen["system"]
    assert "friendly" in seen["prompt"]
    ask("get me a pizza", "sales")
    assert "sales floor" in seen["system"] and "Acknowledge what they actually said" in seen["prompt"]


def test_every_known_role_has_a_tone_and_an_offline_voice():
    for role in ("sales", "operations", "hr", "student"):
        assert "Tone:" in persona.persona_block(role, None, None)
        assert persona.smalltalk_reply("greeting", role)
        assert "{want}" not in persona.offtopic_reply("a pizza", role)
