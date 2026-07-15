"""Generate the SETU hackathon detailed submission document."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "SETU_ET_AI_Hackathon_Detailed_Submission.pdf"
REPLAY_SCREENSHOT = ROOT / "docs" / "assets" / "setu-replay.png"

NAVY = colors.HexColor("#0B1736")
BLUE = colors.HexColor("#1769E0")
SKY = colors.HexColor("#EAF3FF")
INK = colors.HexColor("#182230")
MUTED = colors.HexColor("#526070")
GREEN = colors.HexColor("#087E5B")
LINE = colors.HexColor("#D7E0EC")


def p(text, style):
    return Paragraph(text, style)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(40, 32, A4[0] - 40, 32)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(40, 20, "SETU | ET AI Hackathon 2.0 | Detailed Submission")
    canvas.drawRightString(A4[0] - 40, 20, f"Page {doc.page}")
    canvas.restoreState()


def section_title(title, subtitle, styles):
    return [
        Spacer(1, 10),
        p(title, styles["Section"]),
        p(subtitle, styles["Subsection"]),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1, color=LINE),
        Spacer(1, 10),
    ]


def bullet(items, styles):
    out = []
    for item in items:
        out.append(p(f'<font color="#1769E0">&#8226;</font> {item}', styles["Body"]))
        out.append(Spacer(1, 3))
    return out


def make_table(rows, widths, styles):
    data = [[p(cell, styles["TableHead"] if r == 0 else styles["TableBody"]) for cell in row] for r, row in enumerate(rows)]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, LINE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFD")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=42,
        bottomMargin=46,
        title="SETU - ET AI Hackathon Detailed Submission",
        author="SETU Team",
    )
    base = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle("Title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=28, leading=33, textColor=NAVY, alignment=TA_LEFT, spaceAfter=10),
        "Kicker": ParagraphStyle("Kicker", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=BLUE, tracking=0.4),
        "Lead": ParagraphStyle("Lead", parent=base["Normal"], fontName="Helvetica", fontSize=13, leading=18, textColor=INK, spaceAfter=10),
        "Section": ParagraphStyle("Section", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=NAVY, spaceAfter=2),
        "Subsection": ParagraphStyle("Subsection", parent=base["Normal"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=MUTED),
        "Body": ParagraphStyle("Body", parent=base["Normal"], fontName="Helvetica", fontSize=9.4, leading=14, textColor=INK, spaceAfter=6),
        "Small": ParagraphStyle("Small", parent=base["Normal"], fontName="Helvetica", fontSize=8.1, leading=11, textColor=MUTED),
        "TableHead": ParagraphStyle("TableHead", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8.2, leading=10.2, textColor=colors.white),
        "TableBody": ParagraphStyle("TableBody", parent=base["Normal"], fontName="Helvetica", fontSize=8.1, leading=10.6, textColor=INK),
        "Callout": ParagraphStyle("Callout", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=GREEN),
    }

    story = []
    story += [
        Spacer(1, 22),
        p("ET AI HACKATHON 2.0 | PROBLEM STATEMENT 2", styles["Kicker"]),
        Spacer(1, 12),
        p("SETU", styles["Title"]),
        p("Strategic Energy Trade Intelligence", styles["Lead"]),
        HRFlowable(width="100%", thickness=3, color=BLUE),
        Spacer(1, 18),
        p("AI-powered energy supply-chain resilience for import-dependent economies.", styles["Lead"]),
        p("SETU converts a source-grounded geopolitical disruption into an auditable operational decision trail: evidence, corridor risk, forecast, cascade simulation, and explainable mitigation options for human approval.", styles["Body"]),
        Spacer(1, 16),
    ]
    cover = Table(
        [
            [p("PROBLEM", styles["TableHead"]), p("WHY IT MATTERS", styles["TableHead"])],
            [p("Import-dependent crude supply is exposed to disruption in a small number of maritime corridors.", styles["TableBody"]), p("A decision team needs a defensible response path - not a stream of alerts - when a corridor is threatened.", styles["TableBody"])],
        ],
        colWidths=[2.45 * inch, 4.25 * inch],
    )
    cover.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("BACKGROUND", (0, 1), (-1, 1), SKY), ("GRID", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 11), ("RIGHTPADDING", (0, 0), (-1, -1), 11), ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    story += [
        cover,
        Spacer(1, 18),
        p("<b>Evidence-backed early warning:</b> SETU flagged elevated Hormuz risk on 10 February 2026 - 20 days before the publicly reported 2 March closure of the Strait of Hormuz.", styles["Callout"]),
        Spacer(1, 8),
        p("React + FastAPI + SQLite | source evidence + simulation + human-in-the-loop decisions | reproducible N=1 replay with a 17-day baseline caveat", styles["Small"]),
        PageBreak(),
    ]

    story += section_title("Verified Hormuz replay", "A reproducible early-warning result, not a retrospective threshold fit", styles)
    story += [
        p("SETU crossed its pre-locked Hormuz risk threshold on <b>10 February 2026</b>, 20 days before the public reference event: the 2 March closure reported by the U.S. Energy Information Administration (EIA).", styles["Body"]),
        p("The threshold (<b>0.437501</b>) was derived only from a separate 17-day January baseline, before the Feb 1-Mar 2 evaluation window. The replay crossing score was <b>0.578125</b>; the trajectory peaked at <b>0.816089</b> on 2 March.", styles["Body"]),
        Image(str(REPLAY_SCREENSHOT), width=6.7 * inch, height=4.35 * inch),
        Spacer(1, 5),
        p("Hormuz replay: crossed status, 20-day lead time, geographic route context, and human approval gate. This is one historical case (N=1), not a broad claim of detection accuracy.", styles["Small"]),
        PageBreak(),
    ]

    story += section_title("1. Problem and opportunity", "Turning reactive crisis response into anticipatory supply-chain resilience", styles)
    story += [
        p("India's crude-oil supply is structurally sensitive to geopolitical and maritime disruption. A disruption at a critical corridor can cascade through port access, refinery throughput, demand fulfillment, and procurement decisions. Existing monitoring tools surface information; SETU is designed to convert that information into a transparent decision sequence.", styles["Body"]),
        p("<b>Target user:</b> energy-security, procurement, logistics, refinery-operations, and policy teams that must evaluate a response quickly while retaining human control.", styles["Body"]),
    ]
    story += [make_table([
        ["Evaluation dimension", "SETU response"],
        ["Innovation", "A source-to-decision workflow that joins evidence extraction, a corridor risk model, forecast telemetry, Monte Carlo cascades, and Pareto mitigation options."],
        ["Business impact", "Makes the effect of a corridor disruption legible before an operator commits to rerouting, reserve use, or supplier diversification."],
        ["Technical excellence", "Frozen JSON contracts, deterministic scoring/orchestration, persisted results, automated tests, and a reproducible Docker path."],
        ["Scalability", "Composable API layers and schema-driven contracts allow more sources, corridors, and operational data feeds to be added."],
        ["User experience", "An operational incident-analysis workflow and evidence-first explanations reduce cognitive load during a crisis."],
    ], [1.42 * inch, 5.28 * inch], styles), Spacer(1, 14)]

    story += section_title("2. Product workflow", "A clear chain of custody from source evidence to recommended response", styles)
    story += [
        p("SETU is not presented as a black-box predictor. Every stage exposes an observable artifact that a decision-maker can inspect.", styles["Body"]),
        make_table([
            ["Stage", "System action", "What the operator sees"],
            ["Evidence", "Ingest a source URL or GDELT signal; extract corridor, event type, severity, evidence terms, and confidence.", "Article title, publisher, source link, timestamps, confidence, and matched terms."],
            ["Risk", "Update corridor-level risk score through deterministic scoring.", "Affected corridor and updated risk state."],
            ["Forecast", "Generate short-horizon risk telemetry from available feature data.", "Forecast dates and uncertainty-aware risk values."],
            ["Cascade", "Propagate the corridor disruption through the crude network using Monte Carlo simulation.", "Scenario identifier and downstream impact bands."],
            ["Mitigation", "Rank response options using risk/time/cost trade-offs.", "Pareto-oriented options, rationale, and explicit approve/reject controls."],
        ], [0.78 * inch, 3.13 * inch, 2.79 * inch], styles),
        Spacer(1, 12),
        p("<b>Operational incident analysis:</b> one action runs a credible reference source through the complete sequence - source evidence -> HORMUZ risk update -> forecast -> cascade -> mitigation options. It provides a repeatable, inspectable operational workflow.", styles["Callout"]),
    ]

    story += [PageBreak()]
    story += section_title("3. Technical architecture", "Neuro-symbolic by design: AI-assisted extraction, deterministic decisions", styles)
    story += [
        p("The system separates interpretation from decision logic. Extraction may use rules or an LLM-backed path, while risk scoring, simulation, and recommendation ranking remain deterministic and inspectable. This is deliberate: in a high-consequence supply decision, explainability and repeatability matter as much as model sophistication.", styles["Body"]),
        make_table([
            ["Layer", "Implementation", "Purpose"],
            ["Experience", "React, Vite, Leaflet, Recharts", "Interactive dashboard, map, evidence, forecast, cascade and recommendation views."],
            ["API", "FastAPI", "Typed endpoints for signals, forecasts, cascades, recommendations, health, and contracts."],
            ["Intelligence", "Rule/LLM extraction + deterministic risk scoring", "Convert a geopolitical text signal into a structured corridor event."],
            ["Simulation", "Network graph + Monte Carlo", "Represent and propagate disruption through ports, refineries, and demand nodes."],
            ["Decision", "Pareto-style orchestrator + HITL", "Expose mitigation trade-offs; humans approve or reject the action."],
            ["Persistence", "SQLite", "Keep signals, forecasts, cascades, recommendations, and audit state reproducible for the prototype."],
            ["Contracts", "JSON Schema + generated types", "Maintain a single source of truth between frontend and backend."],
        ], [1.08 * inch, 2.15 * inch, 3.47 * inch], styles),
    ]

    story += section_title("4. Data credibility and explainability", "Make the evidence visible before asking a user to trust the result", styles)
    story += bullet([
        "URL ingestion retains <b>source URL, publisher, title, publication/scrape timestamps, confidence, and matched evidence terms</b> in the UI.",
        "The dashboard labels source-grounded items and de-emphasizes weak or zero-contribution seeded rows, preventing synthetic reference data from being mistaken for live evidence.",
        "Recommendations show <b>why</b> an option is proposed and surface its risk reduction, time penalty, and cost trade-off before approval.",
        "The application supports cached samples for reproducible offline operation and optional external data sources including GDELT, OFAC, EIA, and FRED as documented in the repository.",
    ], styles)
    story += [Spacer(1, 7), make_table([
        ["Claim", "Evidence in the product"],
        ["Not just a news summary", "The source triggers a corridor-specific risk update, forecast, simulation, and mitigation sequence."],
        ["Not a hard-coded dashboard", "The incident-analysis workflow performs API actions in sequence and renders the returned evidence, forecast, cascade, and recommendations."],
        ["Not autonomous procurement", "Human-in-the-loop approve/reject controls remain at the final recommendation stage."],
        ["Honest uncertainty", "Forecast and cascade panels use risk/impact bands; documented limitations identify the boundaries of the MVP."],
    ], [2.05 * inch, 4.65 * inch], styles)]

    story += [PageBreak()]
    story += section_title("5. Prototype validation", "Evidence that the submitted path runs end to end", styles)
    story += [
        p("The current prototype has been validated through backend regression tests, a frontend production build, Docker startup with a healthy API, and an in-browser run of operational incident analysis. The verified workflow completed all five stages and rendered AP evidence, a HORMUZ risk update, forecast output, a cascade scenario, and three mitigation options.", styles["Body"]),
        make_table([
            ["Check", "Result"],
            ["Backend regression suite", "217 tests passed; the Phase 7 edge-case sweep also passed."],
            ["Frontend production build", "Passed; Vite emitted only a bundle-size advisory."],
            ["Containerised stack", "Docker build completed; backend health endpoint became available; frontend served at port 5173."],
            ["Browser verification", "No console errors on the dashboard; operational incident analysis completed all 5 stages; maps, route simulation, and replay were checked."],
            ["Calibrated Hormuz replay", "Crossed 0.437501 on 10 Feb 2026 (score 0.578125), 20 days before the 2 March EIA reference event; N=1 and 17-day-baseline caveats documented."],
            ["Repository hygiene", "The private SRS build-plan working document is ignored and excluded from the intended submission commit."],
        ], [2.25 * inch, 4.45 * inch], styles),
    ]

    story += section_title("6. Product walkthrough", "A focused 3-4 minute explanation of the operational workflow", styles)
    story += [make_table([
        ["Time", "Show", "Narration"],
        ["0:00-0:25", "SETU landing explanation", "SETU detects geopolitical supply-chain shocks, maps affected crude corridors, forecasts risk, simulates downstream impact, and recommends mitigation."],
        ["0:25-0:55", "Credibility panel", "A decision begins with evidence: source, confidence, terms, and timestamps are visible."],
        ["0:55-2:10", "Run incident analysis", "One credible reference source drives the end-to-end sequence: evidence, risk, forecast, cascade, and mitigations."],
        ["2:10-3:00", "Recommendation panel", "Each option shows why it is recommended, its trade-offs, and the human approval gate."],
        ["3:00-3:30", "Limitations and close", "This is an auditable decision-support MVP; expanded AIS, broader validation, and live operational integrations are next."],
    ], [0.75 * inch, 1.75 * inch, 4.2 * inch], styles)]

    story += [PageBreak()]
    story += section_title("7. Responsible scope and roadmap", "What SETU proves now, and what a production deployment still needs", styles)
    story += [
        p("SETU makes explicit choices about scope rather than hiding them. It is an MVP for decision support, not a replacement for maritime intelligence, price analytics, or procurement governance.", styles["Body"]),
        make_table([
            ["Current MVP boundary", "Production extension"],
            ["English-language source text", "Multilingual extraction with domain validation."],
            ["No AIS vessel tracking", "Integrate vessel, port congestion, and tanker-availability feeds."],
            ["Crude throughput model", "Extend to refined products, refinery compatibility, and inventory policy."],
            ["Up to 7-day forecast horizon", "Calibrated longer-horizon models with ongoing backtesting."],
            ["One historical backtest crisis", "Multiple event windows, baselines, and independent validation."],
            ["Single-node prototype persistence", "Role-based access, audit controls, event streaming, and resilient operational infrastructure."],
        ], [2.75 * inch, 3.95 * inch], styles),
        Spacer(1, 15),
        p("<b>Next milestone:</b> connect validated AIS, supplier, refinery, and market data feeds; calibrate the network model with domain partners; and measure detection lead time and recommendation quality against real operating scenarios.", styles["Callout"]),
    ]

    story += section_title("8. How to run", "Reproducible local deployment", styles)
    story += [
        p("<b>Prerequisite:</b> Docker Desktop (Windows/macOS) or Docker Engine with Docker Compose (Linux).", styles["Body"]),
        p("<font face=\"Courier\">git clone https://github.com/Yumekaz/SETU.git<br/>cd SETU<br/>docker compose up --build</font>", styles["Body"]),
        p("Open <b>http://127.0.0.1:5173</b>, select <b>Run incident analysis</b>, then inspect the evidence and recommendation panels. The API health endpoint is available at <b>http://127.0.0.1:8000/health</b>.", styles["Body"]),
        Spacer(1, 12),
        p("Repository documentation includes architecture, data-source notes, known limitations, validation materials, a product walkthrough script, and a video outline.", styles["Body"]),
        Spacer(1, 20),
        HRFlowable(width="100%", thickness=2, color=BLUE),
        Spacer(1, 12),
        p("SETU: from geopolitical signal to an explainable energy-supply decision.", styles["Lead"]),
        p("Thank you for evaluating our submission.", ParagraphStyle("End", parent=styles["Body"], alignment=TA_CENTER, textColor=MUTED)),
    ]

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()
