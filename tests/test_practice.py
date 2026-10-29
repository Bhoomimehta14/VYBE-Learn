"""Flashcards and quizzes after cleaning (EDA, ML foundations, modeling), and the upload speed-ups."""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app" / "educator"))
os.environ.setdefault("ADK_BASE_URL", "http://127.0.0.1:1")

import pytest
from fastapi.testclient import TestClient

from web.api import app

client = TestClient(app)


@pytest.fixture()
def headers():
    sid = client.post("/api/session", json={"role": "business owner", "experience": "new to this"}).json()["session_id"]
    h = {"X-Session-Id": sid}
    assert client.post("/api/dataset", data={"use_sample": "true"}, headers=h).status_code == 200
    return h


@pytest.mark.parametrize("stage", ["eda", "foundations", "model"])
def test_every_later_stage_has_flashcards(headers, stage):
    cards = client.get(f"/api/practice/{stage}/cards", headers=headers).json()["cards"]
    assert len(cards) >= 4
    assert all(c["front"] and c["back"] for c in cards)


@pytest.mark.parametrize("stage", ["eda", "foundations"])
def test_quiz_is_graded_and_scored_once(headers, stage):
    qs = client.get(f"/api/practice/{stage}/quiz", headers=headers).json()["questions"]
    assert qs and all(len(q["options"]) >= 2 for q in qs)
    first = client.post(f"/api/practice/{stage}/quiz", json={"answers": {q["id"]: q["options"][0] for q in qs}}, headers=headers).json()
    assert set(first["results"]) == {q["id"] for q in qs}
    assert all(a in q["options"] for q, a in zip(qs, first["correct_answers"].values()))
    again = client.post(f"/api/practice/{stage}/quiz", json={"answers": {q["id"]: "nope" for q in qs}}, headers=headers).json()
    assert again["points_awarded"] == first["points_awarded"], "a second submit must not change the score"


def test_unknown_stage_is_a_404(headers):
    assert client.get("/api/practice/nonsense/cards", headers=headers).status_code == 404
    assert client.get("/api/practice/model/quiz", headers=headers).status_code == 404


def test_the_eda_question_uses_the_learners_own_data(headers):
    qs = client.get("/api/practice/eda/quiz", headers=headers).json()["questions"]
    ids = {q["id"] for q in qs}
    assert "eda_histogram" in ids and "eda_top_group" in ids


def test_results_can_skip_the_written_summary_and_fetch_it_separately(headers):
    quick = client.get("/api/results?lesson=false", headers=headers).json()
    assert "lesson" not in quick and "model" in quick
    assert "## " in client.get("/api/results/lesson", headers=headers).json()["lesson"]


def test_upload_does_not_wait_for_model_selection(monkeypatch):
    """The slow step (cross-validated forests) runs in the background after upload."""
    from web import pipeline

    started = {}
    real = pipeline._run_model

    def slow(*a, **k):
        started["t"] = time.time()
        time.sleep(1.5)
        return real(*a, **k)

    monkeypatch.setattr(pipeline, "_run_model", slow)
    sid = client.post("/api/session", json={"role": "x", "experience": "new to this"}).json()["session_id"]
    t0 = time.time()
    assert client.post("/api/dataset", data={"use_sample": "true"}, headers={"X-Session-Id": sid}).status_code == 200
    assert time.time() - t0 < 1.4, "the upload waited for model selection"
    # and asking for it still works once it is done
    assert client.get("/api/model", headers={"X-Session-Id": sid}).json()["available"] in (True, False)


def test_the_model_is_only_computed_once(monkeypatch):
    from web import pipeline

    calls = []
    real = pipeline._run_model
    monkeypatch.setattr(pipeline, "_run_model", lambda *a, **k: (calls.append(1), real(*a, **k))[1])
    sid = client.post("/api/session", json={}).json()["session_id"]
    h = {"X-Session-Id": sid}
    client.post("/api/dataset", data={"use_sample": "true"}, headers=h)
    for _ in range(3):
        client.get("/api/model", headers=h)
    assert len(calls) == 1
