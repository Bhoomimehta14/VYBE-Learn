# The agents in VYBE Learn, and how to show them

## The short version

VYBE Learn is a multi-agent system with two layers:

1. **The data agents** (deterministic Python) clean the data, check it, and pick a model.
2. **The tutor agents** (Gemini plus one small trained model) teach what the data agents did.

Rule that holds everywhere: **the LLM never makes a data decision.** Every cleaning, checking and
model choice is made by code and tested with numbers. The LLM only explains.

## Which agents are used, and what each one does

### In the running web app

| Agent | What it does | How |
|---|---|---|
| **Cleaning agent** (`app/agent/`) | Finds problems in your columns and fixes them | Loop: observe (detect issues) → decide (decision tree picks a fix) → act (apply it) → evaluate (did the stats stay healthy?) → adapt (if not, discard the fix and try the next one) |
| **Verification agent** (`app/evaluation/`) | Checks the cleaned data is really usable | Runs a group-by, a chart build and a time-series check; all must pass |
| **Model-selection agent** (`app/modeling/`) | Picks a model and justifies it | Same loop: start with the simplest model, score it with cross-validation and a residual check, move to a more flexible model only when a check fails |
| **Educator agent** (`app/educator/`) | Writes the plain-language explanation of every decision | Gemini, one call per log entry in parallel; template text if Gemini is unavailable |
| **Mentor agent** (`web/chat.py`) | Answers the learner's questions beside each lesson | Intent classifier → learner level → Gemini, grounded in the lesson, dataset and code on screen |

### In the Google ADK tutor (`adk-tutor/`)

One ADK **root agent** (Gemini) is the front door. It has five tools and no teaching ability of its
own. The tools call an **orchestrator** that routes each message to specialists:

| Specialist | Job |
|---|---|
| Orchestrator | Works out what the learner wants (keyword rules first, LLM only if no rule matches) and runs the right sequence of specialists |
| Profiler | Turns what the learner says about themselves into a profile: role, experience, goal |
| Data agent | Analyses the learner's own dataset (real pandas numbers) |
| Curriculum | Picks the next lesson from the profile, by rules |
| Teacher | Teaches one lesson as explain → example from their data → a question back |
| Visualization | Suggests and builds the right chart |
| Quiz | Writes and marks questions |
| Practice | Gives small challenges |
| Evaluator | Scores the answers |
| Gamification | Tracks XP, levels, badges, streaks |

The mentor tries this tutor first. If it is not running, it uses Gemini directly, and if Gemini is
unavailable it uses built-in tips. The ADK tutor is **not running in the deployed demo**; it runs
locally.

## How transfer learning is used

Transfer learning is in the **mentor agent**, in one place: working out what kind of help the learner
is asking for.

- A **frozen pretrained model** (`BAAI/bge-small-en-v1.5`, already trained by others on huge amounts
  of text) turns the message into 384 numbers that capture its meaning.
- A **small head** (logistic regression) was trained by us on 186 labelled learner questions to pick
  one of 7 intents: concept question, hint request, stuck or frustrated, why wrong, next step,
  example request, off-topic.
- We keep the big model's knowledge and train only the tiny last step. That is the transfer.
- If the head is under 45% confident it says nothing, and the mentor works as normal.
- The head only **routes**: it adds one guidance line to the prompt. Gemini still writes the answer.

Evidence (reproduce with `python -m app.intent`): 93.5% in 5-fold cross-validation against 71.0% for a
plain TF-IDF baseline; with only 2 labelled examples per intent, 73.2% against 41.1%. The held-out set
is small and self-written, so treat the few-shot rows as the main result.

## How we "trained it on Google ADK"

Honest answer: **ADK is not a training tool, so nothing was trained on it.** ADK is a framework for
building and running agents. What we did with it:

1. Defined a root agent (`adk-tutor/tutor_agent/agent.py`) with a Gemini model, a written
   instruction, and five tools.
2. Wrote the tools (`tutor_agent/tools.py`) to call our own Python multi-agent pipeline, so the
   numbers still come from pandas and scikit-learn.
3. Ran it as a server (`adk web`, which also serves the `/run` endpoint). Our backend sends each message to it with the learner's id
   and a session id, so the profile, XP and badges persist between visits.
4. Fixed the user id lookup so each learner keeps their own memory.

The only thing we trained is the intent head above, and it lives in our backend, outside ADK.
If your teacher asks "where did the learning happen?", the answer is: pretrained encoder (not ours)
plus the head (ours), on 186 labelled examples.

## Things to try in front of your teacher

Log in with `demo` / `demo123` (a beginner), then load the sample data. Open the mentor on any lesson
and type these. The intent shown under each reply is what the classifier detected; all of these were
checked.

| Type this | What it shows |
|---|---|
| "What does missing value mean?" | Detected as a concept question; a plain explanation |
| "Can you give me a small hint?" | Hint request; hints, not the answer, because the learner is a beginner |
| "I'm so lost, I don't get any of this" | Stuck or frustrated; the tone softens and the support level goes up |
| "Why was my answer wrong?" | Why wrong; explains the mistake using the lesson on screen |
| "Show me an example with my data" | Example request; uses this dataset's own columns |
| "Tell me a joke about pizza" | Off-topic; one friendly line, then back to the lesson, not a refusal |
| "Why does median imputation distort deal_value?" | The classifier is **unsure** (below 45%) and stays quiet; shows the safety net |

A good two-minute story:

1. "The cleaning agent tried median imputation, the check failed because the data was distorted by 21%,
   so it backtracked to KNN, which distorted it by 7.6%." (Level 1.) This is observe, decide, act,
   evaluate, adapt, and no LLM chose it.
2. "Now watch the mentor adapt." Type the frustrated sentence, then the hint sentence. Point at the
   intent tag and the support-mode tag.
3. Start again from the landing page, answer the three questions as a confident analyst, ask for a hint again, and compare:
   the confident learner gets less hand-holding. Same question, different support level.
4. Type the pizza joke: it redirects. Then the median imputation question: the classifier abstains.
5. "The model is only a router. Gemini writes the words; the data decisions came from code."

## Questions a teacher may ask

- **Is it really multi-agent?** Yes: separate agents with one job each (clean, verify, model, explain,
  mentor), plus the ADK tutor's nine specialists coordinated by an orchestrator.
- **Why not let the LLM decide?** Auditable and repeatable: a rule and a threshold can be checked, an LLM
  answer cannot.
- **What if Gemini is down or out of quota?** The app keeps working with built-in text and says so.
- **What is the weakness?** The intent head was trained on questions we wrote, not real learners, and the
  held-out test is small. Also the ADK tutor is not deployed.
