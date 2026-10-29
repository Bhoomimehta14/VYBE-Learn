# VYBE Learn: An Agentic Data Cleaning & Modeling Educator

An AI tutor for people with no data science background. An agent cleans the
learner's own messy dataset, verifies its work actually holds up, picks an
appropriate ML model, and explains every decision in plain language. An AI
Mentor sits beside each lesson, and a transfer-learning classifier works out
what kind of help the learner needs and how much support to give.
(The engine started life as AutoTriage-Clean, so some file names still say so.)

## The problem

Non-technical professionals (sales, ops, HR) have real data they want to
understand, but existing options are two extremes: generic DS courses using
textbook datasets, or nothing at all. People end up avoiding their own data,
outsourcing it, or fumbling through it without real understanding.

## Why this needs to be an agent, not a script or a chatbot

A fixed cleaning script applies one rule per problem and hopes for the best.
An LLM chatbot can *describe* cleaning steps but has no mechanism to check
whether its own actions actually worked. This system does neither — it:

1. **Observes** the data and detects real problems (missing values,
   inconsistent category labels, inconsistent formats)
2. **Decides** which fix to try first, based on the problem type
3. **Acts** — applies the fix
4. **Evaluates** — re-inspects the data afterward against statistical
   thresholds (does the fix actually hold up, or did it quietly distort
   the data?)
5. **Adapts** — if the fix failed the check, it's discarded and a more
   sophisticated strategy is tried instead

The same loop runs a second time for model selection: the agent tries a
simple model first, checks its cross-validated fit and residual pattern,
and escalates to more flexible models only when there's a concrete,
measured reason to.

**Concrete example, not hypothetical:** on a sales dataset with a bimodal
deal-size column (mostly small deals, some large enterprise deals),
median imputation for missing values distorts the distribution by 21%.
The agent's evaluation step catches this, discards the fix, and switches
to KNN imputation, which distorts it by only 7.6% — a genuine
try → fail → adapt cycle, not a scripted demo.

## Our solution

Two parts work together:

1. **The agent** (deterministic) cleans the data and picks the model, using the
   loop above. Every decision is checked by a statistical test, not by an LLM.
2. **The tutor** (Gemini, plus a small transfer-learning model) teaches what
   the agent did. It reads the learner's profile (role, experience, goal) and
   their message, decides what kind of help they are asking for, and sets how
   much to reveal: guided, assisted or independent.

The tutor never makes the cleaning or modelling decisions. It only explains
them, and it still works offline with built-in tips.

## Architecture

```
                        ┌─────────────────┐
   User uploads  ─────► │  detect_issues   │  observes the data,
   raw, messy           │                  │  classifies problems
   dataset               └────────┬─────────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │  decision tree   │  decides which fix
                        │                  │  to try, in order
                        └────────┬─────────┘
                                  │
                     ┌────────────┴────────────┐
                     ▼                          │
            ┌─────────────────┐                │
            │   action_fn()    │  acts          │
            └────────┬─────────┘                │
                     ▼                          │
            ┌─────────────────┐                │
            │  compute_stats   │  evaluates:    │
            │  before vs after │  did it work?  │
            └────────┬─────────┘                │
                     │                          │
              pass ──┤── fail ───────────────────┘
                     │      (try next candidate,
                     ▼       or flag for human review)
            ┌─────────────────┐
            │ downstream_check │  final verification:
            │                  │  can the data actually
            └────────┬─────────┘  be used? (aggregation,
                     │             chart, trend)
                     ▼
            ┌─────────────────┐
            │  model_selector  │  same observe→decide→act
            │  (2nd agentic    │  →evaluate→adapt loop,
            │   loop)          │  applied to model choice
            └────────┬─────────┘
                     ▼
            ┌─────────────────┐
            │ educator/narrate │  turns every log entry into
            │  (LLM + fallback)│  plain-language explanation
            └────────┬─────────┘
                     ▼
              User sees: cleaned data, working chart/model,
              and a step-by-step explanation of every decision
              the agent made and why.
```

The AI Mentor, docked beside every lesson, is a second path built on top:

```
  learner's message + profile (role, experience, goal)
        │
        ▼
  intent classifier (transfer learning)    frozen bge-small encoder + small head
        │   concept? hint? why wrong? stuck? next step? example? off-topic?
        ▼
  learner_level                            profile + mastery + hints/attempts
        │                                  -> guided / assisted / independent
        ▼
  Gemini (grounded in the lesson, dataset and code)
        │      falls back to a Google ADK tutor first when it is running,
        ▼      and to built-in tips when Gemini is unavailable
  reply, shown with the detected intent and support mode
```

### Component breakdown

| Component | What it does | Deterministic or LLM-driven |
|---|---|---|
| `detect_issues` | Scans columns, classifies problems | Deterministic (rule-based) |
| Decision tree | Orders candidate fixes per problem type | Deterministic |
| Action functions | Apply a specific fix | Deterministic |
| `compute_stats` / evaluation | Checks whether a fix actually worked | Deterministic (statistical thresholds) |
| `downstream_check` | Verifies the cleaned data is genuinely usable | Deterministic |
| `model_selector` | Picks and validates a regression model | Deterministic decision logic, standard sklearn models |
| `educator/narrate` | Explains every decision in plain language | LLM (Gemini), with a deterministic fallback if the API is unavailable |
| `app/intent` | Classifies what kind of help a learner is asking for | Transfer learning: frozen pretrained encoder + small trained head |
| `web/persona.py` | Turns role, experience, mastery and struggle into a support level | Deterministic |
| `web/chat.py` (AI Mentor) | Answers learner questions, grounded in the lesson | Gemini, with ADK tutor and offline fallbacks |

**Why rule-based planning, not LLM-driven planning:** auditable, fast,
free per-decision, and defensible to judges — "if X then Y" is provable;
"the LLM decided" is not. The LLM's role is deliberately narrow: explaining
decisions that were already made deterministically, never making the
decisions itself. This also means the system degrades gracefully — if the
LLM API is unavailable, the agent still works, just with plainer
explanations.

The classifier follows the same rule: it only routes. It picks which guidance
line goes into the prompt and never writes an answer or touches the data.

## Transfer learning: the learner-intent classifier

The AI Mentor and chat first work out what kind of help a learner is asking
for (a concept, a hint, a mistake explained, a next step, an example, or a
moment of frustration) and tailor the reply to their role, experience and
goal. That step is transfer learning: a frozen pretrained text encoder
(`BAAI/bge-small-en-v1.5`) turns the message into an embedding, and a small
head trained on 186 labelled learner questions picks the intent. The head only
routes; Gemini still writes every answer. If the encoder or head is missing,
or the head is not confident, the chat behaves exactly as before.

| Test | Transfer | Baseline (TF-IDF) |
|---|---|---|
| 5-fold cross-validation | 93.5% | 71.0% |
| 2 labelled examples per intent | 73.2% | 41.1% |
| 8 labelled examples per intent | 87.1% | 57.9% |

The few-shot rows are the point: with very few labels, the pretrained encoder
does far better. On a held-out set of 56 messages the gap is much smaller, and
that set was written by the same author as the training rows. Reproduce with
`python -m app.intent`. Method, caveats and file map: `docs/transfer-learning.md`.

## What changed after the first draft

- **Transfer learning added.** The mentor now detects the learner's intent and
  adjusts its reply (see above), instead of treating every message the same.
- **Personalisation.** A learner level and a role/experience/goal profile set
  how much help is shown. Off-topic questions get a friendly redirect on every
  tier, including offline.
- **One mentor.** The two separate chats became a single docked AI Mentor.
- **Simpler lessons.** Each level is two clear steps with clickable answers
  and an obvious next step.
- **Login first.** "Let's get started" opens a login page backed by
  `data/demo_users.json`.
- **Faster.** Dataset loading dropped from about 18 seconds to under one second
  locally, because the lesson text is now written on demand.
- **Flashcards and quizzes after EDA, ML foundations and modeling**, so those
  stages are no longer just data on a screen.
- **Faster upload.** Model selection (the slowest step) now runs in the background
  after upload and is cheaper (3-fold cross-validation, 100 trees, sampling past
  3,000 rows): an upload of 2,000 rows went from 36 seconds to about 1.
- **Faster mentor.** Gemini's extra "thinking" is switched off for short answers
  (about half the wait), the intent model loads at startup, and a tutor that is
  down is skipped for a minute instead of checked on every message.
- **Demo login** is `demo` / `demo123`.
- **Gemini instead of Claude**, with a pause-and-fallback when the free quota
  or key fails.
- **One deployed backend** on Render, and the ADK tutor copied into `adk-tutor/`.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # add GEMINI_API_KEY for the AI explanations (optional)
```

`GEMINI_API_KEY` (or `GOOGLE_API_KEY`) turns on the Gemini-written lesson
text and mentor replies. Without it, everything still works with built-in
template text. The free Gemini tier allows about 20 requests a day. When it
runs out, or the key is rejected, the backend pauses its Gemini calls, shows
"not personalized live yet", and uses the built-in tips until the quota resets.
`/api/health` reports `llm_available`, `llm_issue` and `llm_retry_in_seconds`.

## Running it

**Web app (React + FastAPI):**

```bash
python run_web.py --port 8000          # backend
npm --prefix web/ui install            # first time only
npm --prefix web/ui run dev            # frontend on http://localhost:5173
```

"Let's get started" opens a login page. The demo accounts live in
`data/demo_users.json` (`demo` / `demo123`, or `admin` / `admin123`) and are checked by
the backend; each account carries its own role, experience and goal. Anyone
without an account can answer three quick questions instead. The AI Mentor
is docked on the right half of every lesson screen and is not shown on the
landing, login, dataset or roadmap screens.

**Command line:**

```bash
python3 run_full_demo.py
```

Runs the full pipeline against the included demo dataset
(`messy_sales_dataset.csv`) and prints every stage: raw data, cleaning
with backtracking, downstream verification, model selection, and the
plain-language explanation a real user would see.

Without an API key set, narration falls back to deterministic
template text automatically. The pipeline never breaks due to a missing
key or a failed API call.

**Deployment:** the frontend runs on Vercel and the backend on Render
(`vybe-learn`). Set `VITE_API_BASE` on Vercel to the backend's address, and
`GEMINI_API_KEY` plus `CORS_ALLOW_ORIGINS` (the Vercel address) on Render.
The optional Google ADK tutor lives in `adk-tutor/`; the backend falls back to
direct Gemini and then to offline tips when it is not running.

**Tests:** blank the keys so the offline tests are not affected by a real one.

```bash
GEMINI_API_KEY= GOOGLE_API_KEY= python -m pytest tests
```

**Speed:** loading a dataset no longer waits on Gemini. The lesson text is
written only when the results page asks for it, in parallel, and cached.

## Example: the adaptation moment

```
[issue] deal_value: missing_numeric (severity=medium)
  -> tried impute_median: FAILED (backtracking) -- skew shifted 21.3%
     (2.186 -> 2.651), exceeds 15.0% threshold -- distribution distorted
  -> tried impute_knn: PASSED -- skew shift 7.6%, within 15.0% threshold
```

## Limitations

- Fuzzy category matching currently uses Python's `difflib` (no internet
  access during development to install `rapidfuzz`); swap in `rapidfuzz`
  for better real-world performance — see `requirements.txt`.
- Known-alias mapping for category normalization (e.g. "Bombay" → "Mumbai")
  is a small manual dictionary, not learned — string similarity alone
  cannot catch aliases that don't look similar as strings.
- Model selection currently supports regression only, using scikit-learn's
  built-in models (Linear, Ridge, Random Forest, Gradient Boosting).
- The downstream check runs once, after cleaning finishes; it does not
  currently trigger a second cleaning pass if it fails.
- The intent classifier was trained on 186 questions written by the team, not
  real learners, and it labels some nonsense input (such as "la la la") as
  off-topic. See `docs/transfer-learning.md` for the full list.

## Team

- **Person A** — agentic core: detection, cleaning actions, evaluation
  logic, backtracking loop, downstream verification, model selection loop
- **Person B** — LLM narration layer: prompt design, API integration,
  deterministic fallback
- **Person C** — Streamlit demo UI, dataset preparation, documentation,
  demo script
