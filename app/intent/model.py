"""Small trained classifier head on top of the frozen encoder (the transfer step)."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

from app.intent import embedder
from app.intent.examples import EXAMPLES

HEAD_PATH = Path(__file__).resolve().parents[2] / "data" / "models" / "intent_head.joblib"
MIN_CONFIDENCE = 0.45  # below this we say "not sure" rather than guess

_head = None


def dataset() -> tuple[list[str], list[str]]:
    texts, labels = [], []
    for intent, rows in EXAMPLES.items():
        texts.extend(rows)
        labels.extend([intent] * len(rows))
    return texts, labels


def new_head() -> LogisticRegression:
    return LogisticRegression(C=10.0, max_iter=2000)


def train_and_save() -> LogisticRegression:
    texts, labels = dataset()
    X = embedder.embed(texts)
    if X is None:
        raise RuntimeError("embedding model unavailable - cannot train")
    head = new_head().fit(X, labels)
    HEAD_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(head, HEAD_PATH)
    return head


def _load_head():
    global _head
    if _head is None and HEAD_PATH.exists():
        _head = joblib.load(HEAD_PATH)
    return _head


def predict_intent(text: str) -> dict | None:
    """Returns {"intent", "confidence"} or None if there is no trained head,
    no encoder, an empty message, or the model is not confident enough."""
    text = (text or "").strip()
    head = _load_head()
    if not text or head is None:
        return None
    X = embedder.embed([text])
    if X is None:
        return None
    probs = head.predict_proba(X)[0]
    i = int(np.argmax(probs))
    confidence = float(probs[i])
    if confidence < MIN_CONFIDENCE:
        return None
    return {"intent": str(head.classes_[i]), "confidence": round(confidence, 3)}
