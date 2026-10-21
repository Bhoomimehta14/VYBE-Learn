"""Learner level and persona for the mentor and chat.

Two small, deterministic pieces (no model call, so they are cheap and testable):

* learner_level(): how much support this learner needs right now.
* persona_block(): who they are (role, experience, goal) turned into guidance
  the LLM can act on - which examples to reach for, how deep to go, how to
  frame the "why".

The detected intent (app/intent) is one input to the level: a frustrated
message makes the mentor gentler for that reply.
"""

from __future__ import annotations

MODES = ("guided", "assisted", "independent")  # most to least support

# What we assume about mastery before the learner has shown us any.
_EXPERIENCE_PRIOR = {"new": 20, "basics": 50, "confident": 75}


def experience_band(experience: str | None) -> str | None:
    """Maps the onboarding answer (or free text the ADK profiler produced)
    to new | basics | confident. None if we have nothing to go on."""
    text = (experience or "").strip().lower()
    if not text:
        return None
    if any(k in text for k in ("new", "beginner", "never", "none", "no experience", "just start")):
        return "new"
    if any(k in text for k in ("confident", "advanced", "expert", "experienced", "comfortable", "senior")):
        return "confident"
    if any(k in text for k in ("basic", "some", "intermediate", "little", "familiar")):
        return "basics"
    return None


def learner_level(
    experience: str | None = None,
    mastery_level: int | None = None,
    attempt_count: int = 0,
    hints_used: int = 0,
    intent: dict | None = None,
    requested_mode: str | None = None,
) -> dict:
    """Returns {"band", "score", "mode", "reason"}.

    score (0-100) starts from what the learner told us (experience) and moves
    toward what they have actually shown (mastery) once there is evidence.
    The mode is the more supportive of what the UI asked for and what this
    says - the mentor never gives less help than the learner already chose.
    """
    band = experience_band(experience)
    prior = _EXPERIENCE_PRIOR.get(band, 50)
    reasons: list[str] = []

    score = float(prior)
    if mastery_level:  # 0 means "no evidence yet", not "knows nothing"
        evidence = min(1.0, 0.4 + 0.15 * max(attempt_count, 0))
        score = (1 - evidence) * prior + evidence * float(mastery_level)
        reasons.append(f"mastery {mastery_level}")
    elif band:
        reasons.append(f"told us: {band}")

    if hints_used >= 3 or attempt_count >= 4:
        score -= 20
        reasons.append("needing a lot of hints or attempts")
    if intent and intent.get("intent") == "stuck_frustrated":
        score -= 25
        reasons.append("sounds stuck or frustrated")

    score = max(0.0, min(100.0, score))
    computed = "guided" if score < 35 else "assisted" if score < 70 else "independent"

    mode = computed
    if requested_mode in MODES and MODES.index(requested_mode) < MODES.index(computed):
        mode = requested_mode
        reasons.append("keeping the more supportive mode you chose")

    return {
        "band": band or "unknown",
        "score": round(score),
        "mode": mode,
        "reason": ", ".join(reasons) or "no information yet, using a middle setting",
    }


# --------------------------------------------------------------- persona

_ROLE_GUIDANCE = {
    "sales": (
        "Use sales examples: deals, pipeline, revenue per rep, regions, discounts, customer segments. "
        "Connect cleaning and modelling to forecasting, trusting the numbers in a report, and not chasing bad leads."
    ),
    "operations": (
        "Use operations examples: orders, inventory, delivery times, supplier delays, defect rates, shifts. "
        "Connect cleaning and modelling to catching errors early, spotting bottlenecks and planning capacity."
    ),
    "hr": (
        "Use HR examples: headcount, attrition, tenure, salary bands, hiring funnels, survey scores. "
        "Connect cleaning and modelling to fair, reliable people decisions, and be careful to note when "
        "sensitive personal data needs extra care."
    ),
    "student": (
        "Use study and campus examples: exam scores, attendance, assignments, survey answers. "
        "Connect ideas to what an exam or coursework would ask, and name the correct term so they can use it."
    ),
}

_DEPTH_GUIDANCE = {
    "new": "They are new to data work. Avoid jargon; if you must use a term, define it in the same sentence. Go slowly.",
    "basics": "They know the basics. You can use common terms (mean, column, outlier) without defining them, but explain anything beyond that.",
    "confident": "They are confident. Be brief and precise, use the proper terms, and focus on the why and the trade-offs.",
}

_GOAL_GUIDANCE = (
    # Order matters: "coursework" contains "work", so coursework is checked before the job goal.
    (("course", "school", "exam", "study"), "Their goal is coursework, so be accurate and use the standard terminology."),
    (("job", "career"), "Their goal is to be better at their job, so end on how it applies to real work decisions."),
    (("curious", "how it works", "how it actually"), "They are curious about how it works, so show the mechanism, not only the rule."),
    (("explor",), "They are just exploring, so keep it light and interesting and do not overload them."),
)


def role_key(role: str | None) -> str | None:
    text = (role or "").strip().lower()
    for key in _ROLE_GUIDANCE:
        if key in text:
            return key
    return None


def persona_block(role: str | None, experience: str | None, goal: str | None) -> str:
    """Guidance lines for the LLM, or "" when we know nothing about the learner."""
    lines: list[str] = []

    key = role_key(role)
    if key:
        lines.append(_ROLE_GUIDANCE[key])
    elif (role or "").strip():
        lines.append(
            f"Their day-to-day is {role.strip()}. Draw examples from that kind of work where you can, "
            "and say so plainly if you are not sure of an example."
        )

    band = experience_band(experience)
    if band:
        lines.append(_DEPTH_GUIDANCE[band])

    goal_text = (goal or "").strip().lower()
    for keywords, guidance in _GOAL_GUIDANCE:
        if goal_text and any(k in goal_text for k in keywords):
            lines.append(guidance)
            break

    if not lines:
        return ""
    return "How to tailor your reply to this learner:\n" + "\n".join(f"- {line}" for line in lines)
