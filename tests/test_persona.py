"""Learner level and persona: unit tests for web/persona.py, plus checks that
the mentor and chat actually carry them into what the model is sent."""

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

from web import chat as chatbot
from web import persona
from web.api import app

client = TestClient(app)


# ------------------------------------------------------------ experience

@pytest.mark.parametrize("text,band", [
    ("New to this", "new"),
    ("Know the basics", "basics"),
    ("Pretty confident", "confident"),
    ("beginner", "new"),
    ("advanced", "confident"),
    ("", None),
    (None, None),
    ("banana", None),
])
def test_experience_band(text, band):
    assert persona.experience_band(text) == band


# ------------------------------------------------------------ learner level

def test_new_learner_with_no_evidence_gets_the_most_support():
    assert persona.learner_level(experience="New to this")["mode"] == "guided"


def test_confident_learner_gets_the_least_support():
    assert persona.learner_level(experience="Pretty confident")["mode"] == "independent"


def test_nothing_known_uses_a_middle_setting():
    assert persona.learner_level()["mode"] == "assisted"


def test_zero_mastery_is_no_evidence_not_knowing_nothing():
    zero = persona.learner_level(experience="Pretty confident", mastery_level=0)
    assert zero["mode"] == "independent"


def test_real_mastery_outweighs_what_they_told_us():
    # Said "confident" but is failing: the evidence wins once there are attempts.
    level = persona.learner_level(experience="Pretty confident", mastery_level=10, attempt_count=3)
    assert level["mode"] == "guided"
    # Said "new" but is doing well.
    level = persona.learner_level(experience="New to this", mastery_level=90, attempt_count=3)
    assert level["mode"] == "independent"


def test_many_hints_make_it_more_supportive():
    easy = persona.learner_level(experience="Know the basics")
    struggling = persona.learner_level(experience="Know the basics", hints_used=4)
    assert persona.MODES.index(struggling["mode"]) < persona.MODES.index(easy["mode"])


def test_a_frustrated_message_makes_this_reply_gentler():
    calm = persona.learner_level(experience="Know the basics")
    upset = persona.learner_level(
        experience="Know the basics", intent={"intent": "stuck_frustrated", "confidence": 0.9}
    )
    assert persona.MODES.index(upset["mode"]) < persona.MODES.index(calm["mode"])


def test_never_gives_less_help_than_the_learner_chose():
    level = persona.learner_level(experience="Pretty confident", requested_mode="guided")
    assert level["mode"] == "guided"


def test_can_give_more_help_than_the_ui_asked_for():
    level = persona.learner_level(experience="New to this", requested_mode="independent")
    assert level["mode"] == "guided"


def test_level_always_explains_itself():
    assert persona.learner_level(experience="New to this")["reason"]
    assert persona.learner_level()["reason"]


# ------------------------------------------------------------ persona block

def test_each_known_role_gets_its_own_examples():
    blocks = {r: persona.persona_block(r, "New to this", "Get better at my job") for r in ("Sales", "Operations", "HR", "Student")}
    assert "deals" in blocks["Sales"].lower()
    assert "inventory" in blocks["Operations"].lower()
    assert "attrition" in blocks["HR"].lower()
    assert "exam" in blocks["Student"].lower()
    assert len(set(blocks.values())) == 4


def test_custom_role_is_used_without_inventing_specifics():
    block = persona.persona_block("Chef", None, None)
    assert "Chef" in block and "not sure of an example" in block


def test_experience_changes_the_depth():
    new = persona.persona_block("Sales", "New to this", None)
    pro = persona.persona_block("Sales", "Pretty confident", None)
    assert "jargon" in new and "jargon" not in pro
    assert "brief" in pro


def test_goal_changes_the_framing():
    job = persona.persona_block(None, None, "Get better at my job")
    school = persona.persona_block(None, None, "Coursework or school")
    assert job != school and "job" in job and "terminology" in school


def test_no_information_adds_nothing():
    assert persona.persona_block(None, None, None) == ""
    assert persona.persona_block("", "", "") == ""


# ------------------------------------------------------------ reaches the model

@pytest.fixture
def captured(monkeypatch):
    """Replaces the direct-Gemini call with one that records what it was sent."""
    seen = {}

    def fake_call_llm(system, prompt, max_tokens=300):
        seen["system"], seen["prompt"] = system, prompt
        return "a live answer"

    monkeypatch.setitem(sys.modules, "llm_client", types.SimpleNamespace(call_llm=fake_call_llm))
    monkeypatch.setattr(chatbot, "ask_adk", lambda *a, **k: None)
    return seen


def _session(role, experience, goal="Get better at my job"):
    sid = client.post("/api/session", json={"role": role, "experience": experience, "goal": goal}).json()["session_id"]
    return {"X-Session-Id": sid}


def test_mentor_tailors_to_the_session_profile(captured):
    headers = _session("Sales", "New to this")
    body = client.post("/api/mentor", headers=headers, json={
        "user_message": "what is skew", "learning_mode": "independent",
    }).json()
    assert body["grounded"] is True
    assert "deals" in captured["system"].lower()  # sales examples
    assert "jargon" in captured["system"]  # beginner depth
    assert body["mode"] == "guided"  # beginner gets more support than the UI asked for
    assert body["level"]["band"] == "new"


def test_same_question_is_answered_differently_for_different_learners(captured):
    question = {"user_message": "what is an outlier"}  # no mode picked, so the server decides

    client.post("/api/mentor", headers=_session("Sales", "New to this"), json=question)
    beginner_sales = dict(captured)
    client.post("/api/mentor", headers=_session("Operations", "Pretty confident"), json=question)
    expert_ops = dict(captured)

    assert beginner_sales["system"] != expert_ops["system"]
    assert "deals" in beginner_sales["system"].lower() and "deals" not in expert_ops["system"].lower()
    assert "inventory" in expert_ops["system"].lower()
    assert "brief" in expert_ops["system"]
    assert "very simple language" in beginner_sales["system"]  # guided mode text
    assert "justify" in expert_ops["system"]  # independent mode text


def test_frustrated_message_softens_the_mentor_for_a_confident_learner(captured):
    headers = _session("Operations", "Pretty confident")
    calm = client.post("/api/mentor", headers=headers, json={"user_message": "what is an outlier"}).json()
    upset = client.post("/api/mentor", headers=headers, json={
        "user_message": "i am so lost and frustrated, nothing makes sense and i give up",
    }).json()
    assert persona.MODES.index(upset["mode"]) < persona.MODES.index(calm["mode"])
    assert upset["intent"]["intent"] == "stuck_frustrated"


def test_mentor_still_works_with_no_profile(captured):
    sid = client.post("/api/session", json={}).json()["session_id"]
    body = client.post("/api/mentor", headers={"X-Session-Id": sid}, json={"user_message": "what is skew"}).json()
    assert body["grounded"] is True
    assert "How to tailor" not in captured["system"]


def test_mentor_fallback_still_honest_without_a_model(monkeypatch):
    monkeypatch.setitem(sys.modules, "llm_client", types.SimpleNamespace(call_llm=lambda *a, **k: None))
    monkeypatch.setattr(chatbot, "ask_adk", lambda *a, **k: None)
    body = client.post("/api/mentor", headers=_session("Sales", "New to this"), json={"user_message": "zzz"}).json()
    assert body["grounded"] is False and body["reply"]


def test_chat_context_carries_the_persona(captured):
    headers = _session("HR", "Know the basics", "Coursework or school")
    client.post("/api/chat", headers=headers, json={"message": "what is a missing value"})
    assert "attrition" in captured["prompt"].lower()
    assert "terminology" in captured["prompt"]
