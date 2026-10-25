"""Generates VYBE_Learn_Pitch_Deck.pptx from the same real facts as
pitch_deck_reference.html - Night Signal palette, no invented numbers."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

BG = RGBColor(0x0B, 0x0A, 0x10)
SURFACE = RGBColor(0x16, 0x14, 0x1C)
SURFACE_RAISED = RGBColor(0x1D, 0x1A, 0x25)
INK = RGBColor(0xF4, 0xF2, 0xF7)
INK_SOFT = RGBColor(0x94, 0x8F, 0xA0)
INK_FAINT = RGBColor(0x63, 0x5D, 0x6E)
ACCENT = RGBColor(0xFF, 0x3E, 0xA5)
LINE = RGBColor(0x28, 0x24, 0x2F)
GOOD = RGBColor(0x3D, 0xDC, 0x8A)
WARN = RGBColor(0xFF, 0xC9, 0x3C)
FAIL = RGBColor(0xFF, 0x6B, 0x7A)

FONT_DISPLAY = "Georgia"  # closest bundled-safe stand-in for Sora's weight
FONT_BODY = "Calibri"
FONT_MONO = "Consolas"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
BLANK = prs.slide_layouts[6]


def add_slide():
    s = prs.slides.add_slide(BLANK)
    bg = s.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG
    return s


def box(slide, l, t, w, h):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    return tb, tf


def set_run(r, text, size, color, bold=False, font=FONT_BODY, italic=False):
    r.text = text
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.bold = bold
    r.font.italic = italic
    r.font.name = font


def para(tf, text, size, color, bold=False, font=FONT_BODY, space_after=6, align=PP_ALIGN.LEFT, first=False):
    p = tf.paragraphs[0] if first and not tf.paragraphs[0].runs else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(space_after)
    r = p.add_run()
    set_run(r, text, size, color, bold, font)
    return p


def eyebrow(slide, text, top=Inches(0.5)):
    _, tf = box(slide, Inches(0.7), top, Inches(11.9), Inches(0.4))
    para(tf, text.upper(), 13, ACCENT, bold=True, font=FONT_MONO, first=True)


def title(slide, text, top=Inches(0.85), size=32, width=Inches(11.9)):
    _, tf = box(slide, Inches(0.7), top, width, Inches(1.1))
    p = para(tf, text, size, INK, bold=True, font=FONT_DISPLAY, first=True)
    return p


def rounded_rect(slide, l, t, w, h, fill=SURFACE, line_color=LINE, radius=0.06):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    shp.adjustments[0] = radius
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = line_color
    shp.line.width = Pt(1)
    shp.shadow.inherit = False
    return shp


def card(slide, l, t, w, h, heading, body, heading_color=INK, body_size=13):
    shp = rounded_rect(slide, l, t, w, h)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.2)
    tf.margin_right = Inches(0.2)
    tf.margin_top = Inches(0.15)
    tf.margin_bottom = Inches(0.15)
    para(tf, heading, 14, heading_color, bold=True, font=FONT_DISPLAY, space_after=4, first=True)
    para(tf, body, body_size, INK_SOFT, space_after=0)
    return shp


def footer(slide, text="vybe-learn \u00b7 web/api.py + app/agent"):
    _, tf = box(slide, Inches(0.7), Inches(7.05), Inches(11.9), Inches(0.35))
    para(tf, text, 9, INK_FAINT, font=FONT_MONO, first=True)


# ------------------------------------------------------------- slide 1: hero
s = add_slide()
_, tf = box(s, Inches(0.9), Inches(1.5), Inches(11.5), Inches(0.5))
para(tf, "SYSTEM ARCHITECTURE & PITCH REFERENCE", 14, ACCENT, bold=True, font=FONT_MONO, first=True)

_, tf = box(s, Inches(0.9), Inches(2.0), Inches(11.5), Inches(1.8))
p = tf.paragraphs[0]
p.alignment = PP_ALIGN.LEFT
r = p.add_run()
set_run(r, "An agent that shows its work,", 40, INK, bold=True, font=FONT_DISPLAY)
p2 = tf.add_paragraph()
r2 = p2.add_run()
set_run(r2, "teaching the work it shows.", 40, INK, bold=True, font=FONT_DISPLAY)

_, tf = box(s, Inches(0.9), Inches(3.6), Inches(10.8), Inches(1.1))
para(
    tf,
    "VYBE Learn is a gamified data-science tutor built around one real constraint: a deterministic "
    "agent cleans data and selects a model on its own - observe, decide, act, evaluate, adapt - and the "
    "learner's job is to predict what it will do, not steer it. An LLM narrates and tutors on top; it "
    "never makes the analytical decisions.",
    16, INK_SOFT, first=True,
)

stats = [
    ("2", "loops", "Real agentic decisions, not one"),
    ("6", "stages", "Python fundamentals \u2192 final project"),
    ("3", "tiers", "Tutor fallback, always answers"),
    ("3", "modes", "Mentor: guided / assisted / independent"),
    ("37", "/ 37", "Backend tests passing"),
    ("0", "invented", "Numbers on screen - all traced to code"),
]
sw = Inches(1.85)
sx = Inches(0.9)
sy = Inches(5.0)
for i, (num, unit, label) in enumerate(stats):
    l = Emu(sx + i * (sw + Inches(0.12)))
    rounded_rect(s, l, sy, sw, Inches(1.5), fill=SURFACE)
    _, tf = box(s, Emu(l + Inches(0.12)), Emu(sy + Inches(0.12)), Emu(sw - Inches(0.24)), Inches(1.3))
    p = tf.paragraphs[0]
    r = p.add_run()
    set_run(r, num, 26, INK, bold=True, font=FONT_MONO)
    r2 = p.add_run()
    set_run(r2, " " + unit, 11, INK_FAINT, font=FONT_MONO)
    p2 = tf.add_paragraph()
    p2.space_before = Pt(4)
    r3 = p2.add_run()
    set_run(r3, label, 10, INK_SOFT)


# ------------------------------------------------------ slide 2: proof log
s = add_slide()
eyebrow(s, "The moment that sells it")
title(s, "Watch it change its mind, on your own data")
_, tf = box(s, Inches(0.7), Inches(1.55), Inches(11.9), Inches(0.9))
para(
    tf,
    "This is the actual reveal log from a live run on the sample dataset - not a scripted demo path. "
    "The agent tried the obvious fix, measured that it distorted the column, and switched strategies "
    "before ever showing the learner an answer.",
    14, INK_SOFT, first=True,
)

log_bg = RGBColor(0x08, 0x07, 0x0B)
log_shp = rounded_rect(s, Inches(0.7), Inches(2.6), Inches(11.9), Inches(2.9), fill=log_bg, radius=0.03)
tf = log_shp.text_frame
tf.word_wrap = True
tf.margin_left = Inches(0.3)
tf.margin_top = Inches(0.25)
tf.margin_right = Inches(0.3)

lines = [
    ('$ agent.clean(column="deal_value", issue="missing_numeric")', INK_FAINT, False),
    ("DISCARDED  impute_median  \u2192  skew shifted 21.3% (2.186 \u2192 2.651), exceeds 15.0% threshold", FAIL, True),
    ("KEPT       impute_knn     \u2192  skew shift 7.6%, within 15.0% threshold", GOOD, True),
    ('$ agent.select_model(target="deal_value")', INK_FAINT, False),
    ("KEPT       LinearRegression  \u2192  R\u00b2=0.287, residual\u2194prediction corr=0.142 (\u22640.25) \u2192 acceptable fit", GOOD, True),
]
for i, (text, color, bold) in enumerate(lines):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(10)
    r = p.add_run()
    set_run(r, text, 13, color, bold=bold, font=FONT_MONO)

_, tf = box(s, Inches(0.7), Inches(5.7), Inches(11.9), Inches(0.9))
p = tf.paragraphs[0]
r = p.add_run()
set_run(r, "Every number above is a live computation, ", 14, INK_SOFT)
r2 = p.add_run()
set_run(r2, "re-run for whatever dataset the judge uploads", 14, INK, bold=True)
r3 = p.add_run()
set_run(r3, " - not a cached string. That's the difference between \u201can AI-themed UI\u201d and an agent.", 14, INK_SOFT)
footer(s)


# --------------------------------------------------- slide 3: architecture
s = add_slide()
eyebrow(s, "01 \u2014 System map")
title(s, "Four layers, one honesty rule")
_, tf = box(s, Inches(0.7), Inches(1.55), Inches(11.9), Inches(0.7))
para(
    tf,
    "The UI never computes an analytical result itself - every number, chart, and decision is fetched "
    "from the deterministic core. The LLM layer only ever narrates or tutors around it.",
    14, INK_SOFT, first=True,
)

layers = [
    ("Browser", "React 19 + Vite + Tailwind v4", "Screen state machine \u00b7 AI Mentor panel \u00b7 Notes", ACCENT),
    ("FastAPI", "web/api.py", "In-memory Session store \u00b7 /api/dataset /api/levels /api/mentor \u2026", INK),
    ("Deterministic core", "decisions never LLM-made", "detect.py \u2192 loop.py \u2192 actions.py \u00b7 model_selector.py", GOOD),
    ("3-tier tutor", "explanation only, never decides", "ADK multi-agent \u2192 direct Gemini \u2192 deterministic FAQ", WARN),
]
ly = Inches(2.4)
lh = Inches(1.05)
for i, (name, sub, detail, accent) in enumerate(layers):
    top = Emu(ly + i * (lh + Inches(0.12)))
    shp = rounded_rect(s, Inches(0.7), top, Inches(11.9), lh, fill=SURFACE)
    # accent bar
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.7), top, Inches(0.08), lh)
    bar.fill.solid()
    bar.fill.fore_color.rgb = accent
    bar.line.fill.background()
    bar.shadow.inherit = False
    tf = shp.text_frame
    tf.margin_left = Inches(0.35)
    tf.margin_top = Inches(0.12)
    p = tf.paragraphs[0]
    r = p.add_run()
    set_run(r, name, 15, INK, bold=True, font=FONT_DISPLAY)
    r2 = p.add_run()
    set_run(r2, "   " + sub, 11, INK_FAINT, font=FONT_MONO)
    p2 = tf.add_paragraph()
    p2.space_before = Pt(4)
    r3 = p2.add_run()
    set_run(r3, detail, 12, INK_SOFT, font=FONT_MONO)
    if i < len(layers) - 1:
        arrow_top = Emu(top + lh + Inches(0.005))
        _, atf = box(s, Inches(6.2), arrow_top, Inches(1), Inches(0.12))
        pa = atf.paragraphs[0]
        pa.alignment = PP_ALIGN.CENTER
        ra = pa.add_run()
        set_run(ra, "\u2193", 12, INK_FAINT)
footer(s)


# ------------------------------------------------------- slide 4: agent loop
s = add_slide()
eyebrow(s, "02 \u2014 The actual agent")
title(s, "Observe \u2192 decide \u2192 act \u2192 evaluate \u2192 adapt")
_, tf = box(s, Inches(0.7), Inches(1.55), Inches(11.9), Inches(0.7))
para(
    tf,
    "The same five-step loop runs twice: once choosing a cleaning strategy per column, once choosing a "
    "regression model. Each escalation is justified by a specific measured failure.",
    14, INK_SOFT, first=True,
)

steps = [
    ("01", "Observe", "Column stats, skew, null% \u2014 or dataset shape, feature count, linearity."),
    ("02", "Decide", "Pick the simplest candidate strategy first, with a stated reason."),
    ("03", "Act", "Apply the transform, or fit the model."),
    ("04", "Evaluate", "Re-measure: skew shift, cross-validated R\u00b2/RMSE, residual pattern."),
    ("05", "Adapt", "Pass \u2192 keep. Fail \u2192 escalate to the next candidate and repeat."),
]
cw = Inches(2.26)
cx = Inches(0.7)
cy = Inches(2.5)
for i, (n, h, b) in enumerate(steps):
    l = Emu(cx + i * (cw + Inches(0.1)))
    shp = rounded_rect(s, l, cy, cw, Inches(1.8), fill=SURFACE)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.15)
    tf.margin_right = Inches(0.15)
    tf.margin_top = Inches(0.15)
    para(tf, n, 11, ACCENT, font=FONT_MONO, space_after=4, first=True)
    para(tf, h, 15, INK, bold=True, font=FONT_DISPLAY, space_after=4)
    para(tf, b, 11, INK_SOFT, space_after=0)

thresh = [
    ("skew shift \u2264 15%", "cleaning fix kept"),
    ("R\u00b2 \u2265 0.15", "model acceptable"),
    ("|residual\u2194pred corr| \u2264 0.25", "no missed pattern"),
]
tx = Inches(0.7)
ty = Inches(4.55)
for label, sub in thresh:
    w = Inches(3.9)
    shp = rounded_rect(s, tx, ty, w, Inches(0.55), fill=SURFACE_RAISED, radius=0.5)
    tf = shp.text_frame
    tf.margin_left = Inches(0.2)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    set_run(r, f"{label}  \u2192  {sub}", 11, WARN, font=FONT_MONO)
    tx = Emu(tx + w + Inches(0.2))

table_top = Inches(5.4)
rows_data = [
    ("Issue type", "Candidate ladder (simplest first)"),
    ("Missing numeric", "impute_median \u2192 impute_knn"),
    ("Missing categorical", "impute_mode"),
    ("Inconsistent labels", "normalize_categories (fuzzy match)"),
    ("Numbers stored as text", "coerce_numeric_strings"),
    ("Mixed-up date formats", "coerce_dates"),
    ("Model family", "LinearRegression \u2192 Ridge \u2192 RandomForest \u2192 GradientBoosting"),
]
gtable = s.shapes.add_table(len(rows_data), 2, Inches(0.7), table_top, Inches(11.9), Inches(1.6)).table
gtable.columns[0].width = Inches(3.2)
gtable.columns[1].width = Inches(8.7)
for ri, (a, b) in enumerate(rows_data):
    is_header = ri == 0
    for ci, val in enumerate((a, b)):
        cell = gtable.cell(ri, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = SURFACE_RAISED if is_header else SURFACE
        cell.margin_left = Inches(0.1)
        cell.margin_top = Inches(0.03)
        cell.margin_bottom = Inches(0.03)
        tf = cell.text_frame
        p = tf.paragraphs[0]
        r = p.add_run()
        color = INK_FAINT if is_header else (INK if ci == 0 else INK_SOFT)
        set_run(r, val, 10 if is_header else 11, color, bold=is_header, font=FONT_MONO if is_header else FONT_BODY)
footer(s)


# ---------------------------------------------------- slide 5: tutor tiers
s = add_slide()
eyebrow(s, "03 \u2014 Never a dead end")
title(s, "Three tutor tiers, one honest fallback")
_, tf = box(s, Inches(0.7), Inches(1.55), Inches(11.9), Inches(0.9))
para(
    tf,
    "Every chat and mentor reply tries the richest source first and degrades gracefully - each tier "
    "returns nothing rather than a guess, so a missing key or a second server never breaks the chat.",
    14, INK_SOFT, first=True,
)

rows_data = [
    ("Tier", "Source", "Adds", "Fails silently when"),
    ("1", "ADK multi-agent tutor (port 8765)", "Profiler + gamification agents - real XP, badges, profile", "Server not running, or its key is invalid"),
    ("2", "Direct Gemini (google-genai)", "Live, grounded answer, no memory layer", "No/invalid GEMINI_API_KEY"),
    ("3", "Deterministic FAQ + rule-based reply", "Always available, zero external dependency", "never - this is the floor"),
]
ttop = Inches(2.7)
gtable = s.shapes.add_table(len(rows_data), 4, Inches(0.7), ttop, Inches(11.9), Inches(2.6)).table
widths = [Inches(0.8), Inches(3.3), Inches(4.1), Inches(3.7)]
for i, w in enumerate(widths):
    gtable.columns[i].width = w
for ri, row in enumerate(rows_data):
    is_header = ri == 0
    for ci, val in enumerate(row):
        cell = gtable.cell(ri, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = SURFACE_RAISED if is_header else SURFACE
        cell.margin_left = Inches(0.12)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        r = p.add_run()
        color = INK_FAINT if is_header else (INK if ci == 0 or ci == 1 else INK_SOFT)
        set_run(r, val, 10 if is_header else 12, color, bold=is_header or ci == 0, font=FONT_MONO if is_header else FONT_BODY)
footer(s)


# ---------------------------------------------------------- slide 6: mentor
s = add_slide()
eyebrow(s, "04 \u2014 Built this session")
title(s, "AI Mentor: platform-wide, mode-aware coaching")
_, tf = box(s, Inches(0.7), Inches(1.55), Inches(11.9), Inches(0.7))
para(
    tf,
    "A floating panel available from any screen, fed a live context object instead of just the last "
    "message - instructed to nudge, not solve, until the learner has actually tried.",
    14, INK_SOFT, first=True,
)

modes = [
    ("Guided", "Struggling", "Very simple language, one step at a time, concrete example, one question per reply."),
    ("Assisted", "Making progress", "Names the concept, gives a partial hint, asks for another attempt before revealing more."),
    ("Independent", "Confident", "Minimal hints - asks the learner to justify their own reasoning and code."),
]
mw = Inches(3.83)
mx = Inches(0.7)
my = Inches(2.4)
for i, (tag, h, b) in enumerate(modes):
    l = Emu(mx + i * (mw + Inches(0.1)))
    shp = rounded_rect(s, l, my, mw, Inches(1.5), fill=SURFACE)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.18)
    tf.margin_top = Inches(0.13)
    para(tf, tag.upper(), 10, ACCENT, bold=True, font=FONT_MONO, space_after=4, first=True)
    para(tf, h, 16, INK, bold=True, font=FONT_DISPLAY, space_after=4)
    para(tf, b, 11, INK_SOFT, space_after=0)

actions = ["Explain this", "Give me a hint", "Why is this wrong?", "Show an example", "Explain the output", "What should I try next?"]
ax = Inches(0.7)
ay = Inches(4.15)
for act in actions:
    w = Inches(1.9) if len(act) < 16 else Inches(2.3)
    shp = rounded_rect(s, ax, ay, w, Inches(0.42), fill=SURFACE_RAISED, radius=0.5)
    tf = shp.text_frame
    tf.margin_left = Inches(0.12)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    set_run(r, act, 10, INK_SOFT)
    ax = Emu(ax + w + Inches(0.12))

code_shp = rounded_rect(s, Inches(0.7), Inches(4.85), Inches(11.9), Inches(1.9), fill=SURFACE_RAISED, radius=0.04)
tf = code_shp.text_frame
tf.word_wrap = True
tf.margin_left = Inches(0.25)
tf.margin_top = Inches(0.15)
ctx_lines = [
    '{ "user_message": "...",',
    '  "current_lesson": { title, objective, difficulty, step },',
    '  "dataset": { name, columns, shape, current_version },',
    '  "current_code": "...", "last_output": "...", "last_error": "...",',
    '  "attempt_count": 0, "hints_used": 0, "mastery_level": 0,',
    '  "learning_mode": "guided|assisted|independent",',
    '  "previous_mistakes": [], "recent_actions": [] }',
]
for i, line in enumerate(ctx_lines):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(2)
    r = p.add_run()
    set_run(r, line, 11, INK_SOFT, font=FONT_MONO)
footer(s)


# ------------------------------------------------ slide 7: transfer learning
s = add_slide()
eyebrow(s, "05 \u2014 Transfer learning")
title(s, "A frozen encoder plus a small trained head")
_, tf = box(s, Inches(0.7), Inches(1.55), Inches(11.9), Inches(0.7))
para(
    tf,
    "Before the mentor answers, a small model works out what kind of help the learner is asking for. "
    "It only routes: Gemini still writes every reply, and with no encoder the chat behaves as it always did.",
    14, INK_SOFT, first=True,
)

steps = [
    ("1  Frozen encoder", "BAAI/bge-small-en-v1.5 already understands language. We never retrain it."),
    ("2  Small trained head", "Logistic regression on 186 labelled learner questions picks one of 7 intents, or says it is not sure."),
    ("3  Tailored reply", "The intent, the learner's level and their role, experience and goal shape the prompt."),
]
sw = Inches(3.83)
for i, (h, b) in enumerate(steps):
    card(s, Emu(Inches(0.7) + i * (sw + Inches(0.2))), Inches(2.4), sw, Inches(1.45), h, b, body_size=12)

tl_rows = [
    ("Test", "Transfer", "Baseline (TF-IDF)"),
    ("5-fold cross-validation, 186 questions", "93.5%", "71.0%"),
    ("Only 2 labelled examples per intent", "73.2%", "41.1%"),
    ("Only 8 labelled examples per intent", "87.1%", "57.9%"),
    ("Only 16 labelled examples per intent", "90.4%", "62.1%"),
]
tl_table = s.shapes.add_table(len(tl_rows), 3, Inches(0.7), Inches(4.1), Inches(11.9), Inches(2.0)).table
for i, w in enumerate([Inches(6.5), Inches(2.7), Inches(2.7)]):
    tl_table.columns[i].width = w
for ri, row in enumerate(tl_rows):
    is_header = ri == 0
    for ci, val in enumerate(row):
        cell = tl_table.cell(ri, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = SURFACE_RAISED if is_header else SURFACE
        cell.margin_left = Inches(0.12)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        p = tf.paragraphs[0]
        r = p.add_run()
        color = INK_FAINT if is_header else (GOOD if ci == 1 else (INK if ci == 0 else INK_SOFT))
        set_run(r, val, 10 if is_header else 12, color, bold=is_header or ci == 1, font=FONT_MONO if is_header else FONT_BODY)

_, tf = box(s, Inches(0.7), Inches(6.2), Inches(11.9), Inches(0.8))
para(
    tf,
    "On 56 held-out messages: 98.2% with no wrong labels, and the baseline reaches 92.9% there, so the gap is small. "
    "We wrote those messages ourselves, which makes them easier than real learners. "
    "The few-shot rows are the real evidence.",
    11, INK_SOFT, first=True,
)
footer(s, "vybe-learn \u00b7 app/intent + web/persona.py \u00b7 docs/transfer-learning.md")


# ------------------------------------------------------- slide 8: curriculum
s = add_slide()
eyebrow(s, "06 \u2014 Learning path")
title(s, "Six stages, ten real steps")
_, tf = box(s, Inches(0.7), Inches(1.55), Inches(11.9), Inches(0.6))
para(
    tf,
    "Verification is a bridging step between Cleaning and EDA - real, tested functionality, kept "
    "because it's the honest answer to \u201cdid the fix actually work?\u201d",
    13, INK_SOFT, first=True,
)

stages = [
    ("01", "Python & Data Fundamentals", "Read a CSV, understand rows/columns, real pd.read_csv / df.shape / df.columns."),
    ("02", "Data Cleaning", "One level per detected issue. \u23ed \u201cSkip cleaning\u201d jumps straight to Verification."),
    ("\u2014", "Verification (bridge)", "Real downstream tasks on cleaned data - aggregation, a bar chart, a trend line."),
    ("03", "Exploratory Data Analysis", "Real histograms, category bars, trend - plus a correlation card."),
    ("04", "Machine Learning Foundations", "Target, features, train/test split, regression vs. classification."),
    ("05", "Model Selection & Evaluation", "The second agentic loop, narrated. \u23ed \u201cSkip modeling\u201d available."),
    ("06", "Final Project", "Full recap - every cleaning decision, every chart, the chosen model."),
]
sy2 = Inches(2.25)
row_h = Inches(0.63)
for i, (n, h, b) in enumerate(stages):
    top = Emu(sy2 + i * row_h)
    _, tf = box(s, Inches(0.7), top, Inches(0.5), row_h)
    para(tf, n, 12, ACCENT, font=FONT_MONO, first=True)
    _, tf = box(s, Inches(1.3), top, Inches(11.3), row_h)
    p = tf.paragraphs[0]
    r = p.add_run()
    set_run(r, h + "  ", 13, INK, bold=True, font=FONT_DISPLAY)
    r2 = p.add_run()
    set_run(r2, b, 11, INK_SOFT)
footer(s)


# ------------------------------------------------------------ slide 8: stack
s = add_slide()
eyebrow(s, "07 \u2014 Tech stack")
title(s, "What it's actually built on")

rows_data = [
    ("Layer", "Library", "Version"),
    ("Frontend", "React / React DOM", "19.2"),
    ("Frontend", "Vite", "8.3"),
    ("Frontend", "TypeScript", "~6.0"),
    ("Frontend", "Tailwind CSS", "4.3"),
    ("Frontend", "framer-motion", "13.2"),
    ("Backend", "FastAPI", "\u22650.110"),
    ("Backend", "Uvicorn", "\u22650.27"),
    ("Backend", "pandas / numpy", "\u22652.0 / \u22651.24"),
    ("Modeling", "scikit-learn", "\u22651.3"),
    ("Modeling", "matplotlib", "\u22653.7"),
    ("AI / narration", "google-genai (direct Gemini)", "\u22650.1"),
    ("AI / narration", "Google ADK (separate service)", "Gemini 3.6 Flash"),
    ("Testing", "pytest + httpx", "\u22657.4 / \u22650.27"),
]
ttop = Inches(1.6)
gtable = s.shapes.add_table(len(rows_data), 3, Inches(0.7), ttop, Inches(11.9), Inches(5.3)).table
widths = [Inches(2.7), Inches(6.2), Inches(3.0)]
for i, w in enumerate(widths):
    gtable.columns[i].width = w
for ri, row in enumerate(rows_data):
    is_header = ri == 0
    gtable.rows[ri].height = Inches(0.34) if not is_header else Inches(0.4)
    for ci, val in enumerate(row):
        cell = gtable.cell(ri, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = SURFACE_RAISED if is_header else SURFACE
        cell.margin_left = Inches(0.12)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        p = tf.paragraphs[0]
        r = p.add_run()
        color = INK_FAINT if is_header else (INK if ci == 0 else INK_SOFT)
        set_run(r, val, 10 if is_header else 12, color, bold=is_header or ci == 0, font=FONT_MONO if (is_header or ci == 2) else FONT_BODY)
footer(s)


# --------------------------------------------------------- slide 9: why wins
s = add_slide()
eyebrow(s, "08 \u2014 The case")
title(s, "Why this beats a chatbot wrapper")

rows_data = [
    ("Axis", "Typical AI-tutor demo", "VYBE Learn"),
    ("Who decides the fix", "the LLM guesses in-context", "a deterministic loop, measured and re-checked"),
    ("Why a fix was kept", "a plausible-sounding sentence", "a real skew-shift number against a stated threshold"),
    ("When the model breaks", "stalls, apologizes, or hallucinates", "falls through ADK \u2192 Gemini \u2192 FAQ, discloses which"),
    ("Personalization", "one-size tone knob", "3 modes, driven by real hint/attempt counters"),
    ("Cheats the learner?", "answers before they've tried", "nudges only, reveal gated on attempt history"),
    ("Respects prior knowledge", "forces every learner through every step", "explicit Skip actions, no faked checkmarks"),
]
ttop = Inches(1.6)
gtable = s.shapes.add_table(len(rows_data), 3, Inches(0.7), ttop, Inches(11.9), Inches(3.6)).table
widths = [Inches(3.1), Inches(4.4), Inches(4.4)]
for i, w in enumerate(widths):
    gtable.columns[i].width = w
for ri, row in enumerate(rows_data):
    is_header = ri == 0
    for ci, val in enumerate(row):
        cell = gtable.cell(ri, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = SURFACE_RAISED if is_header else SURFACE
        cell.margin_left = Inches(0.12)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        prefix = "" if is_header else ("\u2717  " if ci == 1 else ("\u2713  " if ci == 2 else ""))
        color = FAIL if (not is_header and ci == 1) else (GOOD if (not is_header and ci == 2) else (INK_FAINT if is_header else INK))
        r = p.add_run()
        set_run(r, prefix + val, 10 if is_header else 11, color, bold=is_header, font=FONT_MONO if is_header else FONT_BODY)

rubric = [
    ("01", "Technical depth", "Two independent agentic loops with real statistical acceptance criteria."),
    ("02", "Reliability under judging", "3-tier fallback: bad wifi or a dead key degrades the tutor, never crashes the demo."),
    ("03", "Genuine UX craft", "Gamified scoring, progress rail, mentor panel, notes - none blocking the core loop."),
    ("04", "Works on their data", "Upload any CSV - detection, cleaning, charts, modeling all run live."),
]
rw = Inches(2.86)
rx = Inches(0.7)
ry = Inches(5.45)
for i, (n, h, b) in enumerate(rubric):
    l = Emu(rx + i * (rw + Inches(0.1)))
    shp = rounded_rect(s, l, ry, rw, Inches(1.45), fill=SURFACE)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.15)
    tf.margin_top = Inches(0.1)
    para(tf, n, 16, ACCENT, bold=True, font=FONT_MONO, space_after=3, first=True)
    para(tf, h, 12, INK, bold=True, font=FONT_DISPLAY, space_after=3)
    para(tf, b, 9.5, INK_SOFT, space_after=0)


# --------------------------------------------------- slide 10: talking points
s = add_slide()
eyebrow(s, "09 \u2014 For the deck")
title(s, "What to actually say")

talk = [
    ("The hook", [
        "The agent cleans data and picks a model completely on its own - the learner predicts, never steers.",
        "Every \u201cwhy\u201d on screen is a real measured number, not a canned explanation.",
        "Wrong guesses cost points but never touch the data.",
    ]),
    ("The differentiator", [
        "Two real agentic loops, same observe/decide/act/evaluate/adapt shape, reused on purpose.",
        "A mentor that refuses to just answer - three modes tuned to how stuck the learner is.",
        "The tutor layer can vanish entirely and the product still teaches, honestly.",
    ]),
    ("Live demo order", [
        "Load the sample dataset \u2192 show the 10-step roadmap.",
        "Guess a cleaning strategy wrong \u2192 reveal the agent's real backtrack.",
        "Open the AI Mentor mid-lesson \u2192 switch modes \u2192 ask \u201cgive me a hint.\u201d",
        "Jump to Model Selection \u2192 escalation reasoning \u2192 Final Project recap.",
    ]),
    ("If asked \u201cwhere's the AI\u201d", [
        "Two places, on purpose: the deterministic core (decisions) and narration (explanation).",
        "That separation is why a judge can trust the R\u00b2 on screen - no LLM touched the math.",
    ]),
]
tw = Inches(5.85)
tx = Inches(0.7)
ty = Inches(1.6)
for i, (h, items) in enumerate(talk):
    col = i % 2
    row = i // 2
    l = Emu(tx + col * (tw + Inches(0.2)))
    t = Emu(ty + row * Inches(2.7))
    shp = rounded_rect(s, l, t, tw, Inches(2.5), fill=SURFACE)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.2)
    tf.margin_top = Inches(0.15)
    para(tf, h, 14, INK, bold=True, font=FONT_DISPLAY, space_after=6, first=True)
    for item in items:
        p = tf.add_paragraph()
        p.space_after = Pt(5)
        r = p.add_run()
        set_run(r, "\u2022 " + item, 11, INK_SOFT)
footer(s)


out_path = r"C:\Users\bhoom\Downloads\project\project\VYBE_Learn_Pitch_Deck.pptx"
prs.save(out_path)
print("Saved:", out_path)
