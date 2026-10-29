"""
Low-level LLM call wrapper -- GEMINI VERSION.

Same shape as the original llm_client.py (Anthropic version), same
retry/cache/fallback guarantees. narrate_llm.py doesn't need to change
at all -- it calls call_llm(system, user, max_tokens) either way, and
gets back a string or None. Swapping providers is exactly as contained
as the comment in the original file promised.

Uses Google's free tier (gemini-2.5-flash) -- no credit card, no
expiration, roughly 250 requests/day on the free tier as of writing.
More than enough for a hackathon demo (narration runs a handful of
times total, not per end-user request).

Setup:
    pip install google-genai
    Get a free key at https://aistudio.google.com/apikey (no card needed)
    Put it in .env as GEMINI_API_KEY=...  (NOT ANTHROPIC_API_KEY)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time

from google import genai

MODEL = "gemini-3.6-flash"  # gemini-2.5-flash was deprecated for new users;
                             # this is Google's own replacement as confirmed
                             # by a live 404 error message from the API itself
TIMEOUT_SECONDS = 8.0
MAX_RETRIES = 2
_THINKING_OFF = True

_client: "genai.Client | None" = None
_cache: dict[str, str] = {}

# Errors that retrying cannot fix. After one of these every caller would otherwise
# wait several seconds per call just to be told the same thing, so we remember it
# for a while and let the deterministic fallback answer immediately.
_NOT_RETRYABLE = {401: "key", 402: "billing", 403: "key", 404: "model", 429: "quota"}
_MAX_BLOCK_SECONDS = 900  # re-test at least every 15 minutes in case it recovered
_blocked_until = 0.0
_blocked_reason: str | None = None


def _error_code(e: Exception) -> int | None:
    code = getattr(e, "code", None)
    if isinstance(code, int):
        return code
    m = re.match(r"\s*(\d{3})(?!\d)", str(e))
    return int(m.group(1)) if m else None


def _block_for(e: Exception, reason: str) -> float:
    """How long to stay off the API: Google's own retry hint when it gives one, capped."""
    m = re.search(r"retryDelay'?\W+(\d+(?:\.\d+)?)s", str(e))
    seconds = float(m.group(1)) if m else 600.0
    return max(30.0, min(seconds, _MAX_BLOCK_SECONDS))


def llm_status() -> dict:
    """Whether live answers are available right now, and if not, why (quota, billing, key, model)."""
    if not os.environ.get("GEMINI_API_KEY"):
        return {"available": False, "reason": "no_key", "retry_in_seconds": 0}
    remaining = _blocked_until - time.time()
    if remaining > 0:
        return {"available": False, "reason": _blocked_reason, "retry_in_seconds": int(remaining)}
    return {"available": True, "reason": None, "retry_in_seconds": 0}


def _get_client() -> "genai.Client":
    global _client
    if _client is None:
        # genai.Client() reads GEMINI_API_KEY from the environment automatically,
        # same pattern as the Anthropic client reading ANTHROPIC_API_KEY.
        _client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    return _client


def _cache_key(system: str, user: str) -> str:
    payload = json.dumps({"system": system, "user": user}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def call_llm(system: str, user: str, max_tokens: int = 100) -> str | None:
    """
    Returns the model's text response, or None if every attempt failed --
    or if no API key is set at all. Same contract as the Anthropic version:
    a None return here is what triggers narrate_llm.py's fallback to the
    deterministic template text, so the demo never breaks on an API hiccup.
    """
    global _blocked_until, _blocked_reason, _THINKING_OFF
    if not os.environ.get("GEMINI_API_KEY"):
        return None

    key = _cache_key(system, user)
    if key in _cache:
        return _cache[key]

    if time.time() < _blocked_until:
        return None  # a known, non-recoverable failure was seen recently: answer instantly with the fallback

    client = _get_client()
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=user,
                config={
                    # Short explanations don't need the model to "think" first: switching it off
                    # roughly halves the wait (about 4.8s -> 2.3s measured). Dropped automatically
                    # if a model ever rejects the setting.
                    **({"thinking_config": {"thinking_budget": 0}} if _THINKING_OFF else {}),
                    "system_instruction": system,
                    # Fragments/truncation were observed with a low ceiling
                    # (e.g. 80 tokens) -- newer Gemini models appear to
                    # consume part of the budget before the visible answer.
                    # Raising this substantially is the safe, verifiable fix;
                    # an untested "thinking_config" parameter was considered
                    # but dropped since it can't be verified from this
                    # environment (no live API access) and risks a new
                    # failure mode if the field name/shape is wrong for
                    # this model.
                    "max_output_tokens": max(max_tokens, 900),
                },
            )
            text = response.text.strip()
            if not text:
                raise ValueError("empty response text -- treating as a failure to trigger fallback")
            _cache[key] = text
            return text
        except Exception as e:  # noqa: BLE001 -- any failure -> fallback, never crash the demo
            last_error = e
            code = _error_code(e)
            if _THINKING_OFF and "thinking" in str(e).lower():
                _THINKING_OFF = False  # this model doesn't accept it: retry without
                continue
            if code in _NOT_RETRYABLE:
                _blocked_reason = _NOT_RETRYABLE[code]
                _blocked_until = time.time() + _block_for(e, _blocked_reason)
                break
            if attempt < MAX_RETRIES:
                time.sleep(0.5 * (2 ** attempt))

    print(f"[llm_client_gemini] giving up: {str(last_error)[:200]}")
    return None
