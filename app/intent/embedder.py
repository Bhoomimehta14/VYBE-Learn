"""Frozen pretrained text encoder - the 'borrowed knowledge' in transfer learning.

The encoder is never trained here. It turns a sentence into a 384-number
vector where sentences with similar meaning land close together. Everything
we train sits on top of these vectors. Returns None if fastembed or the model
files are unavailable so callers can degrade instead of crashing.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

import numpy as np

MODEL_NAME = "BAAI/bge-small-en-v1.5"
CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "models" / "fastembed_cache"

_model = None
_failed = False
_lock = threading.Lock()


def _load():
    global _model, _failed
    if _model is not None or _failed:
        return _model
    with _lock:
        if _model is not None or _failed:
            return _model
        try:
            os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
            from fastembed import TextEmbedding

            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            _model = TextEmbedding(MODEL_NAME, cache_dir=str(CACHE_DIR))
        except Exception as exc:  # noqa: BLE001 - any failure means "no encoder"
            print(f"[intent] embedding model unavailable, intent detection off: {exc}")
            _failed = True
    return _model


def embed(texts: list[str]) -> np.ndarray | None:
    model = _load()
    if model is None:
        return None
    return np.array(list(model.embed(texts)))
