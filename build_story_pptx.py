"""VYBE_Learn_Story_Pitch.pptx - storytelling submission deck.
Businessman narrative + hackathon-required sections, mascot throughout.
Reuses only real facts (repo URLs, live URLs, actual agent behavior)."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR

BG = RGBColor(0x0B, 0x0A, 0x10)
SURFACE = RGBColor(0x16, 0x14, 0x1C)
SURFACE_RAISED = RGBColor(0x1D, 0x1A, 0x25)
INK = RGBColor(0xF4, 0xF2, 0xF7)
INK_SOFT = RGBColor(0x94, 0x8F, 0xA0)
INK_FAINT = RGBColor(0x63, 0x5D, 0x6E)
ACCENT = RGBColor(0xFF, 0x3E, 0xA5)
ACCENT_DEEP = RGBColor(0xD9, 0x1C, 0x82)
LINE = RGBColor(0x28, 0x24, 0x2F)
GOOD = RGBColor(0x3D, 0xDC, 0x8A)
WARN = RGBColor(0xFF, 0xC9, 0x3C)
FAIL = RGBColor(0xFF, 0x6B, 0x7A)
RAJ_SKIN = RGBColor(0xE0, 0xB0, 0x88)
RAJ_SHIRT = RGBColor(0x5C, 0x6B, 0xC0)

FONT_DISPLAY = "Georgia"
FONT_BODY = "Calibri"
FONT_MONO = "Consolas"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def add_slide(bg_color=BG):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = bg_color
    return s


def _noline(shp):
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


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


def para(tf, text, size, color, bold=False, font=FONT_BODY, space_after=6, align=PP_ALIGN.LEFT, first=False, italic=False):
    p = tf.paragraphs[0] if first and not tf.paragraphs[0].runs else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(space_after)
    r = p.add_run()
    set_run(r, text, size, color, bold, font, italic=italic)
    return p


def rounded_rect(slide, l, t, w, h, fill=SURFACE, line_color=None, radius=0.08, line_width=1.0):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    shp.adjustments[0] = radius
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line_color is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line_color
        shp.line.width = Pt(line_width)
    shp.shadow.inherit = False
    return shp


def eyebrow(slide, text, top=Inches(0.45), color=ACCENT):
    _, tf = box(slide, Inches(0.7), top, Inches(11.9), Inches(0.4))
    para(tf, text.upper(), 13, color, bold=True, font=FONT_MONO, first=True)


def slide_title(slide, text, top=Inches(0.8), size=30, width=Inches(11.9)):
    _, tf = box(slide, Inches(0.7), top, width, Inches(1.0))
    para(tf, text, size, INK, bold=True, font=FONT_DISPLAY, first=True)


def footer(slide, text="VYBE Learn \u00b7 built for people who have real work to do, not a semester to spend"):
    _, tf = box(slide, Inches(0.7), Inches(7.08), Inches(11.9), Inches(0.32))
    para(tf, text, 9, INK_FAINT, font=FONT_MONO, first=True)


# ------------------------------------------------------------ mascot + raj

def draw_mascot(slide, cx, cy, size=Inches(1.3), mood="happy"):
    """Cx/cy = center. Blob body, two eyes, a smile, a small antenna -
    same silhouette as the product's own Mascot.tsx, in shapes not pixels."""
    half = Emu(int(size / 2))
    l, t = Emu(cx - half), Emu(cy - half)
    body = rounded_rect(slide, l, t, size, size, fill=None, line_color=ACCENT, radius=0.42, line_width=3.0)

    eye_r = Emu(int(size * 0.045))
    eye_dx = Emu(int(size * 0.16))
    eye_dy = Emu(int(size * 0.02))
    for sign in (-1, 1):
        ex = Emu(cx + sign * eye_dx - eye_r)
        ey = Emu(cy + eye_dy - eye_r)
        e = slide.shapes.add_shape(MSO_SHAPE.OVAL, ex, ey, Emu(eye_r * 2), Emu(eye_r * 2))
        e.fill.solid()
        e.fill.fore_color.rgb = INK if mood != "confused" else WARN
        _noline(e)

    # smile: a thin flattened arc built from a rounded-rectangle sliver
    smile_w = Emu(int(size * 0.26))
    smile_h = Emu(int(size * 0.10))
    sx = Emu(cx - smile_w // 2)
    sy = Emu(cy + int(size * 0.16))
    if mood == "confused":
        sm = rounded_rect(slide, sx, Emu(sy - smile_h), smile_w, smile_h, fill=None, line_color=WARN, radius=1.0, line_width=2.5)
    else:
        sm = rounded_rect(slide, sx, sy, smile_w, smile_h, fill=None, line_color=ACCENT, radius=1.0, line_width=2.5)
    sm.rotation = 180 if mood != "confused" else 0

    # antenna
    ant_top = Emu(t - int(size * 0.14))
    conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(cx + int(size * 0.12)), t, Emu(cx + int(size * 0.22)), ant_top)
    conn.line.color.rgb = ACCENT
    conn.line.width = Pt(2.5)
    dot_r = Emu(int(size * 0.035))
    dot = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, Emu(cx + int(size * 0.22) - dot_r), Emu(ant_top - dot_r), Emu(dot_r * 2), Emu(dot_r * 2)
    )
    dot.fill.solid()
    dot.fill.fore_color.rgb = ACCENT
    _noline(dot)
    return body


def speech_bubble(slide, l, t, w, h, text, size=13, color=INK, tail="bl"):
    shp = rounded_rect(slide, l, t, w, h, fill=SURFACE_RAISED, line_color=LINE, radius=0.18, line_width=1.0)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.18)
    tf.margin_right = Inches(0.18)
    tf.margin_top = Inches(0.1)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    para(tf, text, size, color, italic=True, space_after=0, first=True)
    tail_size = Inches(0.22)
    tx = Emu(l + Inches(0.35)) if "l" in tail else Emu(l + w - Inches(0.55))
    ty = Emu(t + h - Inches(0.02))
    tri = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, tx, ty, tail_size, tail_size)
    tri.rotation = 180
    tri.fill.solid()
    tri.fill.fore_color.rgb = SURFACE_RAISED
    _noline(tri)
    return shp


def draw_person(slide, cx, top, scale=1.0, shirt=RAJ_SHIRT, mood="worried"):
    """Small abstract businessman: head + shoulders, enough to read as
    'a person', not a mascot - keeps Raj visually distinct from VYBE."""
    head_r = Inches(0.35 * scale)
    hl = Emu(cx - int(head_r))
    ht = top
    head = slide.shapes.add_shape(MSO_SHAPE.OVAL, hl, ht, Emu(int(head_r * 2)), Emu(int(head_r * 2)))
    head.fill.solid()
    head.fill.fore_color.rgb = RAJ_SKIN
    _noline(head)

    body_w = Inches(1.15 * scale)
    body_h = Inches(0.85 * scale)
    bl = Emu(cx - int(body_w) // 2)
    bt = Emu(int(ht) + int(head_r * 2) - Inches(0.06 * scale))
    body = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, bl, bt, body_w, body_h)
    body.adjustments[0] = 0.35
    body.fill.solid()
    body.fill.fore_color.rgb = shirt
    _noline(body)

    eye_r = Emu(int(Inches(0.035 * scale)))
    for sign in (-1, 1):
        ex = Emu(cx + sign * int(Inches(0.11 * scale)) - eye_r)
        ey = Emu(int(ht) + int(head_r * 1.1) - eye_r)
        e = slide.shapes.add_shape(MSO_SHAPE.OVAL, ex, ey, Emu(eye_r * 2), Emu(eye_r * 2))
        e.fill.solid()
        e.fill.fore_color.rgb = RGBColor(0x2A, 0x20, 0x18)
        _noline(e)

    brow_color = FAIL if mood == "worried" else GOOD
    for sign in (-1, 1):
        bw = Inches(0.09 * scale)
        bl2 = Emu(cx + sign * int(Inches(0.14 * scale)) - int(bw) // 2)
        bt2 = Emu(int(ht) + int(head_r * 0.75))
        brow = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, bl2, bt2, bw, Emu(int(Inches(0.02))))
        brow.rotation = -15 * sign if mood == "worried" else 10 * sign
        brow.fill.solid()
        brow.fill.fore_color.rgb = RGBColor(0x2A, 0x20, 0x18)
        _noline(brow)
    return body


def x_o_badge(slide, l, t, size, ok):
    color = GOOD if ok else FAIL
    shp = slide.shapes.add_shape(MSO_SHAPE.OVAL, l, t, size, size)
    shp.fill.solid()
    shp.fill.fore_color.rgb = SURFACE
    shp.line.color.rgb = color
    shp.line.width = Pt(2.5)
    shp.shadow.inherit = False
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    set_run(r, "\u2713" if ok else "\u2717", 20, color, bold=True)
    return shp


# ============================================================ SLIDE 1: cold open
s = add_slide()
draw_mascot(s, Inches(6.67), Inches(2.9), size=Inches(2.0))
_, tf = box(s, Inches(2.5), Inches(4.6), Inches(8.3), Inches(0.9))
para(tf, "Hi. I'm Vy.", 34, INK, bold=True, font=FONT_DISPLAY, align=PP_ALIGN.CENTER, first=True)
_, tf = box(s, Inches(2.0), Inches(5.35), Inches(9.3), Inches(0.9))
para(
    tf,
    "I'm going to show you why VYBE Learn exists \u2014 and I promise it starts with a spreadsheet, not a syllabus.",
    16, INK_SOFT, align=PP_ALIGN.CENTER, first=True,
)
_, tf = box(s, Inches(2.0), Inches(6.4), Inches(9.3), Inches(0.5))
para(tf, "VYBE LEARN", 15, ACCENT, bold=True, font=FONT_MONO, align=PP_ALIGN.CENTER, first=True)


# ============================================================ SLIDE 2: meet raj
s = add_slide()
eyebrow(s, "Scene 1 \u2014 Meet Raj")
slide_title(s, "This is Raj. He runs a 12-person sales team.")
draw_person(s, Inches(3.0), Inches(2.3), scale=1.6, mood="worried")
speech_bubble(
    s, Inches(4.3), Inches(2.3), Inches(6.5), Inches(1.5),
    "\u201cMy sales spreadsheet has three date formats, half my city "
    "names are misspelled, and I don't even know where deal values go missing.\u201d",
    size=15,
)
_, tf = box(s, Inches(0.7), Inches(5.1), Inches(11.9), Inches(1.6))
para(
    tf,
    "Raj isn't a data scientist. He's never needed to be \u2014 until now. His business runs on this "
    "spreadsheet, and right now, he doesn't trust a single number in it.",
    16, INK_SOFT, first=True,
)
draw_mascot(s, Inches(11.5), Inches(6.4), size=Inches(0.8))
footer(s)


# ============================================================ SLIDE 3: the dilemma
s = add_slide()
eyebrow(s, "Scene 2 \u2014 The dilemma")
slide_title(s, "Raj has exactly two options. Both are bad.")

optA_l = Inches(0.9)
optB_l = Inches(7.0)
opt_w = Inches(5.4)
opt_t = Inches(1.9)
opt_h = Inches(3.6)

rounded_rect(s, optA_l, opt_t, opt_w, opt_h, fill=SURFACE, line_color=LINE)
x_o_badge(s, Emu(optA_l + Inches(0.25)), Emu(opt_t + Inches(0.25)), Inches(0.5), ok=False)
_, tf = box(s, Emu(optA_l + Inches(0.9)), Emu(opt_t + Inches(0.2)), Inches(4.2), Inches(0.7))
para(tf, "Hire a data analyst", 18, INK, bold=True, font=FONT_DISPLAY, first=True)
_, tf = box(s, Emu(optA_l + Inches(0.3)), Emu(opt_t + Inches(1.1)), Inches(4.8), Inches(2.3))
for line in [
    "Real salary, every month, for one spreadsheet",
    "Weeks of onboarding before they even touch his data",
    "He still doesn't understand his own numbers",
    "Doesn't scale \u2014 next messy file, same cost again",
]:
    para(tf, "\u2022 " + line, 13, INK_SOFT, space_after=8, first=(line == "Real salary, every month, for one spreadsheet"))

rounded_rect(s, optB_l, opt_t, opt_w, opt_h, fill=SURFACE, line_color=LINE)
x_o_badge(s, Emu(optB_l + Inches(0.25)), Emu(opt_t + Inches(0.25)), Inches(0.5), ok=False)
_, tf = box(s, Emu(optB_l + Inches(0.9)), Emu(opt_t + Inches(0.2)), Inches(4.2), Inches(0.7))
para(tf, "Learn data science himself", 18, INK, bold=True, font=FONT_DISPLAY, first=True)
_, tf = box(s, Emu(optB_l + Inches(0.3)), Emu(opt_t + Inches(1.1)), Inches(4.8), Inches(2.3))
for line in [
    "A full course built for future data scientists, not a sales manager",
    "80% of it \u2014 theory, syntax, textbook datasets \u2014 he'll never use",
    "Months before he can even open his own file with confidence",
    "He has a business to run today, not a semester to spare",
]:
    para(tf, "\u2022 " + line, 13, INK_SOFT, space_after=8, first=(line.startswith("A full course")))

draw_mascot(s, Inches(6.67), Inches(6.15), size=Inches(0.9), mood="confused")
_, tf = box(s, Inches(4.5), Inches(6.65), Inches(4.3), Inches(0.5))
para(tf, "\u201cThere has to be a third way\u2026\u201d", 13, INK_FAINT, italic=True, align=PP_ALIGN.CENTER, first=True)


# ============================================================ SLIDE 4: enter vybe
s = add_slide()
draw_mascot(s, Inches(2.6), Inches(2.6), size=Inches(1.8))
speech_bubble(
    s, Inches(4.0), Inches(1.5), Inches(8.4), Inches(2.1),
    "\u201cRaj doesn't need to learn everything. He needs an agent that already knows how \u2014 "
    "and shows him only the part that matters, on his own data.\u201d",
    size=18, tail="l",
)
_, tf = box(s, Inches(0.9), Inches(4.1), Inches(11.5), Inches(0.6))
para(tf, "That's the whole idea behind VYBE Learn.", 22, INK, bold=True, font=FONT_DISPLAY, first=True)

pillars = [
    ("The agent does the real work", "Cleans, verifies, and models Raj's actual spreadsheet \u2014 for real, not a demo."),
    ("Raj learns just enough", "Bite-sized, grounded in his own numbers \u2014 not a generic 40-hour syllabus."),
    ("He keeps his job, not switches careers", "20 minutes with his own data beats 6 months of a course he'll abandon."),
]
pw = Inches(3.83)
px = Inches(0.9)
py = Inches(5.0)
for i, (h, b) in enumerate(pillars):
    l = Emu(px + i * (pw + Inches(0.1)))
    shp = rounded_rect(s, l, py, pw, Inches(1.7), fill=SURFACE)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.18)
    tf.margin_top = Inches(0.15)
    para(tf, h, 14, INK, bold=True, font=FONT_DISPLAY, space_after=5, first=True)
    para(tf, b, 11.5, INK_SOFT, space_after=0)


# ============================================================ SLIDE 5: watch it work
s = add_slide()
eyebrow(s, "Scene 3 \u2014 Watch it work")
slide_title(s, "Raj uploads his spreadsheet. Here's what happens.")

beats = [
    ("GOAL", "Fix the missing deal values without quietly distorting the sales numbers.", ACCENT),
    ("DECISION", "Try the obvious fix first \u2014 fill blanks with the average.", INK_SOFT),
    ("ACTION", "impute_median runs on deal_value.", INK_SOFT),
    ("RESULT", "Distorts the shape of the data by 21.3% \u2014 fails the agent's own check.", FAIL),
    ("ADAPTATION", "Escalates to a smarter fix: impute_knn, which looks at similar rows instead of one flat number.", WARN),
    ("OUTCOME", "Shape distorted by only 7.6% \u2014 kept. Raj sees exactly why, in one plain sentence.", GOOD),
]
by = Inches(1.75)
bh = Inches(0.78)
for i, (tag, text, color) in enumerate(beats):
    top = Emu(by + i * bh)
    _, tf = box(s, Inches(0.7), top, Inches(1.7), bh)
    para(tf, tag, 11, color, bold=True, font=FONT_MONO, first=True)
    _, tf = box(s, Inches(2.5), top, Inches(10.0), bh)
    para(tf, text, 13, INK, first=True)
    if i < len(beats) - 1:
        conn = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(0.95), Emu(top + bh - Inches(0.03)), Inches(0.95), Emu(top + bh + Inches(0.06)))
        conn.line.color.rgb = LINE
        conn.line.width = Pt(1.5)
footer(s, "This exact sequence is a live run on the sample dataset, not a scripted screen \u2014 it re-runs on any file Raj uploads.")


# ============================================================ SLIDE 6: raj now
s = add_slide()
draw_mascot(s, Inches(2.2), Inches(2.1), size=Inches(1.3))
draw_person(s, Inches(4.6), Inches(1.7), scale=1.4, mood="happy")
speech_bubble(
    s, Inches(6.1), Inches(1.7), Inches(6.1), Inches(1.7),
    "\u201cI didn't just get a clean file. I understand why every fix was made \u2014 and I could explain it "
    "to my own team.\u201d \u2014 Raj, 20 minutes later",
    size=14,
)

_, tf = box(s, Inches(0.9), Inches(3.7), Inches(11.5), Inches(0.6))
para(tf, "In one sitting, Raj walks away with:", 20, INK, bold=True, font=FONT_DISPLAY, first=True)

outcomes = [
    "A clean dataset, with every decision explained in plain language",
    "A trained model for his own sales data, not a textbook example",
    "Real, working knowledge of the 4 issues his own data actually had",
    "A portfolio-ready analysis he can hand to his team \u2014 today",
]
_, tf = box(s, Inches(0.9), Inches(4.4), Inches(11.0), Inches(2.4))
for i, o in enumerate(outcomes):
    para(tf, "\u2713  " + o, 15, GOOD if i == 0 else INK_SOFT, space_after=10, first=(i == 0))
footer(s)


# ============================================================ SLIDE 7: brief
s = add_slide()
eyebrow(s, "Problem & Solution Brief")
slide_title(s, "The same story, in submission language")

items = [
    ("Problem statement", "Non-technical professionals have real data they need to understand, but only two "
     "extremes exist: hire it out, or take a generic course built for future data scientists."),
    ("Target users", "Small-business owners, sales/ops/HR managers, students \u2014 anyone with their own messy "
     "spreadsheet and zero interest in becoming a full-time data scientist."),
    ("Why this needs to be agentic", "A fixed script applies one rule and hopes. A chatbot can describe a fix "
     "but can't check if it worked. This system observes \u2192 decides \u2192 acts \u2192 evaluates \u2192 adapts, on real "
     "measured thresholds \u2014 the same loop for cleaning and for model selection."),
    ("Proposed solution", "VYBE Learn: a deterministic agent that cleans, verifies, and models the learner's "
     "own dataset, narrated by an AI tutor \u2014 gamified so understanding is earned a step at a time, never "
     "dumped as a wall of theory."),
    ("Expected impact", "Turns \u201cI have to hire this out or give up\u201d into \u201cI understood my own data in one "
     "sitting\u201d \u2014 for the huge population of people data science was never built for."),
]
iy = Inches(1.65)
for i, (h, b) in enumerate(items):
    ih = Inches(1.02)
    top = Emu(iy + i * ih)
    _, tf = box(s, Inches(0.7), top, Inches(2.5), ih)
    para(tf, h, 13, ACCENT, bold=True, font=FONT_DISPLAY, first=True)
    _, tf = box(s, Inches(3.3), top, Inches(9.3), ih)
    para(tf, b, 12.5, INK_SOFT, first=True)
draw_mascot(s, Inches(12.4), Inches(0.75), size=Inches(0.7))


# ============================================================ SLIDE 8: architecture
s = add_slide()
eyebrow(s, "System Architecture")
slide_title(s, "Nine components, mapped honestly")

arch = [
    ("Agent / controller", "loop.py's decision loop (cleaning) + model_selector.py's loop (modeling) + web/chat.py's tutor-tier orchestration"),
    ("Tools", "actions.py transforms (impute_median, impute_knn, normalize_categories\u2026) \u2014 the agent's real callable actions"),
    ("External systems", "Google Gemini API (direct + via ADK), GitHub, Render + Vercel hosting"),
    ("Memory / state", "In-memory Session (per learner) \u2014 dataset, guesses, points; ADK's own profile/XP store; localStorage Notes"),
    ("Retrieval", "Lightweight only \u2014 keyword-matched FAQ fallback, no vector DB. Grounding comes from real dataset stats, not documents."),
    ("Planning", "The candidate ladder per issue type \u2014 simplest strategy first, escalate only on a measured failure"),
    ("Evaluation / verification", "stats.py + downstream.py \u2014 skew-shift thresholds, cross-val R\u00b2, residual-pattern checks, real downstream tasks"),
    ("Human interaction", "Learner predicts the agent's fix before seeing it, takes quizzes, chats with the AI Mentor, can Skip any stage"),
    ("Failure handling", "Honest-failure path (flagged for a human when every strategy fails) + 3-tier tutor fallback that never hard-errors"),
]
ay = Inches(1.65)
ah = Inches(0.56)
for i, (h, b) in enumerate(arch):
    top = Emu(ay + i * ah)
    _, tf = box(s, Inches(0.7), top, Inches(2.7), ah)
    para(tf, h, 12, ACCENT, bold=True, font=FONT_MONO, first=True)
    _, tf = box(s, Inches(3.5), top, Inches(9.1), ah)
    para(tf, b, 11.5, INK_SOFT, first=True)
footer(s, "Full diagram (layered system map + agentic loop) in the pitch_deck_reference artifact / VYBE_Learn_Pitch_Deck.pptx")


# ============================================================ SLIDE 9: source code
s = add_slide()
eyebrow(s, "Source Code")
slide_title(s, "Two public repos, both live")

repos = [
    ("Main app \u2014 frontend + backend", "github.com/kanishkaanand0911-dotcom/personalized-data-science-tutor", "branch: vybe-learn-frontend",
     "React 19 + Vite frontend, FastAPI backend, the deterministic agent core, README with setup + architecture notes."),
    ("ADK tutor companion", "github.com/Bhoomimehta14/vybe-learn-adk-tutor", "branch: main",
     "Google ADK-hosted multi-agent tutor (profiler + gamification), README with its own setup instructions."),
]
ry = Inches(1.8)
for i, (h, url, br, desc) in enumerate(repos):
    top = Emu(ry + i * Inches(2.2))
    shp = rounded_rect(s, Inches(0.7), top, Inches(11.9), Inches(2.0), fill=SURFACE)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.3)
    tf.margin_top = Inches(0.2)
    para(tf, h, 16, INK, bold=True, font=FONT_DISPLAY, space_after=4, first=True)
    para(tf, url, 13, ACCENT, font=FONT_MONO, space_after=2)
    para(tf, br, 10.5, INK_FAINT, font=FONT_MONO, space_after=8)
    para(tf, desc, 12, INK_SOFT, space_after=0)
_, tf = box(s, Inches(0.7), Inches(6.3), Inches(11.9), Inches(0.6))
para(tf, "Each repo's README covers: dependencies, environment variables (.env.example provided), and run commands.", 11.5, INK_FAINT, italic=True, first=True)


# ============================================================ SLIDE 10: demo video
s = add_slide()
eyebrow(s, "Demo Video \u2014 to record", color=WARN)
slide_title(s, "3\u20135 min screen capture \u2014 not yet recorded")

_, tf = box(s, Inches(0.7), Inches(1.55), Inches(11.9), Inches(0.7))
para(
    tf,
    "Everything below already happened live in this session \u2014 this slide is the shot list, using Scene 3 "
    "(slide 5) as the script.",
    13, INK_SOFT, first=True,
)

checklist = [
    ("Goal", "Show Raj's messy sample dataset loading \u2014 missing values, mixed date formats, inconsistent labels."),
    ("Decision", "Guess a cleaning strategy before revealing the agent's choice (the app's own predict-first flow)."),
    ("Action", "Reveal the agent's real fix \u2014 the median-imputation attempt."),
    ("Intermediate result", "Show the agent's own check failing it (21.3% distortion) and discarding it."),
    ("Adaptation", "Show the escalation to KNN imputation, and it passing (7.6%)."),
    ("Final outcome", "Jump to Final Project \u2014 the full recap, chosen model, portfolio-ready analysis."),
    ("Failure/unexpected condition (encouraged)", "Show the AI Mentor or chat gracefully degrading when a key/quota fails \u2014 the honest fallback tier, not a crash."),
]
cy = Inches(2.4)
ch = Inches(0.62)
for i, (h, b) in enumerate(checklist):
    top = Emu(cy + i * ch)
    box_shp = slide_title  # unused placeholder to keep linter calm
    chk = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.7), Emu(top + Inches(0.06)), Inches(0.28), Inches(0.28))
    chk.adjustments[0] = 0.3
    chk.fill.background()
    chk.line.color.rgb = WARN
    chk.line.width = Pt(2)
    chk.shadow.inherit = False
    _, tf = box(s, Inches(1.15), top, Inches(2.3), ch)
    para(tf, h, 12, WARN, bold=True, first=True)
    _, tf = box(s, Inches(3.5), top, Inches(9.1), ch)
    para(tf, b, 11.5, INK_SOFT, first=True)
footer(s)


# ============================================================ SLIDE 11: deployment
s = add_slide()
eyebrow(s, "Deployment / Runnable Version")
slide_title(s, "Live right now \u2014 no setup needed for judges")

links = [
    ("Web application", "vybelearn.vercel.app", "The full learner experience \u2014 upload a CSV or try the sample."),
    ("Backend API", "personalized-data-science-tutor.onrender.com", "FastAPI service the frontend calls \u2014 /api/docs for the raw endpoints."),
    ("ADK tutor service", "vybe-learn.onrender.com", "The multi-agent tutor backing the richer AI Mentor tier."),
]
ly = Inches(1.8)
for i, (h, url, b) in enumerate(links):
    top = Emu(ly + i * Inches(1.15))
    shp = rounded_rect(s, Inches(0.7), top, Inches(11.9), Inches(1.0), fill=SURFACE)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.3)
    tf.margin_top = Inches(0.13)
    p = tf.paragraphs[0]
    r = p.add_run()
    set_run(r, h + "   ", 14, INK, bold=True, font=FONT_DISPLAY)
    r2 = p.add_run()
    set_run(r2, url, 13, ACCENT, font=FONT_MONO)
    p2 = tf.add_paragraph()
    p2.space_before = Pt(3)
    r3 = p2.add_run()
    set_run(r3, b, 11.5, INK_SOFT)

_, tf = box(s, Inches(0.7), Inches(5.5), Inches(11.9), Inches(1.2))
para(tf, "Fallback \u2014 local setup (both repos have README instructions):", 13, INK, bold=True, first=True)
para(tf, "pip install -r requirements.txt  &&  uvicorn web.api:app --reload   (backend)      cd web/ui && npm install && npm run dev   (frontend)", 11, INK_SOFT, font=FONT_MONO)
footer(s, "Free-tier hosting: first request after idle can take up to ~50s to wake the instance \u2014 not a bug, just Render's free plan.")


# ============================================================ SLIDE 12: closing
s = add_slide()
draw_mascot(s, Inches(6.67), Inches(2.6), size=Inches(1.8))
_, tf = box(s, Inches(1.5), Inches(4.2), Inches(10.3), Inches(0.8))
para(tf, "Raj didn't need a course. He needed a guide.", 26, INK, bold=True, font=FONT_DISPLAY, align=PP_ALIGN.CENTER, first=True)
_, tf = box(s, Inches(1.5), Inches(5.0), Inches(10.3), Inches(0.6))
para(tf, "That's what we built.", 16, INK_SOFT, align=PP_ALIGN.CENTER, first=True)
_, tf = box(s, Inches(1.5), Inches(6.0), Inches(10.3), Inches(0.8))
para(tf, "vybelearn.vercel.app", 15, ACCENT, bold=True, font=FONT_MONO, align=PP_ALIGN.CENTER, first=True)
para(tf, "github.com/kanishkaanand0911-dotcom/personalized-data-science-tutor", 11, INK_FAINT, font=FONT_MONO, align=PP_ALIGN.CENTER)


out_path = r"C:\Users\bhoom\Downloads\project\project\VYBE_Learn_Story_Pitch.pptx"
prs.save(out_path)
print("Saved:", out_path)
