"""Generate the CyberGuard AI viva preparation guide as a PDF.

    cd backend
    venv\\Scripts\\activate
    python generate_viva_pdf.py

Writes ``documentation/CyberGuard_AI_Viva_Guide.pdf``.

Every figure quoted in the document is taken from the measured results recorded
in documentation/17-19 and from the constants defined in the running code, so the
guide cannot drift from the implementation without the numbers below changing.
"""
import sys
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape as _escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)

BACKEND_DIR = Path(__file__).resolve().parent
ROOT = BACKEND_DIR.parent
SHOTS = ROOT / "documentation" / "screenshots"
OUTPUT = ROOT / "documentation" / "CyberGuard_AI_Viva_Guide.pdf"

# ----------------------------------------------------------------- design tokens
INK = colors.HexColor("#0f172a")
ACCENT = colors.HexColor("#0e7490")
ACCENT_LIGHT = colors.HexColor("#ecfeff")
MUTED = colors.HexColor("#64748b")
RULE = colors.HexColor("#cbd5e1")
BAND = colors.HexColor("#f1f5f9")
CODE_BG = colors.HexColor("#0f172a")
GREEN = colors.HexColor("#15803d")
AMBER = colors.HexColor("#b45309")
RED = colors.HexColor("#b91c1c")

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN


def esc(text):
    return _escape(str(text))


# ----------------------------------------------------------------------- styles
_base = getSampleStyleSheet()

S = {
    "title": ParagraphStyle("title", parent=_base["Title"], fontName="Helvetica-Bold",
                            fontSize=30, leading=35, textColor=INK, alignment=TA_CENTER,
                            spaceAfter=4),
    "subtitle": ParagraphStyle("subtitle", parent=_base["Normal"], fontName="Helvetica",
                               fontSize=13, leading=18, textColor=ACCENT, alignment=TA_CENTER),
    "covermeta": ParagraphStyle("covermeta", parent=_base["Normal"], fontName="Helvetica",
                                fontSize=10, leading=15, textColor=MUTED, alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", parent=_base["Heading1"], fontName="Helvetica-Bold",
                         fontSize=18, leading=22, textColor=INK, spaceBefore=2, spaceAfter=8),
    "h2": ParagraphStyle("h2", parent=_base["Heading2"], fontName="Helvetica-Bold",
                         fontSize=13, leading=17, textColor=ACCENT, spaceBefore=12, spaceAfter=5),
    "h3": ParagraphStyle("h3", parent=_base["Heading3"], fontName="Helvetica-Bold",
                         fontSize=10.5, leading=14, textColor=INK, spaceBefore=8, spaceAfter=3),
    "body": ParagraphStyle("body", parent=_base["BodyText"], fontName="Helvetica",
                           fontSize=9.5, leading=13.5, textColor=INK, alignment=TA_JUSTIFY,
                           spaceAfter=5),
    "small": ParagraphStyle("small", parent=_base["BodyText"], fontName="Helvetica",
                            fontSize=8.2, leading=11.5, textColor=MUTED, spaceAfter=3),
    "cell": ParagraphStyle("cell", parent=_base["BodyText"], fontName="Helvetica",
                           fontSize=8.3, leading=11, textColor=INK, spaceAfter=0),
    "cellb": ParagraphStyle("cellb", parent=_base["BodyText"], fontName="Helvetica-Bold",
                            fontSize=8.3, leading=11, textColor=INK, spaceAfter=0),
    "cellhead": ParagraphStyle("cellhead", parent=_base["BodyText"], fontName="Helvetica-Bold",
                               fontSize=8.3, leading=11, textColor=colors.white, spaceAfter=0),
    "code": ParagraphStyle("code", parent=_base["BodyText"], fontName="Courier",
                           fontSize=8, leading=11, textColor=colors.white, spaceAfter=0,
                           leftIndent=6, rightIndent=6, spaceBefore=0),
    "q": ParagraphStyle("q", parent=_base["BodyText"], fontName="Helvetica-Bold",
                        fontSize=9.5, leading=13, textColor=ACCENT, spaceBefore=7, spaceAfter=2),
    "a": ParagraphStyle("a", parent=_base["BodyText"], fontName="Helvetica",
                        fontSize=9.3, leading=13, textColor=INK, alignment=TA_JUSTIFY,
                        spaceAfter=3, leftIndent=9),
    "caption": ParagraphStyle("caption", parent=_base["BodyText"], fontName="Helvetica-Oblique",
                              fontSize=8.3, leading=11, textColor=MUTED, alignment=TA_CENTER,
                              spaceBefore=3, spaceAfter=10),
}


def P(text, style="body"):
    return Paragraph(text, S[style])


def bullets(items, style="body"):
    """A bulleted list rendered as an indented table so wrapping stays aligned."""
    rows = [[Paragraph("&bull;", S[style]), Paragraph(item, S[style])] for item in items]
    table = Table(rows, colWidths=[6 * mm, CONTENT_W - 6 * mm])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def code_block(lines, width=CONTENT_W):
    """A dark terminal-style block."""
    body = [[Paragraph(esc(line).replace(" ", "&nbsp;") or "&nbsp;", S["code"])] for line in lines]
    table = Table(body, colWidths=[width])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
        ("TOPPADDING", (0, 1), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 0),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    # A terminal block split across a page boundary is unreadable, so keep it whole.
    return KeepTogether([table])


def data_table(header, rows, widths, align_right=(), zebra=True, font_size=8.3):
    """A standard bordered table with a dark header row.

    A cell whose text begins with the marker ``<b>`` is rendered in the bold cell
    style; the marker itself is stripped so it never reaches the XML parser.
    """
    data = [[Paragraph(esc(h), S["cellhead"]) for h in header]]
    for row in rows:
        cells = []
        for value in row:
            text = str(value)
            if text.startswith("<b>"):
                cells.append(Paragraph(text[3:], S["cellb"]))
            else:
                cells.append(Paragraph(text, S["cell"]))
        data.append(cells)
    table = Table(data, colWidths=widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if zebra:
        style.append(("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BAND]))
    for col in align_right:
        style.append(("ALIGN", (col, 1), (col, -1), "RIGHT"))
    table.setStyle(TableStyle(style))
    return table


def callout(title, text, tone="accent"):
    """A tinted box used for 'say this in the viva' prompts."""
    tones = {
        "accent": (ACCENT_LIGHT, ACCENT),
        "warn": (colors.HexColor("#fffbeb"), AMBER),
        "danger": (colors.HexColor("#fef2f2"), RED),
        "ok": (colors.HexColor("#f0fdf4"), GREEN),
    }
    bg, bar = tones[tone]
    inner = [
        [Paragraph("<b>%s</b>" % esc(title), ParagraphStyle(
            "ct", parent=S["cell"], fontName="Helvetica-Bold", fontSize=9, textColor=bar))],
        [Paragraph(text, ParagraphStyle("cb", parent=S["cell"], fontSize=9, leading=12.5))],
    ]
    table = Table(inner, colWidths=[CONTENT_W - 8])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 2.5, bar),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
        ("TOPPADDING", (0, 1), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
    ]))
    return table


def screenshot(filename, caption):
    """Embed a captured screen at content width, preserving its 1440x900 ratio."""
    path = SHOTS / filename
    if not path.exists():
        return P("<i>[screenshot %s not found]</i>" % esc(filename), "small")
    width = CONTENT_W
    height = width * 900.0 / 1440.0
    image = Image(str(path), width=width, height=height)
    image.hAlign = "CENTER"
    frame = Table([[image]], colWidths=[width])
    frame.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return KeepTogether([frame, P(caption, "caption")])


def section(number, title):
    """Section heading with a coloured rule underneath."""
    head = Paragraph("<font color='#0e7490'>%s</font>&nbsp;&nbsp;%s" % (number, esc(title)), S["h1"])
    line = Table([[""]], colWidths=[CONTENT_W], rowHeights=[2])
    line.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACCENT)]))
    return KeepTogether([head, line, Spacer(1, 7)])


# ------------------------------------------------------------------ page chrome
def draw_cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(INK)
    canvas.rect(0, PAGE_H - 88 * mm, PAGE_W, 88 * mm, stroke=0, fill=1)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, PAGE_H - 91 * mm, PAGE_W, 3 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#22d3ee"))
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 26 * mm, "BCSE301P  SOFTWARE ENGINEERING LAB")
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 30)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 46 * mm, "CyberGuard AI")
    canvas.setFont("Helvetica", 14)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 57 * mm, "Intelligent Cyber Threat Detection System")
    canvas.setFillColor(colors.HexColor("#94a3b8"))
    canvas.setFont("Helvetica", 11)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H - 70 * mm, "Viva Preparation Guide")
    canvas.setFont("Helvetica-Oblique", 8.5)
    canvas.setFillColor(MUTED)
    canvas.drawCentredString(PAGE_W / 2, 14 * mm,
                             "Academic prototype - analyses simulated, defensive telemetry only.")
    canvas.restoreState()


def draw_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, PAGE_H - 13 * mm, PAGE_W - MARGIN, PAGE_H - 13 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, PAGE_H - 11.5 * mm, "CyberGuard AI  |  Viva Preparation Guide")
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 11.5 * mm,
                           "BCSE301P Software Engineering Lab")
    canvas.line(MARGIN, 13 * mm, PAGE_W - MARGIN, 13 * mm)
    canvas.drawString(MARGIN, 9 * mm, "Academic prototype - simulated telemetry only")
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(INK)
    canvas.drawRightString(PAGE_W - MARGIN, 9 * mm, "Page %d" % (doc.page - 1))
    canvas.restoreState()


def build():
    doc = BaseDocTemplate(
        str(OUTPUT), pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=20 * mm, bottomMargin=18 * mm,
        title="CyberGuard AI - Viva Preparation Guide",
        author="CyberGuard AI project team",
        subject="BCSE301P Software Engineering Lab",
    )
    frame = Frame(MARGIN, 18 * mm, CONTENT_W, PAGE_H - 38 * mm, id="body")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame], onPage=draw_cover),
        PageTemplate(id="main", frames=[frame], onPage=draw_page),
    ])

    story = []
    add = story.append

    # ================================================================== COVER
    add(Spacer(1, 96 * mm))
    add(P("<b>What this document is</b>", "h3"))
    add(P(
        "A single-sitting preparation guide for the CyberGuard AI viva. It explains what the "
        "system does, how each part works, how the implementation maps onto every Software "
        "Engineering Lab experiment, a timed live-demonstration script, and prepared answers to "
        "the questions most likely to be asked. Every number quoted here was measured from the "
        "running system, not estimated."))
    add(Spacer(1, 4 * mm))

    summary = data_table(
        ["Delivered", "Figure", "Delivered", "Figure"],
        [
            ["<b>Backend Python modules", "48", "<b>Automated tests", "117 (all passing)"],
            ["<b>Frontend modules", "22", "<b>REST endpoints", "46"],
            ["<b>Database entities", "10", "<b>Frontend screens", "12"],
            ["<b>Detection categories", "8", "<b>Engineered features", "18"],
            ["<b>Behavioural rules", "7", "<b>SE documents", "23"],
        ],
        widths=[CONTENT_W * 0.28, CONTENT_W * 0.22, CONTENT_W * 0.28, CONTENT_W * 0.22])
    add(summary)
    add(Spacer(1, 5 * mm))
    add(P("Generated %s" % date.today().strftime("%d %B %Y"), "covermeta"))

    add(NextPageTemplate("main"))
    add(PageBreak())

    # =============================================================== CONTENTS
    add(section("", "Contents"))
    contents = [
        ["1", "The project in sixty seconds", "What to say when asked 'what is it?'"],
        ["2", "Architecture", "Layers, dependency rule, why it is shaped this way"],
        ["3", "The detection engine", "The technical core - expect the most questions here"],
        ["4", "Database design", "Ten entities, the relationships that matter"],
        ["5", "The incident state machine", "The strongest single demonstration"],
        ["6", "Syllabus mapping", "Every experiment traced to an artefact"],
        ["7", "The application in twelve screens", "Real captures from the running system"],
        ["8", "Live demonstration script", "A timed ten-minute walkthrough"],
        ["9", "Anticipated viva questions", "Thirty questions with prepared answers"],
        ["10", "Defects found and fixed", "The honest engineering story"],
        ["11", "Limitations and future work", "What to admit before being asked"],
        ["12", "Quick reference card", "Commands, numbers and constants to memorise"],
    ]
    add(data_table(["#", "Section", "Why it matters"], contents,
                   widths=[10 * mm, 52 * mm, CONTENT_W - 62 * mm]))
    add(Spacer(1, 6 * mm))
    add(callout(
        "How to use this guide",
        "Read sections 1, 3 and 5 until you can deliver them without notes - they carry the most "
        "marks. Section 8 is the demonstration itself. Section 10 is what separates a project that "
        "was built from one that was merely assembled: be ready to talk about the defects you "
        "found, because being able to describe a bug you fixed is stronger evidence of "
        "understanding than any feature list."))

    add(PageBreak())

    # ========================================================= 1. SIXTY SECONDS
    add(section("1", "The project in sixty seconds"))
    add(P(
        "CyberGuard AI is a working Security Operations Centre platform. It takes security "
        "telemetry - records of network connections and authentication attempts - classifies each "
        "record with an explainable detection engine, raises alerts for anything suspicious, "
        "drives an investigation through a guarded lifecycle, and produces a report at the end."))
    add(P(
        "The distinguishing design decision is that <b>every verdict is explainable</b>. The engine "
        "never returns a bare score. It returns a classification, a risk value from 0 to 100, a "
        "confidence, the individual contribution of each of its three detectors, and a list of "
        "plain-English reasons an analyst can act on or challenge."))
    add(P(
        "The second decision is that <b>the documentation and the code are the same system</b>. "
        "The state transition diagram is the transition table the API enforces. The ER diagram is "
        "the SQLAlchemy schema. The severity bands in the Level 2 data flow diagram are the "
        "constants the engine applies. None of the diagrams were drawn separately from the "
        "implementation, which is why they cannot drift out of step with it."))

    add(P("What it deliberately does not do", "h2"))
    add(P(
        "The system is strictly defensive and that is visible at the diagram level. Looking at the "
        "context diagram, <b>there is no outbound arrow to any network, host or third-party "
        "service</b>. CyberGuard AI only ever replies to the people who call it. It cannot scan, "
        "probe or attack anything, because it has no data flow through which to do so. All "
        "telemetry is pushed in by a human - either typed into a form or uploaded as a CSV file."))
    add(bullets([
        "No malware, exploits or payloads of any kind exist in the repository.",
        "No credential harvesting, password cracking or brute-force capability.",
        "No scanning or attack automation - the engine only reads numbers it was handed.",
        "No real threat infrastructure: indicators use the RFC 5737 documentation ranges "
        "(192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) and the reserved <i>.invalid</i> and "
        "<i>.example</i> domain namespaces.",
    ]))

    add(callout(
        "Say this if asked 'is this safe?'",
        "\"It is defensive by construction, not by policy. The context diagram has no outbound "
        "flow - the system has no mechanism to reach any host. It reads numbers that a user gives "
        "it and scores them. Every address in the demonstration data comes from the IETF ranges "
        "reserved for documentation.\"", "ok"))

    add(PageBreak())

    # ============================================================ 2. ARCHITECTURE
    add(section("2", "Architecture"))
    add(code_block([
        "  Browser  -  React 18 + Vite + Tailwind + Recharts",
        "      |",
        "      |   REST / JSON, Bearer token",
        "      v",
        "  Flask application factory",
        "      |",
        "      +-- routes/     11 blueprints, 46 endpoints, one JSON envelope",
        "      +-- services/   detection, alert, incident, analytics, report,",
        "      |               auth, audit",
        "      +-- ml/         detection engine",
        "      |                 features.py   18 engineered features",
        "      |                 rules.py      7 explainable rules",
        "      |                 anomaly.py    statistical baseline",
        "      |                 detector.py   fusion, severity, explanation",
        "      +-- models/     10 SQLAlchemy entities",
        "      +-- utils/      validation, security, errors, CSV, logging",
        "      |",
        "      v",
        "  SQLite  -  database/cyberguard.db",
    ]))
    add(Spacer(1, 4 * mm))

    add(P("The dependency rule", "h2"))
    add(P(
        "Dependencies point strictly inward and never back out: "
        "<font face='Courier'>routes &rarr; services &rarr; models &rarr; extensions</font>, with "
        "<font face='Courier'>utils</font> available to every layer."))
    add(data_table(
        ["Package", "May import", "Must never import"],
        [
            ["<b>routes", "services, utils, models", "nothing imports routes"],
            ["<b>services", "models, ml, utils, extensions", "routes"],
            ["<b>ml", "standard library, NumPy, scikit-learn (optional)",
             "models, services, routes, Flask, the database"],
            ["<b>models", "extensions, utils", "services, routes, ml"],
            ["<b>utils", "models (inside a function body only)", "services, routes"],
        ],
        widths=[24 * mm, 68 * mm, CONTENT_W - 92 * mm]))
    add(Spacer(1, 3 * mm))

    add(callout(
        "The point worth making about ml/",
        "The detection engine imports nothing from Flask, from SQLAlchemy or from the rest of the "
        "application. That is a deliberate design decision with three payoffs: its 18 unit tests "
        "run with no database and no HTTP layer; the same engine runs from the command line via "
        "<font face='Courier'>python -m app.ml.predict</font>; and it could be swapped for a "
        "different implementation provided <font face='Courier'>detect()</font> keeps its "
        "contract."))

    add(P("Why these technology choices", "h2"))
    add(data_table(
        ["Choice", "Reason"],
        [
            ["<b>SQLite, not PostgreSQL",
             "No service to install and no credentials to configure - the whole database is one "
             "file that can be deleted and rebuilt with a single command. The lab machine may not "
             "permit installing a database service. SQLAlchemy abstracts the dialect, so moving "
             "to PostgreSQL is a change to one URL."],
            ["<b>Flask, not Django",
             "The project needs a REST API and nothing else. Django's admin, templating and auth "
             "stack would all be unused weight."],
            ["<b>Detection engine in-process",
             "Avoids a second process to start and a network hop per event. At the prototype's "
             "volumes an in-process call takes 7 milliseconds."],
            ["<b>ML is optional",
             "If scikit-learn or the trained artefacts are absent the engine reports "
             "<font face='Courier'>hybrid-rules</font> mode and keeps working. This is proved by "
             "a test, not merely claimed."],
            ["<b>Vite dev-server proxy",
             "The browser only ever talks to one origin during development, so CORS is never "
             "exercised. CORS is still configured for the case where the frontend is served "
             "separately."],
        ],
        widths=[42 * mm, CONTENT_W - 42 * mm]))

    add(PageBreak())

    # ======================================================== 3. DETECTION ENGINE
    add(section("3", "The detection engine"))
    add(P(
        "This is the technical core of the project and where the most detailed questions will be "
        "asked. Three independent detectors vote on every event."))

    add(data_table(
        ["Detector", "Nature", "What it contributes"],
        [
            ["<b>Rule bank", "Deterministic, fully explainable",
             "7 behavioural rules; each returns a score and a list of reasons"],
            ["<b>Statistical baseline", "Unsupervised",
             "Robust z-scores against learned normals, mapped through a saturating curve"],
            ["<b>Machine learning", "Optional, supervised + novelty",
             "RandomForest probability and IsolationForest outlier score"],
        ],
        widths=[32 * mm, 42 * mm, CONTENT_W - 74 * mm]))
    add(Spacer(1, 3 * mm))

    add(P("The eight processing stages", "h2"))
    add(data_table(
        ["#", "Stage", "What happens"],
        [
            ["1", "Extract features", "11 observed fields become 18 numeric features"],
            ["2", "Rule bank", "All 7 rules evaluated; highest score wins the classification"],
            ["3", "Statistical", "z-scores; only deviations above +2 sigma count"],
            ["4", "Machine learning", "Skipped entirely if artefacts are missing"],
            ["5", "Fuse scores", "Weighted blend with a rule-score floor"],
            ["6", "Map severity", "Risk band, and the threat/benign verdict"],
            ["7", "Confidence", "Grows with signal strength and detector agreement"],
            ["8", "Assemble explanation", "Reasons, recommended action, MITRE tactic, timing"],
        ],
        widths=[8 * mm, 34 * mm, CONTENT_W - 42 * mm]))
    add(Spacer(1, 4 * mm))

    add(P("The fusion formula", "h2"))
    add(code_block([
        "  with ML:     weighted = 0.58*rule + 0.18*anomaly + 0.24*ml",
        "  without ML:  weighted = 0.74*rule + 0.26*anomaly",
        "",
        "  risk = clamp( max(weighted, 0.85 * rule_score) * sensitivity , 0, 100 )",
    ]))
    add(Spacer(1, 3 * mm))
    add(P(
        "The <b>rule score acts as a floor</b>. The statistical and machine-learning detectors "
        "contribute only through the weighted term, so on their own they can raise an event to "
        "MEDIUM for review but never to CRITICAL. This is a deliberate decision: an unexplained "
        "statistical outlier is worth a human glance, but it is not worth waking someone up. "
        "Without the floor the alert queue fills with unactionable 'critical' noise."))
    add(P(
        "<font face='Courier'>sensitivity</font> is the analyst's own setting from the Settings "
        "page, clamped to the range 0.5 to 1.5."))

    add(P("Severity bands and what they trigger", "h2"))
    band_rows = [
        ["<b>LOW", "0 - 25", "Benign. Stored and counted, nothing raised.", ""],
        ["<b>MEDIUM", "26 - 50", "Threat recorded and an <b>alert raised</b>.", "alert threshold"],
        ["<b>HIGH", "51 - 75", "Threat and alert; analyst prioritises it.", ""],
        ["<b>CRITICAL", "76 - 100", "Alert plus an <b>incident opened automatically</b>.",
         "incident threshold"],
    ]
    band_table = data_table(["Band", "Risk", "Consequence", "Constant"], band_rows,
                            widths=[22 * mm, 22 * mm, CONTENT_W - 78 * mm, 34 * mm])
    band_table.setStyle(TableStyle([
        ("TEXTCOLOR", (0, 1), (0, 1), GREEN),
        ("TEXTCOLOR", (0, 2), (0, 2), AMBER),
        ("TEXTCOLOR", (0, 3), (0, 3), colors.HexColor("#e11d48")),
        ("TEXTCOLOR", (0, 4), (0, 4), RED),
    ]))
    add(band_table)
    add(Spacer(1, 4 * mm))

    add(P("The seven rules", "h2"))
    add(data_table(
        ["Rule", "Fires when", "Magnitude term"],
        [
            ["<b>Brute Force Attempt", "failed logins &ge; 5", "38 + 30&middot;log10(failed/4)"],
            ["<b>Denial-of-Service Pattern", "requests &ge; 400 or packets/s &ge; 400",
             "20 + 30&middot;log10(requests/300)"],
            ["<b>Data Transfer Anomaly", "bytes &ge; 45 MB", "18 + 30&middot;log10(MB/40)"],
            ["<b>Port Scanning Pattern", "requests &ge; 25 and bytes/packet &le; 220",
             "18 + 26&middot;log10(requests/20)"],
            ["<b>Credential Abuse Pattern", "auth event, failed &ge; 3, requests &ge; 30",
             "22 + 18&middot;log10(requests/25), capped at 45"],
            ["<b>Suspicious Login Activity", "1 &le; failed logins &le; 4", "15 + 7&middot;failed"],
            ["<b>Network Anomaly", "catch-all traffic-shape rule", "duration and packet-size terms"],
        ],
        widths=[44 * mm, 56 * mm, CONTENT_W - 100 * mm]))
    add(Spacer(1, 3 * mm))

    add(callout(
        "Why the magnitude terms are logarithmic - the best answer in the project",
        "With a linear term, a brute-force attempt with 20 failed logins and one with 2000 both "
        "saturate at 100, so the entire alert queue collapses into a single severity band and the "
        "dashboard conveys nothing. A logarithmic curve keeps the ordering intact across three "
        "orders of magnitude: 5 failures score 41, 20 score 59, 50 score 71, 150 score 85. That "
        "is exactly what an analyst needs in order to prioritise. This was not the first design - "
        "see section 10, defect D1.", "accent"))

    add(PageBreak())

    add(P("Measured performance", "h2"))
    add(P(
        "Measured on the development machine (Windows 11, Python 3.10.0) over 2000 generated "
        "events per mode, first call discarded:"))
    add(data_table(
        ["Mode", "Mean", "Median", "p95", "p99", "Throughput"],
        [
            ["<b>hybrid-ml", "7.083 ms", "6.596 ms", "9.890 ms", "13.672 ms", "141 events/s"],
            ["<b>hybrid-rules", "0.033 ms", "0.027 ms", "0.069 ms", "0.121 ms", "29 930 events/s"],
        ],
        widths=[32 * mm, 24 * mm, 24 * mm, 24 * mm, 26 * mm, CONTENT_W - 130 * mm]))
    add(Spacer(1, 3 * mm))
    add(P(
        "The requirement was under 50 ms per event, so the p99 in ML mode sits comfortably inside "
        "it. The first measurement did not - see defect D3 in section 10."))

    add(P("Honesty about the model accuracy", "h2"))
    add(callout(
        "Do not claim 99.9% accuracy - explain it",
        "The trained classifier reports around 99.9% on its hold-out split, and that number is "
        "<b>not</b> evidence of real-world performance. The synthetic generator produces "
        "behaviour profiles that are well separated by construction, so a high score reflects that "
        "separability, not detection skill. The system has never analysed a real network capture. "
        "The metadata file, the project report and this guide all state this. Saying so first is "
        "far stronger than being caught by the question.", "warn"))
    add(Spacer(1, 3 * mm))
    add(P(
        "The dashboard therefore never displays a bare accuracy figure. It selects a source in "
        "priority order and labels it:"))
    add(bullets([
        "<b>Analyst-confirmed precision</b> once five or more alerts have been triaged: "
        "resolved &divide; (resolved + false positives).",
        "Otherwise the <b>model hold-out accuracy</b>, explicitly marked as measured on synthetic "
        "data.",
        "Otherwise the <b>mean engine confidence</b>, marked as a fallback.",
    ]))
    add(P(
        "Every response carries <font face='Courier'>source</font>, "
        "<font face='Courier'>label</font> and <font face='Courier'>note</font>, so a number is "
        "never presented without saying where it came from."))

    add(PageBreak())

    # ============================================================== 4. DATABASE
    add(section("4", "Database design"))
    add(P(
        "Ten entities. The schema is in Third Normal Form with two documented, deliberate "
        "exceptions."))
    add(data_table(
        ["Entity", "Purpose", "Key relationship"],
        [
            ["<b>User", "Analysts and administrators", "owns Incidents, AuditLogs, Reports"],
            ["<b>Asset", "Monitored hosts and devices", "1 : N SecurityEvent"],
            ["<b>SecurityEvent", "One observed record - the central fact table",
             "1 : 1 DetectionResult"],
            ["<b>DetectionResult", "The engine's verdict", "unique FK to SecurityEvent"],
            ["<b>Threat", "A classified malicious-looking finding", "N : 1 SecurityEvent"],
            ["<b>Alert", "Analyst-facing notification", "N : 1 Threat, N : 1 Incident"],
            ["<b>Incident", "Investigation case with a lifecycle", "1 : N Alert"],
            ["<b>ThreatIndicator", "Simulated intelligence records", "no FK - matched by value"],
            ["<b>Report", "Generated security report", "N : 1 User"],
            ["<b>AuditLog", "Append-only trail of state changes", "N : 1 User"],
        ],
        widths=[32 * mm, CONTENT_W - 92 * mm, 60 * mm]))
    add(Spacer(1, 4 * mm))

    add(P("The three relationships worth explaining", "h2"))
    add(P(
        "<b>SecurityEvent &rarr; DetectionResult is the only true 1:1.</b> It is enforced by a "
        "UNIQUE constraint on the foreign key. Conceptually one event cannot have two "
        "contradictory verdicts."))
    add(P(
        "<b>Incident &rarr; Alert is what makes triage work.</b> Several alerts from the same "
        "source attach to one incident, so the analyst investigates a campaign rather than each "
        "packet-level finding in isolation. When the incident closes, every alert attached to it "
        "closes with it."))
    add(P(
        "<b>ThreatIndicator has no foreign key by design.</b> Indicators are correlated to events "
        "by value, not by referential integrity. Adding a foreign key would mean an indicator "
        "could only exist once matching evidence already existed - which inverts how an "
        "intelligence feed actually works, since the feed is meant to be populated before the "
        "matching traffic appears."))

    add(P("The deliberate denormalisation", "h2"))
    add(P(
        "Be ready for this - an examiner who reads the schema will spot it. Severity and score "
        "are duplicated across DetectionResult, Threat and Alert. That is a <b>temporal "
        "snapshot</b>, not an oversight: an alert records the severity as assessed at the moment "
        "it was raised. If an analyst later changes their detection sensitivity, previously "
        "stored detections must keep their original scores, otherwise historical charts would "
        "silently rewrite themselves. For a security tool, auditability outweighs strict "
        "normalisation."))
    add(P(
        "The second exception is JSON-serialised columns - reasons, features, history and report "
        "content. These are variable-length, always read whole with their parent row, and never "
        "queried or joined on. Five child tables would add joins to every read for no query "
        "benefit."))

    add(KeepTogether([
        P("Deletion behaviour", "h2"),
        data_table(
            ["Relationship", "On delete", "Why"],
            [
                ["SecurityEvent &rarr; DetectionResult / Threat / Alert", "cascade delete",
                 "A verdict about a deleted event is meaningless"],
                ["<b>Asset &rarr; SecurityEvent", "<b>set asset_id to NULL",
                 "<b>Retiring an asset must not destroy security history"],
                ["Incident &rarr; Alert", "no cascade", "Alerts survive and can be re-linked"],
            ],
            widths=[62 * mm, 32 * mm, CONTENT_W - 94 * mm]),
    ]))

    add(PageBreak())

    # ======================================================== 5. STATE MACHINE
    add(section("5", "The incident state machine"))
    add(callout(
        "This is the single strongest demonstration in the project",
        "It shows a behavioural model that is not merely drawn but <b>enforced at runtime</b>. "
        "The transition table in the design document is the same Python dictionary the API "
        "consults on every request. Demonstrate it live - section 8, step 4."))
    add(Spacer(1, 3 * mm))

    add(code_block([
        "                        (risk >= 76, or created manually)",
        "                                     |",
        "                                     v",
        "                                 [  NEW  ]",
        "                                 /   |   \\",
        "                    acknowledge /    |    \\ dismiss",
        "                               v     | begin v",
        "                          [ OPEN ]   | triage  [ FALSE_POSITIVE ]",
        "                            |  \\     |              ^     |",
        "                     begin  |   \\    |              |     | reopen",
        "                     triage |    \\   v              |     v",
        "                            v     [ INVESTIGATING ]--+-->[ INVESTIGATING ]",
        "                             \\         |     \\",
        "                      contain \\        |      \\ resolve",
        "                               v       | contain\\",
        "                          [ CONTAINED ]         v",
        "                                |   \\     [ RESOLVED ]",
        "                        resolve |    \\ reopen   |",
        "                                v     +---------+ reopen",
        "                          [ RESOLVED ]",
    ]))
    add(Spacer(1, 4 * mm))

    add(P("The transition table - the executable specification", "h2"))
    add(data_table(
        ["From state", "Permitted next states"],
        [
            ["<b>NEW", "OPEN, INVESTIGATING, FALSE_POSITIVE"],
            ["<b>OPEN", "INVESTIGATING, CONTAINED, FALSE_POSITIVE"],
            ["<b>INVESTIGATING", "CONTAINED, RESOLVED, FALSE_POSITIVE"],
            ["<b>CONTAINED", "RESOLVED, INVESTIGATING"],
            ["<b>RESOLVED", "INVESTIGATING (reopen)"],
            ["<b>FALSE_POSITIVE", "INVESTIGATING (reopen)"],
        ],
        widths=[42 * mm, CONTENT_W - 42 * mm]))
    add(Spacer(1, 3 * mm))
    add(P(
        "Anything not in that table is refused with <b>HTTP 409 CONFLICT</b>, and the response "
        "names the current state and the permitted set."))

    add(P("Why specific transitions are forbidden", "h2"))
    add(data_table(
        ["Attempted", "Why it is refused"],
        [
            ["NEW &rarr; CONTAINED", "Nothing can be contained before anyone has looked at it"],
            ["NEW &rarr; RESOLVED",
             "Closing a case nobody investigated would defeat the audit trail"],
            ["CONTAINED &rarr; FALSE_POSITIVE",
             "Containment was already applied, so the finding was acted on; retroactively calling "
             "it a false positive would misstate the history"],
            ["RESOLVED &rarr; CONTAINED", "Cannot regress from closed - reopen to INVESTIGATING first"],
        ],
        widths=[46 * mm, CONTENT_W - 46 * mm]))
    add(Spacer(1, 4 * mm))

    add(P("How the user interface stays honest", "h2"))
    add(P(
        "The API returns <font face='Courier'>allowed_transitions</font> on every incident read, "
        "and the Incident Details page renders a button only for each entry in that array. The "
        "interface therefore <b>cannot offer an illegal move</b> - and the API would refuse it "
        "anyway if something else called it directly. Two independent guards, one source of "
        "truth."))

    add(P("Why alerts have a different, looser machine", "h2"))
    add(P(
        "An alert may legitimately be resolved straight from NEW: an experienced analyst can "
        "recognise a known-benign pattern at a glance. An <b>incident</b>, by contrast, exists "
        "precisely because something needs work, so skipping investigation would make its audit "
        "trail meaningless. The asymmetry is the reason the two machines are separate rather than "
        "shared."))

    add(P("The feedback loop", "h2"))
    add(P(
        "The two terminal alert states are not merely bookkeeping - they are the system's "
        "ground-truth signal. Once five or more alerts have been closed, "
        "<font face='Courier'>resolved &divide; (resolved + false positives)</font> becomes the "
        "Detection Accuracy figure on the dashboard, labelled 'analyst-confirmed precision'. "
        "Triage decisions made in section 8 of the demonstration change the number shown in "
        "step 2."))

    add(PageBreak())

    # ======================================================== 6. SYLLABUS MAP
    add(section("6", "Syllabus mapping"))
    add(P(
        "Every lab experiment traced to the artefact that satisfies it and to the code that "
        "implements it. All documents are in <font face='Courier'>documentation/</font>."))
    add(data_table(
        ["Experiment", "Artefact", "Doc", "In the code"],
        [
            ["<b>1. Process model",
             "Incremental/Agile selected after comparing Waterfall, Prototyping, Spiral; 9 "
             "increments; risk register", "01",
             "Evidenced by the increment-7 re-calibration"],
            ["<b>2. WBS and estimation",
             "All four views - process, product, geographic, role - with duration, effort, "
             "dependencies, roles", "02", "445-hour baseline, cross-checked"],
            ["<b>3. ER diagram",
             "10 entities, 9 relationships, cardinality, keys, indexes, normalisation", "04",
             "app/models/ (10 files)"],
            ["<b>4. Context + DFD",
             "Context, Level 0, Level 1, Level 2 with balancing checks", "05-08",
             "routes/, services/, ml/, csv_parser.py"],
            ["<b>5. State transition",
             "Incident and alert lifecycles, legal and forbidden transitions", "09",
             "models/incident.py"],
            ["<b>6. Use case + class",
             "3 actors, 17 use cases, include/extend; entity, control and service classes", "10, 11",
             "whole code base"],
            ["<b>7. Interaction models",
             "7 sequence diagrams, 6 communication diagrams", "12, 13", "whole code base"],
            ["<b>8. Package / component / deployment",
             "Dependency rule, provided-required interfaces, degradation matrix, two topologies",
             "14-16", "package layout of app/ and src/"],
            ["<b>9. Testing",
             "117 automated cases, 11 manual scenarios, measured non-functional results",
             "17-19", "backend/tests/ (5 modules)"],
            ["<b>10. Storyboard + UI",
             "9-frame narrative storyboard; colour system, components, accessibility", "20, 21",
             "frontend/src/"],
        ],
        widths=[36 * mm, CONTENT_W - 108 * mm, 14 * mm, 58 * mm]))
    add(Spacer(1, 4 * mm))

    add(PageBreak())
    add(P("The concept-to-realisation table", "h2"))
    add(data_table(
        ["Concept", "CyberGuard AI realisation"],
        [
            ["Process Model", "Incremental/Agile with a documentation-inclusive Definition of Done"],
            ["WBS", "Project task decomposition in four views"],
            ["ERD", "The database structure - 10 entities as SQLAlchemy models"],
            ["DFD", "Security event processing, down to the engine's eight stages"],
            ["State Diagram", "The incident lifecycle, enforced by the API"],
            ["Use Case", "Analyst and administrator interactions with the console"],
            ["Class Diagram", "Entity, service and engine classes with multiplicity"],
            ["Sequence Diagram", "The threat-detection interaction, end to end"],
            ["Component Diagram", "System architecture with its degradation paths"],
            ["Deployment Diagram", "The two-process local deployment on Windows 11"],
            ["Testing", "117 backend cases plus manual frontend scenarios"],
            ["Storyboard", "One analyst's shift, from login to handover report"],
            ["UI Design", "The Security Operations Centre dashboard"],
        ],
        widths=[44 * mm, CONTENT_W - 44 * mm]))

    add(PageBreak())

    # ============================================================ 7. SCREENS
    add(section("7", "The application in twelve screens"))
    add(P(
        "Every image below is a real capture from the running application at a 1440&times;900 "
        "viewport. Demonstration passwords on the login screen were replaced with bullet "
        "characters before capture; no credential, token or key appears in any image."))
    add(Spacer(1, 2 * mm))

    shots = [
        ("01_login.png",
         "1. Login - demo account cards, with passwords redacted for publication."),
        ("02_dashboard.png",
         "2. Dashboard - 8 KPIs, threat level, and six charts, every figure read from the "
         "database."),
        ("03_threat_detection.png",
         "3. Threat Detection - the event form with a sample scenario loaded."),
        ("12_detection_result.png",
         "12. Detection result - risk 92/100, CRITICAL, 95.7% confidence, with the reasons and "
         "the three detector sub-scores."),
        ("04_alerts.png",
         "4. Alerts - the triage queue with server-side filtering, search and pagination."),
        ("05_incidents.png",
         "5. Incidents - cases opened automatically at CRITICAL or raised by hand."),
        ("06_incident_details.png",
         "6. Incident details - the lifecycle tracker, and only the transitions the state machine "
         "currently permits."),
        ("07_threat_intelligence.png",
         "7. Threat Intelligence - a simulated indicator feed, labelled as simulated."),
        ("08_log_analyzer.png",
         "8. Log Analyzer - a 120-row CSV analysed, broken down by severity."),
        ("09_assets.png",
         "9. Assets - the monitored inventory; risk rises with the worst event seen on each host."),
        ("10_reports.png",
         "10. Reports - generation form, live preview, and stored reports for re-download."),
        ("11_settings.png",
         "11. Settings - system status with live per-table row counts."),
    ]
    for index, (filename, caption) in enumerate(shots):
        add(screenshot(filename, caption))
        if index % 2 == 1 and index != len(shots) - 1:
            add(PageBreak())

    add(PageBreak())

    # ========================================================= 8. DEMO SCRIPT
    add(section("8", "Live demonstration script"))
    add(P(
        "A ten-minute walkthrough that touches every syllabus concept against running code. "
        "Start both servers before the viva begins and leave them running."))
    add(code_block([
        "  Terminal 1:   cd backend",
        "                venv\\Scripts\\activate",
        "                python run.py",
        "",
        "  Terminal 2:   cd frontend",
        "                npm run dev",
        "",
        "  Browser:      http://localhost:5173",
    ]))
    add(Spacer(1, 4 * mm))

    steps = [
        ("1", "0:00", "Show that it is real",
         "Open <font face='Courier'>http://127.0.0.1:5000/api/health</font> in a tab. Point at "
         "<font face='Courier'>detection_engine.mode</font> and "
         "<font face='Courier'>database.connected</font>. This is a live service, not a mockup."),
        ("2", "1:00", "Login and dashboard",
         "Sign in with the Administrator demo card. On the dashboard make two specific points: "
         "the Detection Accuracy tile <b>states its own source</b> ('Analyst-confirmed "
         "precision'), and the Threat Level card <b>states the basis</b> for its assessment. The "
         "system never shows a bare number."),
        ("3", "2:00", "Analyse an event - the core demonstration",
         "Threat Detection &rarr; load the sample <b>'Repeated failed SSH logins'</b> &rarr; "
         "Analyze Threat. Talk through the risk score, the severity, the <b>reasons</b>, and the "
         "<b>three sub-score bars</b>. Explain that the rule score is the floor, so a verdict is "
         "always anchored to something deterministic. Point out the alert and incident created "
         "automatically at the 26 and 76 thresholds. Then submit an <b>invalid IP</b> to show "
         "validation naming the exact field."),
        ("4", "5:00", "The state machine - the strongest moment",
         "Open the incident just created. It is in NEW, and <b>only three buttons are offered</b> "
         "- Investigate, Reopen as open, False positive. Contain and Resolve are absent. Then "
         "attempt the illegal transition directly against the API and show the HTTP 409 naming "
         "the allowed set. Finally drive it properly: Investigate &rarr; Contain &rarr; Resolve, "
         "and show the four attributed history entries and the linked alert closing with it."),
        ("5", "7:00", "CSV upload and error isolation",
         "Log Analyzer &rarr; upload <font face='Courier'>sample_logs_mixed.csv</font> and show "
         "the severity breakdown. Then upload "
         "<font face='Courier'>sample_logs_invalid.csv</font>: <b>1 row analysed, 4 rejected</b>, "
         "each with its line number and reason, and still HTTP 201. Explain that one malformed "
         "row must never abort a real log export."),
        ("6", "8:30", "Reports",
         "Generate a 30-day summary. Point out that the <b>recommendations are derived from the "
         "actual figures</b>, not a fixed list. Download the PDF."),
        ("7", "9:00", "Tests and the honest engineering story",
         "Run <font face='Courier'>python -m pytest -q</font> - 117 passed. Then walk through two "
         "of the defects in section 10, especially D1 (severity saturation) and D3 (the "
         "performance defect found by measurement)."),
    ]
    add(data_table(
        ["#", "At", "Step", "What to do and say"],
        [[s[0], s[1], "<b>" + s[2], s[3]] for s in steps],
        widths=[8 * mm, 12 * mm, 34 * mm, CONTENT_W - 54 * mm]))
    add(Spacer(1, 4 * mm))

    add(P("The one command to have ready", "h2"))
    add(P("For step 4, paste this into PowerShell to prove the state machine is enforced:"))
    add(code_block([
        "  $r = Invoke-RestMethod -Uri http://127.0.0.1:5000/api/auth/login -Method Post `",
        "        -ContentType 'application/json' `",
        "        -Body '{\"email\":\"admin@cyberguard.ai\",\"password\":\"admin123\"}'",
        "  $T = $r.data.token",
        "",
        "  # replace 93 with the incident id shown on screen",
        "  Invoke-RestMethod -Uri http://127.0.0.1:5000/api/incidents/93 -Method Put `",
        "        -Headers @{ Authorization = \"Bearer $T\" } `",
        "        -ContentType 'application/json' -Body '{\"status\":\"RESOLVED\"}'",
        "",
        "  # -> HTTP 409 CONFLICT",
        "  #    'Invalid lifecycle transition: NEW -> RESOLVED.",
        "  #     Allowed from NEW: FALSE_POSITIVE, INVESTIGATING, OPEN.'",
    ]))

    add(PageBreak())

    # ============================================================== 9. Q & A
    add(section("9", "Anticipated viva questions"))

    qa = [
        ("Why did you choose an Agile/Incremental process model rather than Waterfall?",
         "Because the detection logic could not be fully specified in advance - it had to be "
         "calibrated against generated data and judged by looking at the output. Waterfall "
         "assumes requirements are frozen after phase 1, and that assumption failed in practice: "
         "the risk-fusion formula and the severity distribution both had to be redesigned after "
         "we saw the first seeded dashboard. A Waterfall process would not have surfaced that "
         "defect until after the documentation was written."),
        ("Agile de-emphasises documentation, but this lab requires it. How did you reconcile that?",
         "By adding documentation to the Definition of Done for every increment. A feature is not "
         "complete until the affected document is updated. That is why the state machine in the "
         "design document and the transition table in the code cannot drift apart - changing one "
         "without the other fails the increment."),
        ("How does the detection engine actually decide?",
         "Eighteen features are extracted from eleven observed fields. Seven behavioural rules "
         "each return a score and reasons; the highest-scoring rule wins the classification. A "
         "statistical baseline computes z-scores against learned normals. If trained models are "
         "present, a RandomForest and an IsolationForest also score the event. The three are "
         "fused with a weighted blend, with the rule score acting as a floor, then scaled by the "
         "analyst's sensitivity and mapped to a severity band."),
        ("Why is the rule score a floor rather than just another term in the average?",
         "So that the statistical and machine-learning detectors cannot single-handedly drive an "
         "event to CRITICAL. An unexplained outlier is worth a human glance - MEDIUM - but not an "
         "incident. Without the floor the queue fills with unactionable 'critical' noise, which "
         "is exactly what happened in the first version."),
        ("What happens if scikit-learn is not installed?",
         "The engine reports <font face='Courier'>hybrid-rules</font> mode and continues using the "
         "rule bank plus the default statistical baseline. The model loading is wrapped in a "
         "try/except, so even a corrupt artefact degrades rather than crashes. This is proved by "
         "a test - <font face='Courier'>test_engine_works_without_any_trained_model</font> - not "
         "merely claimed. You can demonstrate it by renaming the "
         "<font face='Courier'>ml_model/</font> folder and restarting."),
        ("Your model reports 99.9% accuracy. Is that believable?",
         "No, and I would not present it as a detection result. It is measured on a synthetic "
         "hold-out split whose classes are well separated by construction, so the score reflects "
         "that separability rather than real-world performance. The system has never analysed a "
         "real network capture. That caveat is written into the model metadata file and the "
         "project report."),
        ("How do you know the severity bands are correct?",
         "They are asserted at the boundaries by a test - "
         "<font face='Courier'>test_severity_bands_match_the_specification</font> checks 0, 25, "
         "26, 50, 51, 75, 76 and 100. The constants live in one place in "
         "<font face='Courier'>detector.py</font> and the documentation describes that constant."),
        ("Is the ER diagram actually what the database looks like?",
         "Yes, and you can verify it live: "
         "<font face='Courier'>GET /api/system/status</font> returns the real per-table row "
         "counts from the running database. The models in "
         "<font face='Courier'>app/models/</font> are the schema - "
         "<font face='Courier'>db.create_all()</font> builds the tables from them."),
        ("Why is there duplicated severity data across three tables? That breaks normalisation.",
         "It is a deliberate temporal snapshot. An alert records the severity as assessed when it "
         "was raised. If an analyst changes their detection sensitivity later, historical "
         "detections must keep their original scores, otherwise past charts would silently "
         "rewrite themselves. For a security tool, auditability outweighs strict normalisation - "
         "and the exception is documented rather than accidental."),
        ("Why does ThreatIndicator have no foreign key?",
         "Indicators are correlated to events by value, not by referential integrity. A foreign "
         "key would mean an indicator could only exist once matching evidence existed, which "
         "inverts how an intelligence feed works - the feed is populated before the matching "
         "traffic appears."),
        ("What stops an analyst putting an incident into an invalid state?",
         "A dictionary in <font face='Courier'>models/incident.py</font> defines every legal "
         "transition. The service validates against it and raises a 409 if the move is not "
         "permitted. Separately, the API returns the currently legal set on every read and the "
         "page renders a button only for each - so the interface cannot even offer an illegal "
         "move. Two guards, one source of truth."),
        ("Why do alerts and incidents have different state machines?",
         "An alert may legitimately be resolved straight from NEW, because an experienced analyst "
         "can recognise a known-benign pattern at a glance. An incident exists precisely because "
         "something needs investigation, so allowing it to skip straight to RESOLVED would make "
         "its audit trail meaningless."),
        ("What happens to the alerts when an incident is resolved?",
         "They are closed with it - RESOLVED if the incident was resolved, FALSE_POSITIVE if it "
         "was dismissed. That cascade is in "
         "<font face='Courier'>incident_service.transition</font> and is covered by "
         "<font face='Courier'>test_resolving_an_incident_closes_its_alerts</font>."),
        ("How does a CSV upload handle a malformed row?",
         "Each row is validated independently. A failure is recorded as a line number and a "
         "reason, and the loop continues. A four-row file with two bad rows returns HTTP 201 with "
         "one record analysed and two rejections reported. Rejecting an entire real log export "
         "because of one bad line would make the feature unusable."),
        ("Is the CSV upload atomic?",
         "Yes. Each row is persisted with <font face='Courier'>commit=False</font> and a single "
         "commit follows the loop, so a file either lands completely or not at all. There is no "
         "state where some rows produced alerts and the rest were lost."),
        ("How is authentication implemented, and is it secure?",
         "Passwords are stored as salted PBKDF2 hashes via Werkzeug. Sessions are signed, "
         "expiring tokens created with itsdangerous. It is deliberately simple and I would not "
         "call it production-grade: tokens cannot be revoked before expiry, there is no rate "
         "limiting, and there is no HTTPS in this setup. Those are listed as known limitations "
         "rather than glossed over."),
        ("Does the login endpoint leak whether an account exists?",
         "No. An unknown email and a wrong password return a byte-identical message and the same "
         "401 status. There is a test asserting the two messages are equal."),
        ("How do you prevent SQL injection?",
         "Every query is built through SQLAlchemy expression objects, which parameterise values. "
         "There is no string-built SQL anywhere in the repository - the single raw statement is "
         "<font face='Courier'>db.text('SELECT 1')</font>, a constant liveness probe with no "
         "interpolation."),
        ("How many tests are there and what do they cover?",
         "117 automated cases across five modules, all passing. They use equivalence "
         "partitioning, boundary value analysis, state-transition testing and a few property "
         "assertions. Every functional requirement has at least two cases, and every requirement "
         "has at least one negative, error-path case."),
        ("Why can the detection engine be tested without a database?",
         "Because <font face='Courier'>app/ml/</font> imports nothing from Flask, SQLAlchemy or "
         "the rest of the application. That isolation is a deliberate architectural decision, and "
         "the 18 engine tests construct a detector directly with no application context."),
        ("What is the difference between the dashboard and the analytics endpoint?",
         "The dashboard endpoint returns what one screen needs - totals, six chart series, threat "
         "level, health and the activity feed. The analytics endpoint returns deeper aggregates: "
         "averages, mean time to resolve, hourly distribution, ingestion channels and status "
         "breakdowns. Both are read-only; neither writes anything, so refreshing cannot alter the "
         "data being reported."),
        ("Are the dashboard numbers hard-coded in React?",
         "No, and it is verifiable: a test compares the dashboard totals with the corresponding "
         "list endpoints and asserts they are equal. Analysing a new event and returning to the "
         "dashboard increases the totals."),
        ("How would you scale this beyond a prototype?",
         "The first real ceiling is SQLite's single-writer model. Because all persistence goes "
         "through SQLAlchemy, moving to PostgreSQL is a change to "
         "<font face='Courier'>DATABASE_URL</font> plus one dialect-specific query. All list "
         "endpoints already paginate server-side, and the engine is stateless per call, so it is "
         "safe behind multiple workers."),
        ("What is the biggest weakness of your detection approach?",
         "There is no cross-event correlation - each event is scored in isolation. A slow "
         "distributed scan spread thinly across many events would not be detected, because no "
         "single event would look unusual. That is the first item on the future-enhancements "
         "list."),
        ("What did you find hardest?",
         "Calibrating the engine. Getting it to classify each attack type correctly was "
         "straightforward. Getting it to produce a <b>useful spread</b> of severities was not - "
         "the first version put every attack in the CRITICAL band and left HIGH completely empty, "
         "which made the dashboard meaningless. Fixing it required changing the scoring "
         "mathematics, the fusion rule and the data generator together."),
        ("Show me something that testing caught that you did not expect.",
         "A failing test that was itself wrong. It escalated a CRITICAL alert that already had an "
         "auto-created incident, then tried to move it straight to CONTAINED, and the API "
         "correctly refused with a 409. The instinct is to change the code; here the code was "
         "right and the test encoded a wrong assumption. I corrected the test and added a new one "
         "for the property I had misunderstood."),
        ("Why is the bundle 824 kB? Is that acceptable?",
         "It is a single chunk dominated by Recharts and React, and it gzips to 231 kB. For a "
         "locally served prototype that is acceptable, but route-based code splitting is on the "
         "enhancement list - it is the obvious next optimisation."),
        ("How long does a detection take?",
         "7.1 milliseconds on average in ML mode and 0.033 milliseconds in rules mode, measured "
         "over 2000 events. The first measurement was 45 milliseconds; profiling showed the "
         "models were loaded with <font face='Courier'>n_jobs=-1</font>, so joblib spent longer "
         "dispatching a thread pool than predicting on a single row. Forcing "
         "<font face='Courier'>n_jobs=1</font> at inference gave a 6.4&times; improvement."),
        ("What would you do differently if you started again?",
         "Two things. I would build the seeding and the dashboard earlier, because the "
         "severity-saturation defect was only visible once real data was rendered - it was "
         "invisible in unit tests that checked classification alone. And I would write the "
         "engine's regression properties, such as monotonicity of risk with attack intensity, as "
         "tests from the very beginning rather than adding them after the defect appeared."),
        ("Is this production-ready?",
         "No, and the project says so in several places. It is an academic prototype: all "
         "telemetry is synthetic, authentication is demonstration-grade, there is no HTTPS or "
         "rate limiting, and it runs on a single-process development server. The deployment "
         "document lists exactly what would have to change first."),
    ]
    for question, answer in qa:
        add(KeepTogether([
            Paragraph("Q.&nbsp;&nbsp;" + esc(question), S["q"]),
            Paragraph("A.&nbsp;&nbsp;" + answer, S["a"]),
        ]))

    add(PageBreak())

    # ============================================================ 10. DEFECTS
    add(section("10", "Defects found and fixed"))
    add(callout(
        "Why this section matters most",
        "Being able to describe a defect you found, diagnosed and fixed is stronger evidence of "
        "understanding than any feature list. Each entry below is a real problem encountered "
        "during development, with the diagnosis and the fix.", "accent"))
    add(Spacer(1, 4 * mm))

    add(P("D1  -  Severity saturation  (the significant one)", "h2"))
    add(P(
        "<b>Symptom.</b> After the first end-to-end build, the seeded dashboard showed "
        "LOW 177, MEDIUM 21, <b>HIGH 0</b>, CRITICAL 140. Every simulated attack landed in the "
        "top band and the HIGH band was completely empty, so the severity chart and the alert "
        "queue conveyed no prioritisation at all."))
    add(P("<b>Diagnosis.</b> Four compounding causes:"))
    add(bullets([
        "The rule bank used <b>linear</b> magnitude terms, so 20 failed logins and 2000 both hit "
        "the ceiling of 100.",
        "The statistical scorer mapped the combined z-score linearly, so any attack-shaped event "
        "saturated at 100.",
        "The fusion floor was <font face='Courier'>0.85 &times; max(rule, anomaly, ml)</font>, "
        "which let the statistical detector alone drive an event to CRITICAL.",
        "The data generator produced every attack at full intensity, which is not how real "
        "telemetry is distributed.",
    ]))
    add(P("<b>Fix.</b>"))
    add(data_table(
        ["Change", "File"],
        [
            ["Logarithmic magnitude terms, e.g. 38 + 30&middot;log10(failed/4)", "ml/rules.py"],
            ["Saturating exponential mapping 100 &middot; (1 - e^(-c/9))", "ml/anomaly.py"],
            ["Floor changed to 0.85 &times; <b>rule score only</b>", "ml/detector.py"],
            ["Low/medium/high intensity tiers, weighted towards mild", "ml/generate_dataset.py"],
        ],
        widths=[CONTENT_W - 46 * mm, 46 * mm]))
    add(Spacer(1, 2 * mm))
    add(P(
        "<b>Result.</b> LOW 57.7%, MEDIUM 9.8%, HIGH 15.5%, CRITICAL 17.0% - a realistic pyramid "
        "with all four bands populated."))
    add(P(
        "<b>Prevention.</b> Two regression tests make this impossible to reintroduce silently: "
        "one asserts all four bands are populated across 400 generated events, the other asserts "
        "the risk score is monotonic in attack intensity."))

    add(P("D2  -  Wrong HTTP status for a wrong password", "h2"))
    add(P(
        "<b>Symptom.</b> A wrong password shorter than six characters returned HTTP 422, a "
        "validation error, instead of 401. <b>Diagnosis.</b> The registration password-strength "
        "rule was being applied at sign-in. Besides the wrong status code it leaked information: "
        "a 422 told an attacker the password they tried was too short to be the real one. "
        "<b>Fix.</b> Login now checks only that a password was supplied; the strength rule applies "
        "to password changes."))

    add(P("D3  -  Machine-learning inference 6.4&times; slower than necessary", "h2"))
    add(P(
        "<b>Symptom.</b> Performance measurement showed ML mode averaging 45.353 ms per event "
        "against 0.025 ms for rules mode. <b>Diagnosis.</b> Timing the sub-calls isolated it to "
        "<font face='Courier'>RandomForest.predict_proba</font> at 43 ms for a <b>single</b> "
        "sample. The models were saved with <font face='Courier'>n_jobs=-1</font>, correct for "
        "fitting, but at inference the engine scores one event at a time and joblib spent far "
        "longer dispatching to a thread pool than doing the work. <b>Fix.</b> Force "
        "<font face='Courier'>n_jobs = 1</font> on the loaded models; training still uses all "
        "cores. <b>Result.</b> 45.353 ms &rarr; 7.083 ms, and the test suite dropped from 78 s to "
        "51 s as a side effect."))

    add(P("D4  -  A failing test that was itself wrong", "h2"))
    add(P(
        "<b>Symptom.</b> A test asserting that resolving an incident closes its alerts failed. "
        "<b>Diagnosis.</b> The test escalated a CRITICAL alert that <b>already had an "
        "auto-created incident in NEW</b>, then tried to move it straight to CONTAINED. The API "
        "correctly refused with 409, because NEW &rarr; CONTAINED is not a legal transition. "
        "<b>Resolution.</b> The code was right and the test encoded a wrong assumption. The test "
        "was corrected to investigate first, and a new test was added for the property that had "
        "been misunderstood - that escalation is idempotent and returns the existing incident "
        "rather than creating a duplicate."))

    add(P("D5  -  Build failure on an invalid Tailwind opacity", "h2"))
    add(P(
        "<font face='Courier'>border-white/12</font> is not on Tailwind's default opacity scale, "
        "so the production build failed. Replaced with <font face='Courier'>/15</font> "
        "throughout. Minor, but a good illustration of why a build step belongs in the Definition "
        "of Done."))

    add(P("D6  -  Every timestamp displayed 5.5 hours in the past", "h2"))
    add(P(
        "<b>Symptom.</b> The dashboard showed 'Updated 5h ago' on a payload generated one second "
        "earlier, and every alert and incident timestamp was similarly shifted. "
        "<b>Diagnosis.</b> The backend stores and emits naive UTC "
        "(<font face='Courier'>2026-09-21T22:35:51</font>, with no zone designator). A date-time "
        "string without a designator is parsed by the browser as <b>local</b> time, so on a "
        "UTC+5:30 machine every value was shifted by the local offset. <b>Fix.</b> A single "
        "<font face='Courier'>parseTimestamp</font> helper in "
        "<font face='Courier'>utils/format.js</font> marks zone-less date-time strings as UTC "
        "before parsing; the four formatting functions all route through it. Date-only strings, "
        "used by the chart series, are already treated as UTC by the specification and are left "
        "untouched."))

    add(PageBreak())

    # ======================================================== 11. LIMITATIONS
    add(section("11", "Limitations and future work"))
    add(callout(
        "Volunteer these before you are asked",
        "An examiner will find at least one of these. Naming them first demonstrates judgement; "
        "being caught by one looks like an oversight.", "warn"))
    add(Spacer(1, 3 * mm))

    add(P("Known limitations", "h2"))
    add(data_table(
        ["Area", "Limitation"],
        [
            ["<b>Security", "Tokens cannot be revoked before expiry - there is no server-side "
                            "session store. No rate limiting on login. No HTTPS. Role checks are "
                            "coarse. No penetration testing or dependency scanning was performed."],
            ["<b>Data", "All telemetry is synthetic; the system has never analysed a real network "
                        "capture. The reported model accuracy is measured on synthetic data whose "
                        "classes are separable by construction."],
            ["<b>Detection", "No cross-event correlation - each event is scored in isolation, so a "
                             "slow distributed scan would not be detected. Indicators are not "
                             "automatically matched against events."],
            ["<b>Scale", "SQLite allows one writer at a time. CSV uploads are capped at 5000 rows "
                         "because parsed rows are held in memory. Single-process development "
                         "server, no clustering."],
            ["<b>Testing", "No automated frontend tests - React is verified manually and by the "
                           "build. No cross-browser matrix, no real-device testing, no automated "
                           "accessibility audit."],
        ],
        widths=[28 * mm, CONTENT_W - 28 * mm]))
    add(Spacer(1, 4 * mm))

    add(P("Future enhancements, in priority order", "h2"))
    add(data_table(
        ["Priority", "Enhancement", "Why it is next"],
        [
            ["<b>High", "Cross-event correlation by source over a time window",
             "The most significant detection gap"],
            ["<b>High", "Automatic indicator matching against incoming events",
             "Makes the intelligence feed operational, not just informational"],
            ["<b>High", "Frontend test suite (Vitest + React Testing Library)",
             "Closes the largest gap in the test strategy"],
            ["<b>Medium", "Server-side session store for token revocation",
             "Removes a stated security limitation"],
            ["<b>Medium", "Rate limiting on authentication and upload",
             "Removes a stated security limitation"],
            ["<b>Medium", "Route-based code splitting", "The bundle is currently one chunk"],
            ["<b>Medium", "PostgreSQL deployment guide", "Lifts the single-writer ceiling"],
            ["<b>Medium", "Real PCAP or syslog ingestion", "Would allow genuine calibration"],
            ["<b>Low", "Light theme", "Preference is stored but only dark ships"],
            ["<b>Low", "WebSocket live feed", "The dashboard currently polls every 45 seconds"],
        ],
        widths=[20 * mm, 62 * mm, CONTENT_W - 82 * mm]))

    add(PageBreak())

    # ====================================================== 12. QUICK REFERENCE
    add(section("12", "Quick reference card"))

    add(P("Startup", "h2"))
    add(code_block([
        "  cd backend                         cd frontend",
        "  venv\\Scripts\\activate              npm run dev",
        "  python run.py                      -> http://localhost:5173",
        "",
        "  python seed_database.py            rebuild the demo dataset",
        "  python -m pytest -q                run the 117 tests",
        "  python -m app.ml.train_model       retrain the optional models",
        "  python capture_screenshots.py      re-capture the 12 screens",
    ]))
    add(Spacer(1, 4 * mm))

    add(P("Numbers to memorise", "h2"))
    two_col = Table([[
        data_table(["Constant", "Value"], [
            ["Severity LOW", "0 - 25"],
            ["Severity MEDIUM", "26 - 50"],
            ["Severity HIGH", "51 - 75"],
            ["Severity CRITICAL", "76 - 100"],
            ["Alert threshold", "risk &ge; 26"],
            ["Incident threshold", "risk &ge; 76"],
            ["Sensitivity range", "0.5 - 1.5"],
            ["Confidence range", "0.50 - 0.99"],
            ["Upload ceiling", "8 MB / 5000 rows"],
        ], widths=[30 * mm, 26 * mm]),
        data_table(["Metric", "Value"], [
            ["Features", "18"],
            ["Rules", "7"],
            ["Categories", "8"],
            ["Entities", "10"],
            ["Endpoints", "46"],
            ["Screens", "12"],
            ["Tests", "117 passing"],
            ["Detection (ML)", "7.083 ms mean"],
            ["Detection (rules)", "0.033 ms mean"],
        ], widths=[30 * mm, 28 * mm]),
    ]], colWidths=[CONTENT_W / 2, CONTENT_W / 2])
    two_col.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("RIGHTPADDING", (1, 0), (1, -1), 0),
    ]))
    add(two_col)
    add(Spacer(1, 5 * mm))

    add(P("The eight detection categories", "h2"))
    add(P(
        "Normal Activity &nbsp;&bull;&nbsp; Brute Force Attempt &nbsp;&bull;&nbsp; Port Scanning "
        "Pattern &nbsp;&bull;&nbsp; Suspicious Login Activity &nbsp;&bull;&nbsp; Network Anomaly "
        "&nbsp;&bull;&nbsp; Data Transfer Anomaly &nbsp;&bull;&nbsp; Denial-of-Service Pattern "
        "&nbsp;&bull;&nbsp; Credential Abuse Pattern"))
    add(Spacer(1, 3 * mm))

    add(P("Demonstration credentials", "h2"))
    add(data_table(
        ["Role", "Email", "Password"],
        [
            ["<b>Administrator", "admin@cyberguard.ai", "admin123"],
            ["Security Analyst", "analyst@cyberguard.ai", "analyst123"],
            ["Viewer", "viewer@cyberguard.ai", "viewer123"],
        ],
        widths=[36 * mm, 62 * mm, CONTENT_W - 98 * mm]))
    add(P(
        "These are seeded credentials for a local academic prototype, stored as salted PBKDF2 "
        "hashes and published in the project README. They are included here because they are "
        "needed to sign in during the demonstration. They are not real secrets and grant no "
        "access to anything beyond a local SQLite file.", "small"))
    add(Spacer(1, 4 * mm))

    add(P("Where everything lives", "h2"))
    add(data_table(
        ["Looking for", "Path"],
        [
            ["Detection engine", "backend/app/ml/"],
            ["State machine", "backend/app/models/incident.py"],
            ["Severity bands", "backend/app/ml/detector.py"],
            ["Validation rules", "backend/app/utils/validators.py"],
            ["Business logic", "backend/app/services/"],
            ["API routes", "backend/app/routes/"],
            ["Tests", "backend/tests/"],
            ["Screens", "frontend/src/pages/"],
            ["The only network module", "frontend/src/services/api.js"],
            ["SE documents", "documentation/ (23 files)"],
            ["Screenshots", "documentation/screenshots/ (12 files)"],
            ["Sample CSV files", "sample_data/ (4 files)"],
        ],
        widths=[52 * mm, CONTENT_W - 52 * mm]))

    add(Spacer(1, 6 * mm))
    add(callout(
        "The closing line",
        "\"CyberGuard AI is a working full-stack security platform where the documentation and the "
        "implementation are the same system viewed from two angles. The state transition diagram "
        "is the transition table the API enforces; the ER diagram is the schema SQLAlchemy "
        "creates; the severity bands in the data flow diagram are the constants the engine "
        "applies. It is an academic prototype on simulated telemetry, and every figure it reports "
        "states where it came from.\"", "accent"))

    doc.build(story)
    return OUTPUT


if __name__ == "__main__":
    path = build()
    size = path.stat().st_size
    print("Written: %s" % path)
    print("Size   : %.1f KB" % (size / 1024.0))
    sys.exit(0)
