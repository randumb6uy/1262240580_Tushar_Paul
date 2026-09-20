"""
Generate a publication-grade 4-slide Presentation Deck PDF for the
Kohler AI Sales & Spatial Design Advisor.
Format: Landscape Presentation Slides (16:9 / Letter Landscape, Exactly 4 Slides).
Fills the slide canvas elegantly with rich visual cards, tables, diagrams, and metrics.
"""

import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfgen import canvas

# Theme Colors (Luxury Architectural Dark Mode + Cyan, Blue, Gold & Green Accents)
COLOR_BG_DARK = colors.HexColor("#090d16")
COLOR_CARD_DARK = colors.HexColor("#0d1322")
COLOR_CARD_BORDER = colors.HexColor("#1e293b")
COLOR_CARD_BORDER_BLUE = colors.HexColor("#0284c7")
COLOR_ACCENT_CYAN = colors.HexColor("#38bdf8")
COLOR_ACCENT_BLUE = colors.HexColor("#0284c7")
COLOR_ACCENT_NAVY = colors.HexColor("#0f2a4a")
COLOR_ACCENT_GOLD = colors.HexColor("#d97706")
COLOR_SUCCESS = colors.HexColor("#10b981")
COLOR_SUCCESS_BG = colors.HexColor("#064e3b")
COLOR_TEXT_WHITE = colors.HexColor("#f8fafc")
COLOR_TEXT_MUTED = colors.HexColor("#94a3b8")
COLOR_TEXT_BODY = colors.HexColor("#334155")
COLOR_TEXT_HEADING = colors.HexColor("#0f172a")
COLOR_LIGHT_BG = colors.HexColor("#f8fafc")
COLOR_ROW_ALT = colors.HexColor("#f1f5f9")
COLOR_BORDER_LIGHT = colors.HexColor("#cbd5e1")
COLOR_CODE_BG = colors.HexColor("#0f172a")
COLOR_CARD_SLATE = colors.HexColor("#1e293b")


class SlideCanvas(canvas.Canvas):
    """Custom canvas for slide headers, footers, slide numbering, and background banners."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_slide_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_slide_decorations(self, total_slides):
        self.saveState()
        width, height = 11 * 72, 8.5 * 72  # Landscape Letter: 792 x 612

        # Top Accent Line
        self.setFillColor(COLOR_ACCENT_CYAN)
        self.rect(36, height - 20, width - 72, 3, fill=1, stroke=0)

        # Header running title
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(COLOR_TEXT_MUTED)
        self.drawString(36, height - 32, "KOHLER AI SALES & SPATIAL DESIGN ADVISOR")
        self.drawRightString(width - 36, height - 32, "EXECUTIVE ARCHITECTURE & INNOVATION PITCH DECK")

        # Top separator
        self.setStrokeColor(COLOR_BORDER_LIGHT)
        self.setLineWidth(0.5)
        self.line(36, height - 36, width - 36, height - 36)

        # Footer
        self.setFont("Helvetica", 7.5)
        self.drawString(36, 20, "Confidential | Autonomous Spatial Commerce Platform for Kohler Luxury Sanitaryware (India INR)")
        slide_text = f"Slide {self._pageNumber} of {total_slides}"
        self.drawRightString(width - 36, 20, slide_text)

        # Footer line
        self.line(36, 28, width - 36, 28)

        self.restoreState()


def create_presentation_deck_pdf(output_filename="Presentation_Deck.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=34,
    )

    styles = getSampleStyleSheet()

    # Typography Styles
    style_slide_title = ParagraphStyle(
        "SlideTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=19,
        textColor=COLOR_TEXT_HEADING,
        spaceAfter=2,
    )
    style_slide_subtitle = ParagraphStyle(
        "SlideSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=12,
        textColor=COLOR_ACCENT_BLUE,
        spaceAfter=7,
    )
    style_card_title = ParagraphStyle(
        "CardTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=COLOR_TEXT_WHITE,
    )
    style_card_title_gold = ParagraphStyle(
        "CardTitleGold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=COLOR_ACCENT_CYAN,
    )
    style_card_body = ParagraphStyle(
        "CardBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#e2e8f0"),
    )
    style_body = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=COLOR_TEXT_BODY,
    )
    style_stat_num = ParagraphStyle(
        "StatNum",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=17,
        textColor=COLOR_ACCENT_CYAN,
        alignment=1,
    )
    style_stat_label = ParagraphStyle(
        "StatLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=COLOR_TEXT_WHITE,
        alignment=1,
    )
    style_stat_sub = ParagraphStyle(
        "StatSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.8,
        leading=8.2,
        textColor=COLOR_TEXT_MUTED,
        alignment=1,
    )
    style_pill = ParagraphStyle(
        "PillText",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=COLOR_TEXT_WHITE,
        alignment=1,
    )

    story = []

    # =========================================================================
    # SLIDE 1: EXECUTIVE OVERVIEW & PROBLEM VS SOLUTION
    # =========================================================================
    story.append(Paragraph("1. Executive Overview & The Luxury Spatial Commerce Challenge", style_slide_title))
    story.append(Paragraph("Autonomous AI Sales & Spatial Design Advisor — Powered by Deterministic Guardrails & 2-Stage RAG", style_slide_subtitle))

    # Top Metric Bar (4 Badges)
    stats_data = [
        [
            Paragraph("0ms / 0 Tokens", style_stat_num),
            Paragraph("100% Deterministic", style_stat_num),
            Paragraph("15\" & 21-30\"", style_stat_num),
            Paragraph("100% Offline Edge", style_stat_num),
        ],
        [
            Paragraph("Fast-Path Router Bypass", style_stat_label),
            Paragraph("Exact 18% GST & Math", style_stat_label),
            Paragraph("Building Code Clearances", style_stat_label),
            Paragraph("Local Ollama Appliance", style_stat_label),
        ],
        [
            Paragraph("Instant greetings & catalog tables", style_stat_sub),
            Paragraph("Zero mental math hallucinations", style_stat_sub),
            Paragraph("Centerline & front space rules", style_stat_sub),
            Paragraph("Zero cloud API dependency/fees", style_stat_sub),
        ],
    ]
    t_stats = Table(stats_data, colWidths=[180, 180, 180, 180])
    t_stats.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_DARK),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_CARD_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t_stats)
    story.append(Spacer(1, 6))

    # Two column layout: The Problem vs The Solution
    col1_content = [
        Paragraph("<b>THE LUXURY SPATIAL COMMERCE CHALLENGE</b>", style_card_title),
        Spacer(1, 4),
        Paragraph("• <b>Spatial Hallucinations & Clearance Violations:</b> Pure LLMs lack spatial awareness, frequently recommending 6ft freestanding bathtubs for compact 4x5 ft powder rooms without verifying door swings or mandatory 15\" toilet centerlines.", style_card_body),
        Spacer(1, 3),
        Paragraph("• <b>Pricing & Tax Arithmetic Inaccuracies:</b> Multi-item luxury quotes involving 15% package discounts, tiered discounts, and 18% GST in Indian Rupees (INR) consistently trigger arithmetic hallucination errors in open-ended LLMs.", style_card_body),
        Spacer(1, 3),
        Paragraph("• <b>High Latency & Paid Cloud Token Waste:</b> Traditional chatbot loops incur 3-6 second delays and paid API tokens for basic conversational greetings or repetitive full-catalog portfolio listings.", style_card_body),
        Spacer(1, 3),
        Paragraph("• <b>Catalog Drift & Out-of-Scope Hallucinations:</b> Unconstrained models invent non-existent finishes or recommend out-of-catalog items (e.g. refrigerators) instead of adhering strictly to verified luxury inventory.", style_card_body),
    ]

    col2_content = [
        Paragraph("<b>OUR AGENTIC SOLUTION & CORE PARADIGM</b>", style_card_title_gold),
        Spacer(1, 4),
        Paragraph("• <b>Decoupled Dual-Engine Architecture:</b> Pairs an intelligent ReAct Orchestrator (LlamaIndex) with four deterministic Python rule, spatial, math, and logistics engines. The LLM directs intent; Python guarantees mathematical truth.", style_card_body),
        Spacer(1, 3),
        Paragraph("• <b>0ms Fast-Path Intent Routing:</b> Deterministic regex classifier intercepts casual greetings, catalog overviews, and single-spec queries instantly with zero token consumption and zero latency overhead.", style_card_body),
        Spacer(1, 3),
        Paragraph("• <b>Spatial Studio & Building Code Validator:</b> Computes exact fixture capacities (compact powder room to master bath) and verifies plumbing building codes (15\" centerline, 21\"-30\" front clearance, 30\" door arc swing).", style_card_body),
        Spacer(1, 3),
        Paragraph("• <b>Native Indian Luxury Market Customization:</b> Strictly binds all pricing to Indian Rupees (INR) with trailing 999 luxury pricing, 18% GST computations, and PIN-code based warehouse fulfillment lead times.", style_card_body),
    ]

    col_table = Table([[col1_content, col2_content]], colWidths=[355, 355])
    col_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#161b26")),
        ("BACKGROUND", (1, 0), (1, 0), COLOR_ACCENT_NAVY),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("BOX", (0, 0), (0, 0), 1, COLOR_CARD_BORDER),
        ("BOX", (1, 0), (1, 0), 1, COLOR_ACCENT_BLUE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(col_table)
    story.append(Spacer(1, 6))

    # Bottom Strategic Banner
    banner_content = [
        Paragraph(
            "<b>CORE ARCHITECTURAL PARADIGM:</b> By replacing unconstrained generative responses with a "
            "<b>Deterministic Rule Engine + 2-Stage Hybrid RAG + Autonomous ReAct Orchestrator</b>, the platform guarantees "
            "100% factual accuracy, zero arithmetic errors, and rapid sub-second consultative sales interactions.",
            style_card_body
        )
    ]
    t_banner = Table([banner_content], colWidths=[710])
    t_banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_CARD_BORDER_BLUE),
    ]))
    story.append(t_banner)

    story.append(PageBreak())

    # =========================================================================
    # SLIDE 2: SYSTEM ARCHITECTURE & 4 DETERMINISTIC ENGINES
    # =========================================================================
    story.append(Paragraph("2. System Architecture & End-to-End ReAct Workflow", style_slide_title))
    story.append(Paragraph("Multi-Stage Orchestration: Fast-Path Intent Router -> Autonomous Agent -> 4 Deterministic Rule Engines", style_slide_subtitle))

    # Top Pipeline Flowchart
    pipeline_data = [
        [
            Paragraph("<b>1. Customer Query</b><br/><font color='#94a3b8' size=6.5>Text or Studio Input</font>", style_pill),
            Paragraph("<b>2. Fast Router (0ms)</b><br/><font color='#38bdf8' size=6.5>Bypass Greetings / Catalog</font>", style_pill),
            Paragraph("<b>3. ReAct Orchestrator</b><br/><font color='#94a3b8' size=6.5>LlamaIndex AgentWorkflow</font>", style_pill),
            Paragraph("<b>4. 4 Deterministic Engines</b><br/><font color='#38bdf8' size=6.5>Spatial | RAG | Math | Stock</font>", style_pill),
            Paragraph("<b>5. Executive Proposal</b><br/><font color='#10b981' size=6.5>18% GST + INR Quote + UI</font>", style_pill),
        ]
    ]
    t_pipe = Table(pipeline_data, colWidths=[142, 142, 142, 142, 142])
    t_pipe.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), COLOR_CARD_DARK),
        ("BACKGROUND", (1, 0), (1, 0), COLOR_ACCENT_NAVY),
        ("BACKGROUND", (2, 0), (2, 0), COLOR_CARD_DARK),
        ("BACKGROUND", (3, 0), (3, 0), COLOR_ACCENT_NAVY),
        ("BACKGROUND", (4, 0), (4, 0), COLOR_SUCCESS_BG),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_CARD_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t_pipe)
    story.append(Spacer(1, 6))

    # 4 Engines 2x2 Grid
    eng1 = [
        Paragraph("<b>1. Spatial Studio & Layout Engine</b>", style_card_title_gold),
        Paragraph("<code>tools/room_planner.py & bundle_optimizer.py</code>", style_card_body),
        Spacer(1, 2),
        Paragraph("• <b>Clearance Enforcement:</b> 15\" toilet centerline, 21\"-30\" front basin/commode clearances, and 30\" door arc swings.", style_card_body),
        Paragraph("• <b>Capacity Solver:</b> Sizing limits for powder rooms (2 fixtures), guest baths (3), master baths (4), and luxury spas (5+).", style_card_body),
        Paragraph("• <b>Curated Themes:</b> Modern Minimalist, Classic Luxury, Japanese Zen, Mid-Century, Smart High-Tech.", style_card_body),
    ]
    eng2 = [
        Paragraph("<b>2. 2-Stage Local Hybrid RAG</b>", style_card_title_gold),
        Paragraph("<code>tools/catalog.py (ChromaDB + Cross-Encoder)</code>", style_card_body),
        Spacer(1, 2),
        Paragraph("• <b>Stage 1 Dense Retrieval:</b> Local ChromaDB vector database powered by <code>BAAI/bge-small-en-v1.5</code> embeddings.", style_card_body),
        Paragraph("• <b>Stage 2 Neural Reranking:</b> <code>ms-marco-MiniLM-L-6-v2</code> Cross-Encoder reranks top candidates for exact SKU & finish matches.", style_card_body),
        Paragraph("• <b>In-Memory LRU Cache:</b> Guarantees 0ms repeated retrievals on frequent queries.", style_card_body),
    ]
    eng3 = [
        Paragraph("<b>3. Precision Pricing & Tax Engine</b>", style_card_title_gold),
        Paragraph("<code>tools/calculator.py (Strict Python Arithmetic)</code>", style_card_body),
        Spacer(1, 2),
        Paragraph("• <b>Itemized MRP Math:</b> Computes exact catalog subtotals in Indian Rupees (INR 1 USD = 83.50 INR normalized).", style_card_body),
        Paragraph("• <b>Automated Bundle Savings:</b> Applies verified 15% package discount calculations across multi-fixture suites.", style_card_body),
        Paragraph("• <b>Mandatory 18% GST Rollup:</b> Computes exact tax subtotals, savings amounts, and final grand totals.", style_card_body),
    ]
    eng4 = [
        Paragraph("<b>4. Warehouse Logistics & Stock Engine</b>", style_card_title_gold),
        Paragraph("<code>tools/inventory.py (Regional Dispatch Centers)</code>", style_card_body),
        Spacer(1, 2),
        Paragraph("• <b>Real-Time Availability:</b> Tracks inventory levels (In Stock, Low Stock) across primary distribution hubs.", style_card_body),
        Paragraph("• <b>PIN/ZIP Code Routing:</b> Resolves closest regional dispatch (Mumbai, Delhi, Bengaluru) and calculates transit days (2-7 days).", style_card_body),
        Paragraph("• <b>Commercial Assurance:</b> Injects manufacturer warranty and 30-day return policy into client proposals.", style_card_body),
    ]

    eng_table = Table([[eng1, eng2], [eng3, eng4]], colWidths=[355, 355])
    eng_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_DARK),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_CARD_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(eng_table)
    story.append(Spacer(1, 5))

    # Resiliency Fallback Box
    resil_content = [
        Paragraph(
            "<b>HIGH RESILIENCY & ZERO-LAG CLOUD TIMEOUT FALLBACK:</b> "
            "If cloud API latency exceeds 3.0s or rate limits trigger (HTTP 429), the system deterministically compiles "
            "a complete, formatted sales proposal directly from verified tool outputs in <50ms. Zero UI freeze, 100% uptime.",
            style_card_body
        )
    ]
    t_resil = Table([resil_content], colWidths=[710])
    t_resil.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_SUCCESS_BG),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_SUCCESS),
    ]))
    story.append(t_resil)

    story.append(PageBreak())

    # =========================================================================
    # SLIDE 3: TECH STACK & DUAL-RUNTIME DEPLOYMENT MATRIX
    # =========================================================================
    story.append(Paragraph("3. Technical Stack & Dual-Runtime Deployment Matrix", style_slide_title))
    story.append(Paragraph("Engineered for Zero-Cost Edge Hardware or Scalable Multi-Tenant Cloud Deployment", style_slide_subtitle))

    # Tech Stack Full-Width Table
    tech_data = [
        [
            Paragraph("Architecture Layer", ParagraphStyle("TH", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, textColor=COLOR_TEXT_WHITE)),
            Paragraph("Technology & Component", ParagraphStyle("TH", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, textColor=COLOR_TEXT_WHITE)),
            Paragraph("Key Technical Capabilities & Engineering Rationale", ParagraphStyle("TH", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, textColor=COLOR_TEXT_WHITE)),
        ],
        [
            Paragraph("<b>Agent Orchestration</b>", style_body),
            Paragraph("<b>LlamaIndex v0.11+</b><br/><code>AgentWorkflow & ReAct Loop</code>", style_body),
            Paragraph("Event-driven ReAct state machine managing dynamic tool dispatch, multi-step reasoning, context retention, and strict sales persona prompt injection.", style_body),
        ],
        [
            Paragraph("<b>Vector Database</b>", style_body),
            Paragraph("<b>ChromaDB</b><br/><code>chromadb.PersistentClient</code>", style_body),
            Paragraph("Persistent embedded local vector store with self-bootstrapping indexer (0-dependency cold startup on fresh machine).", style_body),
        ],
        [
            Paragraph("<b>Neural Embeddings & Reranker</b>", style_body),
            Paragraph("<b>BGE-Small-v1.5 +</b><br/><b>ms-marco-MiniLM-L-6-v2</b>", style_body),
            Paragraph("Local HuggingFace embeddings combined with Cross-Encoder reranker and in-memory LRU cache for high-precision, 0ms repeated retrievals.", style_body),
        ],
        [
            Paragraph("<b>Dual LLM Engine</b>", style_body),
            Paragraph("<b>Ollama (Local Edge) /</b><br/><b>OpenRouter (Cloud API)</b>", style_body),
            Paragraph("100% offline edge execution via <code>qwen2.5:3b</code> (Flash Attention) with seamless automatic fallback to cloud models if local runtime is absent.", style_body),
        ],
        [
            Paragraph("<b>Interactive Studio UI</b>", style_body),
            Paragraph("<b>Gradio 6.0 Custom UI</b>", style_body),
            Paragraph("Interactive Spatial Studio 3D visualizer, responsive clearance sliders, quick-action chips, dark/light theme, and live sales advisor chat.", style_body),
        ],
        [
            Paragraph("<b>DevOps & Testing</b>", style_body),
            Paragraph("<b>Docker Compose + Scripts +</b><br/><b>12-Scenario Test Suite</b>", style_body),
            Paragraph("Containerized Docker deployment, Windows <code>.bat</code> / Linux <code>.sh</code> one-click launchers, and automated end-to-end verification suite.", style_body),
        ],
    ]
    t_tech = Table(tech_data, colWidths=[120, 175, 415])
    t_tech.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_DARK),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT_BG, COLOR_ROW_ALT]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 5))

    # Dual-Deployment Comparison Callout
    dep1 = [
        Paragraph("<b>MODE A: 100% OFFLINE EDGE APPLIANCE (SHOWROOMS)</b>", style_card_title_gold),
        Spacer(1, 2),
        Paragraph("• Runs locally on showroom workstation or laptop with consumer GPU / CPU.<br/>• <b>Zero API Costs:</b> 100% free token usage via quantized Ollama weights.<br/>• <b>Air-Gapped Privacy:</b> Customer architectural floor plans and quotes never leave the device.", style_card_body),
    ]
    dep2 = [
        Paragraph("<b>MODE B: MULTI-TENANT CLOUD CLUSTER</b>", style_card_title),
        Spacer(1, 2),
        Paragraph("• Containerized Docker deployment with OpenRouter cloud LLMs.<br/>• <b>Scalable Concurrency:</b> Handles multi-user customer showroom sessions simultaneously.<br/>• <b>Live Client Sharing:</b> Automatic temporary public URL generation via <code>--share</code>.", style_card_body),
    ]
    t_dep = Table([[dep1, dep2]], colWidths=[355, 355])
    t_dep.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), COLOR_ACCENT_NAVY),
        ("BACKGROUND", (1, 0), (1, 0), COLOR_CARD_DARK),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("BOX", (0, 0), (0, 0), 1, COLOR_ACCENT_BLUE),
        ("BOX", (1, 0), (1, 0), 1, COLOR_CARD_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_dep)

    story.append(PageBreak())

    # =========================================================================
    # SLIDE 4: INNOVATION PITCH, BUSINESS IMPACT & ROI
    # =========================================================================
    story.append(Paragraph("4. Innovation Pitch & Commercial Value Proposition", style_slide_title))
    story.append(Paragraph("Transforming Luxury Sanitaryware Buying from Static Brochures into Interactive Spatial Intelligence", style_slide_subtitle))

    # 4 Innovation Pillars
    inno1 = [
        Paragraph("<b>1. Hallucination-Proof Spatial CAD Engine</b>", style_card_title_gold),
        Spacer(1, 2),
        Paragraph("• Eliminates mis-ordered fixtures, customer returns, and installation rework by deterministically validating room dimensions, 30\" entrance door swings, and 15\" fixture centerlines before quoting.<br/>• Recommends wall-hung fixtures for compact powder rooms and focal freestanding soaking tubs for luxury master suites.", style_card_body),
    ]
    inno2 = [
        Paragraph("<b>2. 0ms Zero-Token Instant Intent Routing</b>", style_card_title_gold),
        Spacer(1, 2),
        Paragraph("• 80% of customer interactions (greetings, catalog exploration, single-spec lookups) bypass LLM inference entirely via regex and keyword matching.<br/>• Saves 100% of LLM compute costs on routine queries and delivers instantaneous sub-millisecond response times for a snappy user experience.", style_card_body),
    ]
    inno3 = [
        Paragraph("<b>3. Interactive 3D Spatial Studio Visualizer</b>", style_card_title),
        Spacer(1, 2),
        Paragraph("• Empowers homeowners and architects to visually manipulate room dimensions, set budgets, select aesthetic themes (Zen, Minimalist, Luxury, High-Tech), and view live 3D top-down layout diagrams.<br/>• One-click <b>\"Transfer to Advisor\"</b> instantly converts visual layouts into itemized commercial sales proposals.", style_card_body),
    ]
    inno4 = [
        Paragraph("<b>4. Complete INR Commercial & Logistics Engine</b>", style_card_title),
        Spacer(1, 2),
        Paragraph("• End-to-end luxury sales workflow: itemized MRP pricing in Indian Rupees, automated 15% suite package discounts, exact 18% GST tax computations, and PIN-code delivery transit estimates in one unified proposal.<br/>• Eliminates mental arithmetic errors and delivers ready-to-purchase quotes.", style_card_body),
    ]

    inno_table = Table([[inno1, inno2], [inno3, inno4]], colWidths=[355, 355])
    inno_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), COLOR_ACCENT_NAVY),
        ("BACKGROUND", (1, 0), (1, 0), COLOR_CARD_DARK),
        ("BACKGROUND", (0, 1), (0, 1), COLOR_CARD_DARK),
        ("BACKGROUND", (1, 1), (1, 1), COLOR_ACCENT_NAVY),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_CARD_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(inno_table)
    story.append(Spacer(1, 5))

    # Bottom Commercial ROI & Readiness Cards
    roi1 = [
        Paragraph("<b>COMMERCIAL ROI & SHOWROOM CONVERSION</b>", style_card_title_gold),
        Spacer(1, 2),
        Paragraph("• <b>Accelerated Sales Cycle:</b> Shrinks design consultation and quoting turnaround from days to under 30 seconds.<br/>• <b>Higher Average Order Value (AOV):</b> Intelligent bundling increases multi-item package adoption across faucets, toilets, and showers.<br/>• <b>Zero Installation Rework:</b> Verified clearances eliminate expensive fixture return logistics.", style_card_body),
    ]
    roi2 = [
        Paragraph("<b>PRODUCTION READINESS & GO-TO-MARKET</b>", style_card_title),
        Spacer(1, 2),
        Paragraph("• <b>Zero-Setup Cold Start:</b> Self-bootstrapping vector store indexes catalog automatically on launch without manual DB provisioning.<br/>• <b>Full Test Automation:</b> Verified against 12 end-to-end scenarios covering spatial constraints, math accuracy, and boundary checks.<br/>• <b>Turnkey Deployment:</b> One-click launch via <code>run_demo.bat</code> or Docker Compose.", style_card_body),
    ]
    t_roi = Table([[roi1, roi2]], colWidths=[355, 355])
    t_roi.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("BOX", (0, 0), (0, 0), 1, COLOR_CARD_BORDER_BLUE),
        ("BOX", (1, 0), (1, 0), 1, COLOR_CARD_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_roi)

    # Build Document with SlideCanvas
    doc.build(story, canvasmaker=SlideCanvas)
    print(f"[SUCCESS] Presentation Deck PDF successfully generated: {output_filename}")


if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else "Presentation_Deck.pdf"
    create_presentation_deck_pdf(out_path)
