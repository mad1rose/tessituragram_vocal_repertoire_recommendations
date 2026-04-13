"""
Build the CADSCOM 2026 conference presentation (.pptx).

Run from the repo root:
    python CADSCOM_PRESENTATION/build_presentation.py

Requires: python-pptx, Pillow
"""

from __future__ import annotations

import os
import pathlib
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "CADSCOM_PRESENTATION" / "CADSCOM_2026_Presentation.pptx"

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
BURGUNDY   = RGBColor(0x6B, 0x1D, 0x2A)
CREAM      = RGBColor(0xFD, 0xF6, 0xEC)
GOLD       = RGBColor(0xC5, 0x9B, 0x3F)
CHARCOAL   = RGBColor(0x2D, 0x2D, 0x2D)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GOLD = RGBColor(0xF5, 0xE6, 0xC4)
SOFT_GRAY  = RGBColor(0x88, 0x88, 0x88)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_slide_bg(slide, color: RGBColor):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_burgundy_header(slide, height=Inches(1.15)):
    shp = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), SLIDE_W, height,
    )
    shp.fill.solid()
    shp.fill.fore_color.rgb = BURGUNDY
    shp.line.fill.background()
    return shp


def _add_gold_accent_line(slide, top, width=Inches(2.5)):
    left = Inches(0.75)
    shp = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, left, top, width, Inches(0.04),
    )
    shp.fill.solid()
    shp.fill.fore_color.rgb = GOLD
    shp.line.fill.background()


def _add_textbox(slide, left, top, width, height):
    return slide.shapes.add_textbox(left, top, width, height)


def _set_font(run, size=Pt(22), bold=False, italic=False,
              color=CHARCOAL, name="Calibri"):
    run.font.size = size
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = name


def _add_title_in_header(slide, text, top=Inches(0.25)):
    tb = _add_textbox(slide, Inches(0.75), top, Inches(11.5), Inches(0.7))
    p = tb.text_frame.paragraphs[0]
    run = p.add_run()
    run.text = text
    _set_font(run, Pt(32), bold=True, color=WHITE)
    p.alignment = PP_ALIGN.LEFT
    return tb


def _add_body_text(slide, lines: list[str], left=Inches(0.75),
                   top=Inches(1.5), width=Inches(11.8), height=Inches(5.5),
                   size=Pt(22), bullet=True, spacing=Pt(8)):
    tb = _add_textbox(slide, left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        run = p.add_run()
        run.text = ("  \u2022  " + line) if bullet else line
        _set_font(run, size, color=CHARCOAL)
        p.space_after = spacing
        p.alignment = PP_ALIGN.LEFT
    return tb


def _add_big_quote(slide, text, top=Inches(2.0)):
    tb = _add_textbox(slide, Inches(1.2), top, Inches(10.9), Inches(3.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    _set_font(run, Pt(34), italic=True, color=BURGUNDY)
    return tb


def _add_image_centered(slide, img_path: str, top=Inches(1.6),
                        max_w=Inches(11.0), max_h=Inches(5.3)):
    from PIL import Image as PILImage
    with PILImage.open(img_path) as im:
        iw, ih = im.size
    aspect = iw / ih
    w = max_w
    h = int(w / aspect)
    if h > max_h:
        h = max_h
        w = int(h * aspect)
    left = int((SLIDE_W - w) / 2)
    slide.shapes.add_picture(img_path, left, top, w, h)


def _add_notes(slide, text: str):
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = text


def _standard_slide(prs, title, bullets, notes, **kw):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    _set_slide_bg(slide, CREAM)
    _add_burgundy_header(slide)
    _add_title_in_header(slide, title)
    _add_gold_accent_line(slide, Inches(1.18))
    if bullets:
        _add_body_text(slide, bullets, **kw)
    _add_notes(slide, notes)
    return slide

# ---------------------------------------------------------------------------
# Slide builders
# ---------------------------------------------------------------------------

def slide_01_title(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, BURGUNDY)

    # Gold accent lines
    for y in (Inches(1.8), Inches(5.6)):
        shp = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(2), y, Inches(9.333), Inches(0.04),
        )
        shp.fill.solid()
        shp.fill.fore_color.rgb = GOLD
        shp.line.fill.background()

    # Title
    tb = _add_textbox(slide, Inches(1), Inches(2.1), Inches(11.333), Inches(2.0))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = "Content-Based Vocal Repertoire Ranking Framework\nUsing Duration-Weighted Pitch Distributions"
    _set_font(run, Pt(34), bold=True, color=WHITE)

    # Authors
    tb2 = _add_textbox(slide, Inches(1), Inches(4.4), Inches(11.333), Inches(1.0))
    p2 = tb2.text_frame.paragraphs[0]
    p2.alignment = PP_ALIGN.CENTER
    run2 = p2.add_run()
    run2.text = "Madeline Johnson, Flint Million, Rajeev Bukralia"
    _set_font(run2, Pt(24), color=LIGHT_GOLD)

    # Affiliation
    tb3 = _add_textbox(slide, Inches(1), Inches(5.05), Inches(11.333), Inches(0.5))
    p3 = tb3.text_frame.paragraphs[0]
    p3.alignment = PP_ALIGN.CENTER
    run3 = p3.add_run()
    run3.text = "Minnesota State University, Mankato"
    _set_font(run3, Pt(20), italic=True, color=LIGHT_GOLD)

    # Conference tag
    tb4 = _add_textbox(slide, Inches(1), Inches(5.9), Inches(11.333), Inches(0.5))
    p4 = tb4.text_frame.paragraphs[0]
    p4.alignment = PP_ALIGN.CENTER
    run4 = p4.add_run()
    run4.text = "CADSCOM 2026"
    _set_font(run4, Pt(20), bold=True, color=GOLD)

    _add_notes(slide, (
        "[~15 seconds]\n\n"
        "Good morning/afternoon, everyone. My name is Madeline Johnson, "
        "and I'm here with my co-authors Flint Million and Rajeev Bukralia "
        "from Minnesota State University, Mankato. Today I'm going to talk "
        "about how we can use data from musical scores to help singers find "
        "repertoire that actually fits their voice."
    ))


def slide_02_hook(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, CREAM)

    _add_big_quote(slide,
        "\u201cHave you ever wondered how a singer decides\n"
        "which songs are safe to sing?\u201d",
        top=Inches(1.8),
    )

    tb = _add_textbox(slide, Inches(1.5), Inches(4.5), Inches(10.3), Inches(2.0))
    tf = tb.text_frame
    tf.word_wrap = True
    lines = [
        "For singers, choosing the wrong piece is not just an inconvenience.",
        "It is an injury risk.",
        "What if we could use data to help?",
    ]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = line
        if i == 1:
            _set_font(run, Pt(26), bold=True, color=BURGUNDY)
        elif i == 2:
            _set_font(run, Pt(26), italic=True, color=GOLD)
        else:
            _set_font(run, Pt(24), color=CHARCOAL)
        p.space_after = Pt(12)

    _add_notes(slide, (
        "[~45 seconds]\n\n"
        "Let me start with a question. Have you ever wondered how a singer "
        "decides which songs are safe to sing? If you're not a singer, that "
        "might sound like an odd question. But for singers, choosing the "
        "wrong piece isn't just a matter of preference. It can lead to real "
        "vocal injury. Research shows that misalignment between a piece's "
        "demands and a singer's capabilities raises the risk of strain "
        "(Apfelbach, 2022; Phyland et al., 1999). In practice, singers and "
        "voice teachers rely on intuition, trial and error, or vocal "
        "classification systems that aren't consistently defined. So what if "
        "we could use data to make this process more objective and safer?"
    ))


def slide_03_gap(prs):
    notes = (
        "[~45 seconds]\n\n"
        "Here's the gap. Tools already exist that can analyze a song's "
        "tessitura -- where the voice sits in a piece. For example, a "
        "program called Tessa can extract a tessitura profile from a "
        "digital score. But these tools only work AFTER you've already "
        "picked a piece. They help you evaluate a choice you've made -- "
        "they don't help you discover new pieces that are likely to fit. "
        "And here's where my background matters. I was a vocal performance "
        "major before pursuing my master's in data science. I lived this "
        "problem as a singer. I know what it's like to pick a piece that "
        "doesn't sit well in your voice. And as a data scientist, I asked: "
        "can we build a system that recommends songs based on where they "
        "actually sit, not just their highest and lowest notes?"
    )
    _standard_slide(prs, "The Gap", [
        "Current tools (like Tessa) analyze a piece after you already picked it \u2014\n"
        "they do not recommend new pieces likely to fit.",
        "Filtering by range alone is misleading: it shows the extremes,\n"
        "not where the voice spends most of its time.",
        "As a former performance major, I lived this problem.\n"
        "As a data scientist, I built a solution.",
    ], notes)


def slide_04_tessitura(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, CREAM)
    _add_burgundy_header(slide)
    _add_title_in_header(slide, "What Is Tessitura?")
    _add_gold_accent_line(slide, Inches(1.18))

    lines_left = [
        "Tessitura is NOT just the highest and lowest notes.",
        "It is where the voice lives in a piece \u2014 the pitches\nthat receive the most singing time.",
        "Duration matters: sustaining a high note for 8 beats\nis far more demanding than touching it briefly.",
    ]
    _add_body_text(slide, lines_left, top=Inches(1.5), width=Inches(6.5),
                   height=Inches(3.5), size=Pt(22))

    # Analogy callout box
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.75), Inches(5.0), Inches(11.8), Inches(1.8),
    )
    shp.fill.solid()
    shp.fill.fore_color.rgb = LIGHT_GOLD
    shp.line.color.rgb = GOLD
    shp.line.width = Pt(1.5)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.3)
    tf.margin_top = Inches(0.2)
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = (
        "Analogy for non-musicians:  Think of it like your daily commute vs. the farthest "
        "you\u2019ve ever driven. What matters for wear-and-tear is the daily average, "
        "not the one-time extreme."
    )
    _set_font(run, Pt(20), italic=True, color=CHARCOAL)
    p.alignment = PP_ALIGN.LEFT

    _add_notes(slide, (
        "[~60 seconds]\n\n"
        "Before we go further, let me explain a music concept that's "
        "central to this research: tessitura. If you look at a piece of "
        "vocal music, you can see the highest note and the lowest note -- "
        "that's the range. But range alone doesn't tell you where the voice "
        "SPENDS MOST OF ITS TIME. That's tessitura. A piece might have one "
        "very high note at the climax, but if the rest of the piece sits "
        "comfortably in the middle of the voice, it's very different from a "
        "piece that lives up high the entire time. Duration matters too: "
        "holding a high B-flat for eight beats is much more demanding than "
        "touching it for a sixteenth note. For those of you who aren't "
        "musicians, think of it like driving. What matters for the wear on "
        "your car isn't the farthest you've ever driven -- it's your daily "
        "commute. Tessitura is the voice's daily commute."
    ))


def slide_05_tessituragram(prs):
    notes = (
        "[~45 seconds]\n\n"
        "So how do we capture tessitura computationally? With something "
        "called a tessituragram. It's essentially a fingerprint of a song. "
        "On one axis you have every pitch in the vocal line, and on the "
        "other you have how much total singing time is spent on that pitch, "
        "weighted by note duration. Longer notes count more because "
        "sustaining a pitch is more demanding than a passing tone. We parse "
        "digital sheet music -- MusicXML files -- using a toolkit called "
        "music21, and we build one of these profiles for every vocal line "
        "in our library. So the question becomes: can we use these "
        "fingerprints to match songs to singers?"
    )
    _standard_slide(prs, "What Is a Tessituragram?", [
        "A tessituragram is a fingerprint of a song \u2014 a histogram\n"
        "of how much singing time falls on each pitch.",
        "Built from MusicXML scores using music21:\n"
        "MIDI pitch \u2192 total duration in quarter-note beats.",
        "Duration-weighted: longer notes count more, because\n"
        "sustaining a pitch is more demanding than a passing tone.",
        "Can we use these fingerprints to match songs to singers?",
    ], notes)


def slide_06_pipeline(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, CREAM)
    _add_burgundy_header(slide)
    _add_title_in_header(slide, "The Pipeline")
    _add_gold_accent_line(slide, Inches(1.18))

    steps = [
        ("Singer\nPreferences", "The singer provides\nrange, favorites,\nand avoids"),
        ("Range\nFilter", "Remove songs\noutside the\nsinger\u2019s range"),
        ("Ideal Profile\nConstruction", "Build a target\npitch-duration\nvector"),
        ("Cosine\nSimilarity\nScoring", "Score each song\nby similarity\nminus avoid penalty"),
        ("Ranked\nSong List", "Songs ordered\nfrom best match\nto worst"),
    ]

    box_w = Inches(2.0)
    box_h = Inches(2.2)
    gap = Inches(0.45)
    total_w = len(steps) * box_w + (len(steps) - 1) * gap
    start_left = int((SLIDE_W - total_w) / 2)
    top_box = Inches(2.0)
    top_desc = Inches(4.4)

    for i, (label, desc) in enumerate(steps):
        left = start_left + i * (box_w + gap)

        # Box
        shp = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, left, top_box, box_w, box_h,
        )
        shp.fill.solid()
        shp.fill.fore_color.rgb = BURGUNDY
        shp.line.fill.background()
        tf = shp.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.1)
        tf.margin_right = Inches(0.1)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = label
        _set_font(run, Pt(18), bold=True, color=WHITE)
        shp.text_frame.paragraphs[0].space_before = Pt(24)

        # Description underneath
        tb = _add_textbox(slide, left, top_desc, box_w, Inches(1.6))
        tf2 = tb.text_frame
        tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.alignment = PP_ALIGN.CENTER
        run2 = p2.add_run()
        run2.text = desc
        _set_font(run2, Pt(16), color=CHARCOAL)

        # Arrow between boxes
        if i < len(steps) - 1:
            arrow_left = left + box_w
            arrow_top = top_box + box_h / 2 - Inches(0.15)
            arr = slide.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW, arrow_left, arrow_top,
                gap, Inches(0.3),
            )
            arr.fill.solid()
            arr.fill.fore_color.rgb = GOLD
            arr.line.fill.background()

    # Bottom summary
    tb = _add_textbox(slide, Inches(1), Inches(6.2), Inches(11.333), Inches(0.8))
    p = tb.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = "The singer tells us three things: range, favorite pitches, and pitches to avoid. We do the rest."
    _set_font(run, Pt(22), italic=True, color=BURGUNDY)

    _add_notes(slide, (
        "[~45 seconds]\n\n"
        "Here's the big picture of how the system works. It's a pipeline "
        "with five steps. First, the singer provides three inputs: their "
        "comfortable vocal range -- the lowest and highest notes they can "
        "sing -- their favorite pitches, and pitches they want to avoid. "
        "Second, we filter out any song whose written range goes beyond "
        "what the singer specified. Third, we construct an ideal pitch "
        "profile from those preferences -- basically a target fingerprint "
        "of what the perfect song would look like for this singer. Fourth, "
        "we score every remaining song by how closely its tessituragram "
        "matches that ideal, minus a penalty for time spent on avoided "
        "pitches. And finally, we return a ranked list from best match to "
        "worst. The singer tells us three things; we do the rest."
    ))


def slide_07_formula(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, CREAM)
    _add_burgundy_header(slide)
    _add_title_in_header(slide, "How Scoring Works")
    _add_gold_accent_line(slide, Inches(1.18))

    # Formula box
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(1.5), Inches(1.7), Inches(10.333), Inches(1.2),
    )
    shp.fill.solid()
    shp.fill.fore_color.rgb = BURGUNDY
    shp.line.fill.background()
    tf = shp.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = "final_score  =  cosine_similarity(song, ideal)  \u2212  \u03B1  \u00D7  avoid_penalty"
    _set_font(run, Pt(26), bold=True, color=WHITE, name="Consolas")

    bullets = [
        "Cosine similarity: how closely does this song\u2019s pitch fingerprint\n"
        "align with the singer\u2019s ideal profile? (1.0 = perfect match)",
        "Avoid penalty: what proportion of the song\u2019s duration is spent\n"
        "on notes the singer wants to avoid?",
        "\u03B1 (alpha = 0.5): controls how heavily we penalize avoided notes.",
    ]
    _add_body_text(slide, bullets, top=Inches(3.2), height=Inches(2.5), size=Pt(22))

    # Analogy callout
    shp2 = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.75), Inches(5.7), Inches(11.8), Inches(1.2),
    )
    shp2.fill.solid()
    shp2.fill.fore_color.rgb = LIGHT_GOLD
    shp2.line.color.rgb = GOLD
    shp2.line.width = Pt(1.5)
    tf2 = shp2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = Inches(0.3)
    tf2.margin_top = Inches(0.15)
    p2 = tf2.paragraphs[0]
    run2 = p2.add_run()
    run2.text = (
        "Analogy:  Like a restaurant recommender that matches your food preferences "
        "and subtracts points for ingredients you dislike."
    )
    _set_font(run2, Pt(20), italic=True, color=CHARCOAL)

    _add_notes(slide, (
        "[~60 seconds]\n\n"
        "So let's look at exactly how the scoring works. The final score "
        "for each song is cosine similarity between that song's "
        "tessituragram and the singer's ideal profile, minus alpha times "
        "the avoid penalty. Let me break that down. Cosine similarity "
        "measures how closely a song's pitch-duration fingerprint aligns "
        "with what the singer wants. A score of 1.0 would be a perfect "
        "match in proportional shape. The avoid penalty is the proportion "
        "of the song's total singing duration that falls on notes the "
        "singer wants to avoid. Alpha controls the trade-off -- at 0.5, "
        "we're splitting the weight evenly. Think of it like a restaurant "
        "recommender. It finds dishes that match your taste preferences and "
        "then subtracts points for ingredients you don't like. Simple idea, "
        "but the question is: does it actually work? How do we know this "
        "produces good rankings?"
    ))


def slide_08_dataset(prs):
    notes = (
        "[~45 seconds]\n\n"
        "To test this, we needed real musical data. We used the OpenScore "
        "Lieder Corpus -- a freely available, openly licensed collection of "
        "art songs. These are real scores by composers like Schubert, Clara "
        "and Robert Schumann, Debussy, and Fauré. We ran two experiments. "
        "The first used a compact library of 101 vocal lines, one per "
        "composition. The second used a much larger expanded library: 1,655 "
        "vocal lines drawn from 1,419 compositions -- about 16 times "
        "larger. Some compositions have multiple voice parts, like duets, "
        "so each vocal line is treated as its own item. These aren't made-up "
        "examples. These are real art songs that singers perform every day "
        "around the world."
    )
    _standard_slide(prs, "The Dataset", [
        "OpenScore Lieder Corpus (CC0, openly licensed)\n"
        "Real published scores: Schubert, Schumann, Debussy, Faur\u00e9, and more.",
        "Experiment 1:  101 vocal lines (one per composition) \u2014 compact library.",
        "Experiment 2:  1,655 vocal lines from 1,419 compositions (~16\u00d7 larger).\n"
        "342 lines from multi-part works, 1,313 from single-voice songs.",
        "These are not made-up examples \u2014\n"
        "these are real art songs that singers perform every day.",
    ], notes)


def slide_09_testing(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, CREAM)
    _add_burgundy_header(slide)
    _add_title_in_header(slide, "How We Tested It: Synthetic Self-Retrieval")
    _add_gold_accent_line(slide, Inches(1.18))

    # Explanation steps
    steps_text = [
        "1.  Pick a vocal line from the library.",
        "2.  Build a singer profile FROM that line\u2019s own fingerprint\n"
        "     (range, top-4 favorite pitches, bottom-2 avoid pitches).",
        "3.  Ask the system: can you find that same line among\n"
        "     hundreds of candidates?",
    ]
    _add_body_text(slide, steps_text, top=Inches(1.5), height=Inches(3.0),
                   size=Pt(22), bullet=False)

    # Baselines box
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.75), Inches(4.4), Inches(11.8), Inches(2.0),
    )
    shp.fill.solid()
    shp.fill.fore_color.rgb = LIGHT_GOLD
    shp.line.color.rgb = GOLD
    shp.line.width = Pt(1.5)
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.3)
    tf.margin_top = Inches(0.2)

    baseline_lines = [
        ("Three baselines compared:", True, False),
        ("Full model:  cosine similarity + avoid penalty (\u03B1 = 0.5)", False, False),
        ("Cosine-only:  similarity without the avoid penalty (\u03B1 = 0)", False, False),
        ("Null (random):  range filter only, then random ordering", False, False),
        ("", False, False),
        ("So what did we find?", False, True),
    ]
    for i, (text, is_bold, is_italic) in enumerate(baseline_lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        run = p.add_run()
        run.text = text
        _set_font(run, Pt(20), bold=is_bold, italic=is_italic, color=CHARCOAL)
        if is_italic:
            run.font.color.rgb = BURGUNDY

    _add_notes(slide, (
        "[~60 seconds]\n\n"
        "Now, we didn't have human judges rating songs for us. That's "
        "future work. Instead, we used a rigorous method called synthetic "
        "self-retrieval. Here's how it works. We pick a vocal line from "
        "the library. We build a singer profile directly from that line's "
        "own tessituragram: the range becomes the singer's range, the four "
        "pitches with the most singing time become the favorites, and the "
        "two pitches with the least become the avoids. Then we ask the "
        "system to rank all the remaining candidates and see where the "
        "original line ends up. If the system is working, it should rank "
        "that line very highly -- ideally first. We compared three models: "
        "the full model with the avoid penalty, cosine-only without the "
        "penalty, and a null baseline that just filters by range and then "
        "ranks randomly. So what did we find?"
    ))


def slide_10_rq1(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, CREAM)
    _add_burgundy_header(slide)
    _add_title_in_header(slide, "Results: Self-Retrieval Accuracy (RQ1)")
    _add_gold_accent_line(slide, Inches(1.18))

    img = str(REPO / "paper_draft" / "figures" / "rq1_oracle_hr1_mrr.png")
    _add_image_centered(slide, img, top=Inches(1.45), max_w=Inches(11.5), max_h=Inches(4.2))

    # Key numbers bar at bottom
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.75), Inches(5.8), Inches(11.8), Inches(1.3),
    )
    shp.fill.solid()
    shp.fill.fore_color.rgb = BURGUNDY
    shp.line.fill.background()
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.3)
    tf.margin_top = Inches(0.12)
    lines_data = [
        "Compact library:  HR@1 = 76%  vs. 6% random   |   Expanded library:  HR@1 = 55%  vs. 2% random",
        "Expanded HR@5 = 86%  \u2014  the target song lands in the top 5 nearly 9 times out of 10.",
    ]
    for i, text in enumerate(lines_data):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = text
        _set_font(run, Pt(18), bold=(i == 1), color=WHITE)
        p.space_after = Pt(4)

    _add_notes(slide, (
        "[~60 seconds]\n\n"
        "Here are the self-retrieval results. This figure shows Hit Rate "
        "at 1 -- how often the target song is ranked first -- and Mean "
        "Reciprocal Rank, which captures how high it ranks on average. "
        "On the left is Experiment 1, the compact 101-line library. The "
        "full model puts the right song first 76 percent of the time. "
        "Random guessing after the same range filter? About 6 percent. "
        "On the right is Experiment 2 with 1,655 lines. The full model "
        "still finds the right song first 55 percent of the time -- versus "
        "just 2 percent for random. And if we look at the top 5 instead of "
        "just the top 1, the system finds the target song 86 percent of "
        "the time. That's nearly 9 out of 10. These two experiments use "
        "different protocols and different candidate pools, so the drop "
        "from 76 to 55 percent is not purely a library-size effect. But the "
        "key takeaway is clear: the system massively outperforms random "
        "ordering in both cases."
    ))


def slide_11_rq2(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, CREAM)
    _add_burgundy_header(slide)
    _add_title_in_header(slide, "Results: Ranking Stability (RQ2)")
    _add_gold_accent_line(slide, Inches(1.18))

    img = str(REPO / "experiment_results" / "RQ2_baselines.png")
    _add_image_centered(slide, img, top=Inches(1.45), max_w=Inches(8.0), max_h=Inches(3.8))

    bullets = [
        "Mean Kendall\u2019s \u03C4 = 0.84\u20130.85 (strong agreement; threshold = 0.7).",
        "Small changes to preferences \u2192 small changes in rankings.",
        "The system is stable and trustworthy.",
    ]
    _add_body_text(slide, bullets, top=Inches(5.5), height=Inches(1.8), size=Pt(20))

    _add_notes(slide, (
        "[~45 seconds]\n\n"
        "Next: is the system stable? If a singer makes a small change to "
        "their preferences -- adds one favorite note or removes one avoid "
        "note -- does the whole ranking fall apart? We tested this with 580 "
        "one-note perturbations across 20 baseline profiles in the expanded "
        "library. We measured Kendall's tau, which compares two ranked lists. "
        "A tau of 1.0 means identical rankings; 0.0 means completely "
        "unrelated. Anything above 0.7 is considered strong agreement. Our "
        "full model achieved a mean tau of 0.84. The cosine-only model was "
        "0.87, with overlapping confidence intervals. The random baseline "
        "was essentially zero, as expected. This means when a singer tweaks "
        "their preferences slightly, the recommendations stay largely the "
        "same. The system is stable and trustworthy."
    ))


def slide_12_alpha(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, CREAM)
    _add_burgundy_header(slide)
    _add_title_in_header(slide, "Sensitivity to the Avoid-Penalty Weight (\u03B1)")
    _add_gold_accent_line(slide, Inches(1.18))

    img = str(REPO / "paper_draft" / "figures" / "alpha_sensitivity_hr1_mrr_tau.png")
    _add_image_centered(slide, img, top=Inches(1.45), max_w=Inches(11.5), max_h=Inches(4.0))

    bullets = [
        "Self-retrieval performance is largely flat across \u03B1 values (0 to 1).",
        "Stability stays strong: \u03C4 \u2265 0.82 even at \u03B1 = 1.0.",
        "\u03B1 = 0.5 is a balanced default \u2014 meaningful avoid control without instability.",
    ]
    _add_body_text(slide, bullets, top=Inches(5.5), height=Inches(1.8), size=Pt(20))

    _add_notes(slide, (
        "[~45 seconds]\n\n"
        "We also tested how sensitive the results are to the choice of "
        "alpha -- the parameter that controls how heavily we penalize "
        "avoided notes. We swept alpha from 0 to 1 in both experiments. "
        "As you can see, self-retrieval performance -- Hit Rate at 1 and "
        "MRR -- is largely flat across the entire range. The system isn't "
        "brittle to this choice. Stability does decrease slightly as alpha "
        "increases, which makes sense: a stronger avoid penalty creates "
        "more sensitivity to changes in avoid preferences. But even at "
        "alpha equals 1, tau stays above 0.82 -- well above the strong "
        "agreement threshold. We report alpha equals 0.5 as a balanced "
        "default: it gives singers meaningful control over their avoid "
        "preferences without making the rankings jittery."
    ))


def slide_13_rq3(prs):
    notes = (
        "[~30 seconds]\n\n"
        "Finally, as an engineering sanity check, we verified that the "
        "formula is implemented exactly as designed. The identity residual "
        "-- the difference between the computed score and what the formula "
        "predicts -- is exactly zero. An OLS regression recovers the exact "
        "coefficients: cosine weight equals 1.0, avoid weight equals "
        "negative 0.5, R-squared equals 1.0. And all correlations go in "
        "the expected directions. Higher cosine similarity predicts a "
        "higher final score. Higher avoid penalty predicts a lower score. "
        "No hidden bugs, no rounding surprises. The math checks out."
    )
    _standard_slide(prs,
        "Implementation Verification (RQ3)",
        [
            "Identity check:  max |final \u2212 (cos \u2212 0.5 \u00d7 avoid)| = 0\n"
            "The formula is implemented with zero numerical error.",
            "OLS regression recovers exact coefficients:\n"
            "cos weight = 1.0,  avoid weight = \u22120.5,  R\u00b2 = 1.0.",
            "Spearman correlations all in expected directions:\n"
            "\u03C1(final, cos) = +0.99   |   \u03C1(final, avoid) = \u22120.32   |   \u03C1(cos, fav_overlap) = +0.92",
            "No hidden bugs.  No rounding surprises.  The math checks out.",
        ],
        notes,
    )


def slide_14_so_what(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, CREAM)
    _add_burgundy_header(slide)
    _add_title_in_header(slide, "What Does This Mean?")
    _add_gold_accent_line(slide, Inches(1.18))

    bullets = [
        "Proof-of-concept: data science can make vocal health decisions\n"
        "safer and more objective.",
        "Familiar techniques applied to a novel domain:\n"
        "cosine similarity, cold-start recommendation, offline evaluation.",
        "Content-based methods can work even without user-interaction data\n"
        "(cold-start / no collaborative signal).",
    ]
    _add_body_text(slide, bullets, top=Inches(1.5), height=Inches(2.8), size=Pt(22))

    # Audience question
    _add_big_quote(slide,
        "\u201cHow might content-based recommendation techniques\n"
        "from your own work apply to creative domains like music?\u201d",
        top=Inches(4.6),
    )

    _add_notes(slide, (
        "[~45 seconds]\n\n"
        "So what does this all mean? This is a proof-of-concept that shows "
        "data science can bring objectivity to a domain where decisions are "
        "traditionally subjective -- and where bad decisions have real "
        "health consequences. For those of you working in recommendation "
        "systems or information retrieval, this demonstrates that familiar "
        "techniques -- cosine similarity, content-based filtering, offline "
        "evaluation metrics -- can work in a completely new domain. And "
        "it works in a cold-start setting with no collaborative filtering "
        "data, which is often the hardest case. I'd love for you to think "
        "about this: how might content-based recommendation techniques from "
        "YOUR work apply to creative domains like music, art, or design? "
        "The tools are the same -- the application is what makes it novel."
    ))


def slide_15_limitations(prs):
    notes = (
        "[~30 seconds]\n\n"
        "I want to be upfront about limitations, because honesty "
        "strengthens research. First, these are synthetic profiles, not "
        "real singer preferences. We haven't done a human study yet. "
        "Second, we only tested on one corpus of German and French art "
        "song. Opera, musical theatre, and popular song are untested. "
        "Third, we only model pitch and duration -- we don't account for "
        "dynamics, tempo, or text setting. For future work, we want to "
        "evaluate with real singers and their actual preferences, expand "
        "to more diverse repertoire, add richer musical features, and "
        "ultimately build an interactive tool that singers and voice "
        "teachers can use in practice."
    )
    _standard_slide(prs, "Limitations & Future Work", [
        "Synthetic profiles only \u2014 no human evaluation yet.",
        "One corpus (German & French art song); opera, musical theatre,\n"
        "and popular song are untested.",
        "Pitch and duration only \u2014 dynamics, tempo, and text omitted.",
        "Future:  real singer preferences  |  diverse repertoire\n"
        "richer features  |  interactive recommendation tool.",
    ], notes)


def slide_16_closing(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_bg(slide, BURGUNDY)

    # Gold lines
    for y in (Inches(1.5), Inches(5.8)):
        shp = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(2), y, Inches(9.333), Inches(0.04),
        )
        shp.fill.solid()
        shp.fill.fore_color.rgb = GOLD
        shp.line.fill.background()

    # Summary
    tb = _add_textbox(slide, Inches(1), Inches(1.9), Inches(11.333), Inches(1.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = (
        "Duration-weighted tessituragrams can rank vocal repertoire\n"
        "by fit \u2014 and this is just the beginning."
    )
    _set_font(run, Pt(30), bold=True, color=WHITE)

    # Callback quote
    tb2 = _add_textbox(slide, Inches(1.5), Inches(3.7), Inches(10.333), Inches(1.0))
    p2 = tb2.text_frame.paragraphs[0]
    p2.alignment = PP_ALIGN.CENTER
    run2 = p2.add_run()
    run2.text = (
        "\u201cNext time a singer asks \u2018What should I sing?\u2019\n"
        "\u2014 data might have an answer.\u201d"
    )
    _set_font(run2, Pt(24), italic=True, color=LIGHT_GOLD)

    # Thank you
    tb3 = _add_textbox(slide, Inches(1), Inches(5.0), Inches(11.333), Inches(0.6))
    p3 = tb3.text_frame.paragraphs[0]
    p3.alignment = PP_ALIGN.CENTER
    run3 = p3.add_run()
    run3.text = "Thank You"
    _set_font(run3, Pt(36), bold=True, color=GOLD)

    # Contact
    tb4 = _add_textbox(slide, Inches(1), Inches(6.1), Inches(11.333), Inches(1.0))
    tf4 = tb4.text_frame
    tf4.word_wrap = True
    contact = [
        "Madeline Johnson, Flint Million, Rajeev Bukralia",
        "Minnesota State University, Mankato",
    ]
    for i, line in enumerate(contact):
        p4 = tf4.paragraphs[0] if i == 0 else tf4.add_paragraph()
        p4.alignment = PP_ALIGN.CENTER
        run4 = p4.add_run()
        run4.text = line
        _set_font(run4, Pt(18), color=LIGHT_GOLD)

    _add_notes(slide, (
        "[~15 seconds]\n\n"
        "To wrap up: duration-weighted tessituragrams can rank vocal "
        "repertoire by fit -- and this is just the beginning. Next time "
        "a singer asks 'What should I sing?', data might have an answer. "
        "Thank you very much for your time. I'd be happy to take any "
        "questions."
    ))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    slide_01_title(prs)
    slide_02_hook(prs)
    slide_03_gap(prs)
    slide_04_tessitura(prs)
    slide_05_tessituragram(prs)
    slide_06_pipeline(prs)
    slide_07_formula(prs)
    slide_08_dataset(prs)
    slide_09_testing(prs)
    slide_10_rq1(prs)
    slide_11_rq2(prs)
    slide_12_alpha(prs)
    slide_13_rq3(prs)
    slide_14_so_what(prs)
    slide_15_limitations(prs)
    slide_16_closing(prs)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print(f"Saved: {OUT}")
    print(f"Slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()
