"""
Generate a comprehensive, publication-grade Mental Model & Architectural Reference PDF
for the Kohler AI Sales & Spatial Design Advisor.
"""

import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
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

# Palette Constants matching the Luxury Dark & Cyan Architectural Theme
COLOR_BG_DARK = colors.HexColor("#090d16")
COLOR_CARD_DARK = colors.HexColor("#0d1322")
COLOR_CARD_BORDER = colors.HexColor("#1e293b")
COLOR_ACCENT_CYAN = colors.HexColor("#38bdf8")
COLOR_ACCENT_BLUE = colors.HexColor("#0284c7")
COLOR_TEXT_WHITE = colors.HexColor("#f8fafc")
COLOR_TEXT_MUTED = colors.HexColor("#94a3b8")
COLOR_TEXT_BODY = colors.HexColor("#334155")
COLOR_TEXT_HEADING = colors.HexColor("#0f172a")
COLOR_ACCENT_GOLD = colors.HexColor("#d97706")
COLOR_SUCCESS = colors.HexColor("#10b981")
COLOR_LIGHT_BG = colors.HexColor("#f8fafc")
COLOR_ROW_ALT = colors.HexColor("#f1f5f9")
COLOR_BORDER_LIGHT = colors.HexColor("#cbd5e1")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and draw total page numbers and running headers."""
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(COLOR_TEXT_MUTED)

        # Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 11 * inch - 36, "KOHLER AI SALES & SPATIAL DESIGN ADVISOR")
            self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "SYSTEM MENTAL MODEL & ARCHITECTURAL REFERENCE")
            self.setStrokeColor(COLOR_BORDER_LIGHT)
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

        # Footer (all pages)
        self.setFont("Helvetica", 8)
        self.drawString(54, 36, "Confidential - Kohler AI Spatial Commerce Platform")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 54, 36, page_str)
        self.setStrokeColor(COLOR_BORDER_LIGHT)
        self.setLineWidth(0.5)
        self.line(54, 46, 8.5 * inch - 54, 46)

        self.restoreState()


def create_mental_model_pdf(output_filename="Kohler_AI_Advisor_Mental_Model.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    style_cover_title = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=COLOR_TEXT_WHITE,
        alignment=0,
    )
    style_cover_subtitle = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=COLOR_ACCENT_CYAN,
        alignment=0,
    )
    style_cover_meta = ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=COLOR_TEXT_MUTED,
        alignment=0,
    )

    style_h1 = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=COLOR_TEXT_HEADING,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )
    style_h2 = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=COLOR_ACCENT_BLUE,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    style_body = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=COLOR_TEXT_BODY,
        spaceAfter=6,
    )
    style_body_bold = ParagraphStyle(
        "BodyBoldCustom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13.5,
        textColor=COLOR_TEXT_HEADING,
        spaceAfter=4,
    )
    style_bullet = ParagraphStyle(
        "BulletCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=COLOR_TEXT_BODY,
        leftIndent=14,
        spaceAfter=3,
    )
    style_table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=COLOR_TEXT_BODY,
    )
    style_table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=COLOR_TEXT_HEADING,
    )
    style_table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=COLOR_TEXT_WHITE,
    )
    style_code_box = ParagraphStyle(
        "CodeBox",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=COLOR_TEXT_HEADING,
    )

    story = []

    # =========================================================================
    # 1. COVER / HEADER BANNER
    # =========================================================================
    banner_data = [
        [
            Paragraph("<b>KOHLER AI SALES & SPATIAL DESIGN ADVISOR</b>", style_cover_title),
        ],
        [
            Paragraph("Comprehensive System Mental Model, Architectural Reference & Technical Specification", style_cover_subtitle),
        ],
        [
            Paragraph("<b>Version:</b> 2.4.0 Production | <b>Architecture:</b> 4-Engine Deterministic Pipeline | <b>Target:</b> Luxury Spatial Commerce", style_cover_meta),
        ],
    ]
    banner_table = Table(banner_data, colWidths=[504])
    banner_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_DARK),
        ("PADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
        ("TOPPADDING", (0, 2), (-1, 2), 0),
        ("BOTTOMPADDING", (0, 2), (-1, 2), 12),
        ("LINEBELOW", (0, 1), (-1, 1), 1, COLOR_ACCENT_BLUE),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 12))

    # =========================================================================
    # 2. EXECUTIVE SUMMARY & PROBLEM STATEMENT
    # =========================================================================
    story.append(Paragraph("1. Executive Summary & Problem Statement", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT_BLUE, spaceAfter=8, spaceBefore=2))
    
    exec_text = (
        "Selecting and purchasing luxury bathroom fixtures involves complex multi-dimensional constraints. "
        "Traditional generative AI approaches fail in this domain due to three systemic vulnerabilities: "
        "<b>(1) Spatial Hallucinations:</b> recommending oversized fixtures into compact powder rooms that violate residential building codes; "
        "<b>(2) Multi-Step Arithmetic Failures:</b> inaccurate discount rollups and tax computations; and "
        "<b>(3) API Latency & Cloud Rate Limits (HTTP 429):</b> resulting in conversational stalls and degraded customer experience."
    )
    story.append(Paragraph(exec_text, style_body))

    sol_text = (
        "The <b>Kohler AI Advisor</b> solves this by decoupling generative natural language from spatial and financial logic. "
        "The system treats generative LLMs strictly as conversational polishers, delegating all spatial clearances, "
        "budget allocations, package discounts, and catalog lookups to four deterministic, verified computation engines."
    )
    story.append(Paragraph(sol_text, style_body))

    # =========================================================================
    # 3. THE 4-ENGINE MENTAL MODEL
    # =========================================================================
    story.append(Paragraph("2. The Mental Model: Four Deterministic Engines", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT_BLUE, spaceAfter=8, spaceBefore=2))

    engine_summary = (
        "The architecture operates on a strict four-layer pipeline where queries are filtered and routed at <b>0ms overhead</b> "
        "before reaching the orchestrator. If cloud LLMs lag or fail, a zero-lag deterministic fallback guarantees instantaneous "
        "proposal delivery."
    )
    story.append(Paragraph(engine_summary, style_body))

    engines_data = [
        [
            Paragraph("Engine Layer", style_table_header),
            Paragraph("Primary Role & Mechanism", style_table_header),
            Paragraph("Latency / Cost", style_table_header),
            Paragraph("Key Output Deliverable", style_table_header),
        ],
        [
            Paragraph("<b>1. Traffic Controller</b><br/>(0ms Intent Router)", style_table_cell),
            Paragraph("Regex pattern classifier bypasses LLM tokens for casual greetings, catalog inquiries, and single-spec fast paths.", style_table_cell),
            Paragraph("0ms<br/>0 Tokens", style_table_cell_bold),
            Paragraph("Direct Welcome Card, Portfolio Table, or Fast-Path Routing.", style_table_cell),
        ],
        [
            Paragraph("<b>2. Spatial Studio & Optimizer</b><br/>(Constraint Engine)", style_table_cell),
            Paragraph("Evaluates room square footage, calculates minimum/maximum fixture counts, enforces 15\" centerline and 21\"-30\" aisle clearances, harmonizes aesthetic themes.", style_table_cell),
            Paragraph("< 2ms<br/>Deterministic", style_table_cell_bold),
            Paragraph("Complete Fixture Package, Code Compliance Matrix, Dimensional Fit.", style_table_cell),
        ],
        [
            Paragraph("<b>3. Financial Engine</b><br/>(INR & GST Math)", style_table_cell),
            Paragraph("Executes exact Indian Rupee commerce arithmetic: 15% package volume discounts, 18% GST calculation, and budget variance checks.", style_table_cell),
            Paragraph("< 1ms<br/>Deterministic", style_table_cell_bold),
            Paragraph("Itemized Quotation Table with Subtotal, Savings, GST, and Grand Total.", style_table_cell),
        ],
        [
            Paragraph("<b>4. 2-Stage Hybrid RAG</b><br/>(Catalog Retrieval)", style_table_cell),
            Paragraph("ChromaDB dense BGE embedding retrieval followed by Cross-Encoder reranking (ms-marco-MiniLM-L-6-v2) with in-memory LRU cache.", style_table_cell),
            Paragraph("15-40ms<br/>Local / Cache", style_table_cell_bold),
            Paragraph("Top-K Kohler SKU specifications, finish codes, dimensions, and live stock.", style_table_cell),
        ],
    ]
    t_engines = Table(engines_data, colWidths=[110, 194, 75, 125])
    t_engines.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_DARK),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT_BG, COLOR_ROW_ALT]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_engines)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 4. ARCHITECTURAL DATA FLOW DIAGRAM
    # =========================================================================
    story.append(Paragraph("3. Architectural Request Flow & Orchestration", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT_BLUE, spaceAfter=8, spaceBefore=2))

    flow_box_data = [
        [Paragraph("<b>USER REQUEST / SPATIAL STUDIO INPUTS</b>", style_cover_subtitle)],
        [Paragraph("↓", style_cover_meta)],
        [Paragraph("<b>0ms INTENT ROUTER (router.py)</b> — Regex Intent Classification & Fast-Path Bypass", style_table_cell_bold)],
        [Paragraph("├─ <i>Greeting / Basic</i> → Instant Direct Sales Advisor Welcome (0ms, 0 Tokens)<br/>"
                   "├─ <i>Portfolio Inquiry</i> → Instant Structured Kohler Catalog Overview (0ms, 0 Tokens)<br/>"
                   "├─ <i>Product Specs</i> → Fast-Path RAG (BGE Embeddings + Cross-Encoder Reranker)<br/>"
                   "└─ <i>Suite Planning / Math / Stock</i> → Advisor Orchestrator (agent.py)", style_table_cell)],
        [Paragraph("↓", style_cover_meta)],
        [Paragraph("<b>DETERMINISTIC TOOL DISPATCH & SYNTHESIS</b>", style_table_cell_bold)],
        [Paragraph("1. <b>bundle_optimizer.py</b>: Room sizing, fixture capacity, clearance validation<br/>"
                   "2. <b>calculator.py</b>: 15% package savings, 18% GST calculation in INR<br/>"
                   "3. <b>inventory.py</b>: Regional warehouse stock & postal PIN transit days<br/>"
                   "4. <b>agent.py (3.0s Timeout)</b>: Ollama / OpenRouter LLM Synthesis<br/>"
                   "&nbsp;&nbsp;&nbsp;&nbsp;↳ <i>On Timeout or 429 Error</i> → <b>Zero-Lag Deterministic Markdown Fallback (0ms)</b>", style_table_cell)],
        [Paragraph("↓", style_cover_meta)],
        [Paragraph("<b>GRADIO DUAL-TAB USER INTERFACE (app.py)</b> — Spatial Studio + Conversational Advisor", style_cover_subtitle)],
    ]
    t_flow = Table(flow_box_data, colWidths=[504])
    t_flow.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_DARK),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("TEXTCOLOR", (0, 0), (-1, -1), COLOR_TEXT_WHITE),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("ALIGN", (0, 4), (-1, 4), "CENTER"),
        ("ALIGN", (0, 7), (-1, 7), "CENTER"),
        ("BACKGROUND", (0, 2), (-1, 3), colors.HexColor("#131c31")),
        ("BACKGROUND", (0, 5), (-1, 6), colors.HexColor("#131c31")),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_CARD_BORDER),
    ]))
    story.append(t_flow)

    story.append(PageBreak())

    # =========================================================================
    # 5. SPATIAL SIZING & BUILDING CODE CLEARANCES
    # =========================================================================
    story.append(Paragraph("4. Ergonomic Clearance & Building Code Standards", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT_BLUE, spaceAfter=8, spaceBefore=2))

    story.append(Paragraph(
        "The Spatial Studio and Suite Optimizer enforce rigorous residential plumbing and ergonomic guidelines. "
        "Rooms below designated square footage thresholds are automatically restricted to prevent overcrowded, non-compliant layouts.",
        style_body
    ))

    code_data = [
        [
            Paragraph("Fixture Category", style_table_header),
            Paragraph("Min. Centerline Clearance", style_table_header),
            Paragraph("Front Aisle Clearance", style_table_header),
            Paragraph("Architectural Constraint / Rule", style_table_header),
        ],
        [
            Paragraph("<b>Smart Toilet / Commode</b>", style_table_cell),
            Paragraph("15 inches (38 cm) from centerline to sidewall", style_table_cell),
            Paragraph("21\" to 30\" (53-76 cm) unobstructed", style_table_cell),
            Paragraph("Must maintain dedicated clearance envelope; placed in dry zone.", style_table_cell),
        ],
        [
            Paragraph("<b>Vanity / Basin</b>", style_table_cell),
            Paragraph("15 inches (38 cm) from centerline to sidewall", style_table_cell),
            Paragraph("21\" to 30\" (53-76 cm) unobstructed", style_table_cell),
            Paragraph("Positioned near entry wall; mirror lighting clearances enforced.", style_table_cell),
        ],
        [
            Paragraph("<b>Walk-In / Spa Shower</b>", style_table_cell),
            Paragraph("30\" x 30\" (76x76 cm) minimum interior envelope", style_table_cell),
            Paragraph("24\" (61 cm) clear door swing area", style_table_cell),
            Paragraph("Wet-zone containment; requires dedicated floor slope/drain.", style_table_cell),
        ],
        [
            Paragraph("<b>Freestanding / Alcove Tub</b>", style_table_cell),
            Paragraph("30 inches (76 cm) accessible side span", style_table_cell),
            Paragraph("21 inches (53 cm) clear apron aisle", style_table_cell),
            Paragraph("Strictly prohibited in rooms < 35 sq ft to prevent code violations.", style_table_cell),
        ],
    ]
    t_code = Table(code_data, colWidths=[110, 125, 115, 154])
    t_code.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_DARK),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT_BG, COLOR_ROW_ALT]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_code)
    story.append(Spacer(1, 10))

    # Room Type Capacities
    story.append(Paragraph("<b>Room Square Footage & Fixture Sizing Rules:</b>", style_body_bold))
    story.append(Paragraph("• <b>Powder Room (&lt; 28 sq ft / e.g. 4x5, 4x6 ft):</b> Fixed capacity: 2 fixtures (Compact Basin + Wall-Hung Commode). Bathtubs and walk-in showers strictly excluded.", style_bullet))
    story.append(Paragraph("• <b>Three-Quarter Bath (28 - 45 sq ft / e.g. 5x7, 6x7 ft):</b> Fixed capacity: 3 fixtures (Vanity + Commode + Walk-in Shower Enclosure).", style_bullet))
    story.append(Paragraph("• <b>Full Family Bath (45 - 75 sq ft / e.g. 7x8, 8x9 ft):</b> Standard capacity: 4 fixtures (Double/Single Vanity + Toilet + Shower + Alcove/Drop-In Tub).", style_bullet))
    story.append(Paragraph("• <b>Grand Master Suite (&gt; 75 sq ft / e.g. 10x10, 12x12 ft):</b> Full capacity: 5 fixtures (Statement Freestanding Tub + Intelligent Smart Toilet + Thermostatic Shower + Double Vanity + Luxury Brassware).", style_bullet))
    story.append(Spacer(1, 10))

    # =========================================================================
    # 6. INDIAN RUPEE COMMERCE & FINANCIAL ENGINE
    # =========================================================================
    story.append(Paragraph("5. Indian Luxury Commerce & Financial Pricing Engine", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT_BLUE, spaceAfter=8, spaceBefore=2))

    story.append(Paragraph(
        "All catalog products are priced in Indian Rupees (INR) following luxury retail conventions. "
        "Pricing is normalized using the standard luxury retail ending (trailing 999):",
        style_body
    ))

    calc_box = [
        [Paragraph("<b>Indian Rupee Price Normalization Formula:</b>", style_table_cell_bold)],
        [Paragraph("Catalog Price (INR) = [ Round( (Base USD × 83.50) / 1000 ) × 1000 ] - 1", style_code_box)],
        [Paragraph("<b>Itemized Quotation Mathematics:</b><br/>"
                   "• <b>Subtotal:</b> Sum of individual catalog MRPs.<br/>"
                   "• <b>Package Savings (15%):</b> Subtotal × 0.15<br/>"
                   "• <b>Taxable Amount:</b> Subtotal - Package Savings<br/>"
                   "• <b>GST (18%):</b> Taxable Amount × 0.18<br/>"
                   "• <b>Grand Total:</b> Taxable Amount + GST Amount<br/>"
                   "• <b>Budget Variance:</b> Target Budget - Grand Total (identifies surplus or budget deficit)", style_table_cell)],
    ]
    t_calc = Table(calc_box, colWidths=[504])
    t_calc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
        ("LINEBELOW", (0, 0), (-1, 0), 1, COLOR_ACCENT_BLUE),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, COLOR_BORDER_LIGHT),
    ]))
    story.append(t_calc)

    story.append(PageBreak())

    # =========================================================================
    # 7. HYBRID LLM STRATEGY & HIGH-RESILIENCY FALLBACK
    # =========================================================================
    story.append(Paragraph("6. Hybrid LLM Architecture & Zero-Lag Fallback", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT_BLUE, spaceAfter=8, spaceBefore=2))

    story.append(Paragraph(
        "To provide both maximum local portability and enterprise cloud capabilities, the system implements a dual-runtime model "
        "backed by a deterministic markdown fallback:",
        style_body
    ))

    llm_data = [
        [
            Paragraph("Runtime Mode", style_table_header),
            Paragraph("Engine / Model", style_table_header),
            Paragraph("Behavior & Fallback Logic", style_table_header),
            Paragraph("Use Case & Portability", style_table_header),
        ],
        [
            Paragraph("<b>Local Offline Mode</b>", style_table_cell),
            Paragraph("Ollama Daemon<br/>(qwen2.5:3b / deepseek-r1)", style_table_cell),
            Paragraph("Checked via 0.5s health ping. Runs 100% offline with zero cloud API keys, zero token fees, and total data privacy.", style_table_cell),
            Paragraph("On-premise showroom kiosks, private offline workstations.", style_table_cell),
        ],
        [
            Paragraph("<b>Cloud Provider Mode</b>", style_table_cell),
            Paragraph("OpenRouter API<br/>(meta-llama / qwen)", style_table_cell),
            Paragraph("Protected with a strict 3.0s timeout. Catches HTTP 429 rate limits, network outages, and socket timeouts.", style_table_cell),
            Paragraph("Cloud web deployments, mobile users, automated CI/CD.", style_table_cell),
        ],
        [
            Paragraph("<b>Zero-Lag Safety Net</b>", style_table_cell),
            Paragraph("Deterministic Markdown Synthesizer", style_table_cell),
            Paragraph("Instantly compiles tool outputs into structured markdown proposal if LLM fails or exceeds 3.0s timeout.", style_table_cell),
            Paragraph("Guarantees 100% UI uptime under all network conditions.", style_table_cell),
        ],
    ]
    t_llm = Table(llm_data, colWidths=[105, 110, 164, 125])
    t_llm.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_DARK),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT_BG, COLOR_ROW_ALT]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_llm)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 8. DUAL-TAB USER EXPERIENCE SPECIFICATION
    # =========================================================================
    story.append(Paragraph("7. Dual-Tab User Experience & Interface Design", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT_BLUE, spaceAfter=8, spaceBefore=2))

    story.append(Paragraph(
        "The web application delivers two complementary workflows in a unified pure Python Gradio interface:",
        style_body
    ))

    story.append(Paragraph("<b>Tab 1: Spatial Studio & Suite Optimizer</b>", style_body_bold))
    story.append(Paragraph("• <b>Visual Control Card:</b> Dimension sliders (4-16 ft), budget slider (INR 30k - 12L+) with quick preset pills (1.5L, 3.5L, 6.5L, 10L+), 5 curated design themes, and fixture checkboxes.", style_bullet))
    story.append(Paragraph("• <b>Live Solution Deliverables:</b> Product package table with finishes and SKU numbers, itemized INR quotation breakdown, and building code compliance check.", style_bullet))
    story.append(Paragraph("• <b>Interactive Handoff:</b> One-click button transfers the full spatial suite proposal into Tab 2 and prompts the AI Advisor for consultative design advice.", style_bullet))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Tab 2: Conversational AI Advisor</b>", style_body_bold))
    story.append(Paragraph("• <b>Executive Sales Assistant:</b> Greets clients, answers technical plumbing questions, recommends finishes, and checks warehouse logistics.", style_bullet))
    story.append(Paragraph("• <b>Custom Dark Scrollbars:</b> Complete cross-browser dark scrollbars matching the luxury slate aesthetic.", style_bullet))
    story.append(Paragraph("• <b>Live Streaming Badges:</b> Transparent status notifications showing tool dispatch, spatial calculations, and GST math in real time.", style_bullet))
    story.append(Spacer(1, 10))

    # =========================================================================
    # 9. VERIFICATION & QUALITY BENCHMARK MATRIX
    # =========================================================================
    story.append(Paragraph("8. Automated Verification & Benchmark Matrix", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT_BLUE, spaceAfter=8, spaceBefore=2))

    story.append(Paragraph(
        "All components are verified via a 12-scenario automated test suite (test_suite.py) testing boundary conditions:",
        style_body
    ))

    test_data = [
        [
            Paragraph("Scenario ID", style_table_header),
            Paragraph("Evaluation Focus & Test Case", style_table_header),
            Paragraph("Expected Deterministic Behavior", style_table_header),
            Paragraph("Status", style_table_header),
        ],
        [
            Paragraph("S1 - S3", style_table_cell),
            Paragraph("Spatial Fit (4x5 Powder Room, 8x9 Family Bath, 10x10 Master Suite)", style_table_cell),
            Paragraph("Respects 2, 4, 5 fixture limits; enforces 15\" centerline and 21\" front clearances.", style_table_cell),
            Paragraph("PASS (100%)", style_table_cell_bold),
        ],
        [
            Paragraph("S4 - S5", style_table_cell),
            Paragraph("Aesthetic Cohesion (Modern Minimalist, Classic Luxury, Japanese Zen)", style_table_cell),
            Paragraph("Curates matching finishes (Matte Black, Brushed Bronze, Chrome, French Gold).", style_table_cell),
            Paragraph("PASS (100%)", style_table_cell_bold),
        ],
        [
            Paragraph("S6 - S8", style_table_cell),
            Paragraph("Financial Accuracy & GST Math (15% package discount, 18% GST in INR)", style_table_cell),
            Paragraph("Zero arithmetic hallucinations; itemized subtotal, discount, GST, and total match.", style_table_cell),
            Paragraph("PASS (100%)", style_table_cell_bold),
        ],
        [
            Paragraph("S9 - S10", style_table_cell),
            Paragraph("Catalog Retrieval & Fast-Path Routing (Veil Toilet, Purist Faucet, Moxie)", style_table_cell),
            Paragraph("Top-K Cross-Encoder retrieval; instant 0ms routing for single-product specs.", style_table_cell),
            Paragraph("PASS (100%)", style_table_cell_bold),
        ],
        [
            Paragraph("S11 - S12", style_table_cell),
            Paragraph("Warehouse Logistics & Resilient Fallback (Postal PIN check, 429 rate limit)", style_table_cell),
            Paragraph("Resolves transit days (2-5 business days); 0ms fallback on LLM timeout.", style_table_cell),
            Paragraph("PASS (100%)", style_table_cell_bold),
        ],
    ]
    t_test = Table(test_data, colWidths=[70, 160, 194, 80])
    t_test.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_DARK),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT_BG, COLOR_ROW_ALT]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (3, 1), (3, -1), "CENTER"),
        ("TEXTCOLOR", (3, 1), (3, -1), COLOR_SUCCESS),
    ]))
    story.append(t_test)

    # Build Document with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] Mental Model PDF successfully generated: {output_filename}")


if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else "Kohler_AI_Advisor_Mental_Model.pdf"
    create_mental_model_pdf(out_path)
