"""
Generate a publication-grade Prompts & System Instructions Documentation PDF
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

# Theme Colors
COLOR_BG_DARK = colors.HexColor("#090d16")
COLOR_CARD_DARK = colors.HexColor("#0d1322")
COLOR_CARD_BORDER = colors.HexColor("#1e293b")
COLOR_ACCENT_CYAN = colors.HexColor("#38bdf8")
COLOR_ACCENT_BLUE = colors.HexColor("#0284c7")
COLOR_TEXT_WHITE = colors.HexColor("#f8fafc")
COLOR_TEXT_MUTED = colors.HexColor("#94a3b8")
COLOR_TEXT_BODY = colors.HexColor("#334155")
COLOR_TEXT_HEADING = colors.HexColor("#0f172a")
COLOR_SUCCESS = colors.HexColor("#10b981")
COLOR_LIGHT_BG = colors.HexColor("#f8fafc")
COLOR_ROW_ALT = colors.HexColor("#f1f5f9")
COLOR_BORDER_LIGHT = colors.HexColor("#cbd5e1")
COLOR_CODE_BG = colors.HexColor("#0f172a")
COLOR_CODE_TEXT = colors.HexColor("#e2e8f0")


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
            self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "PROMPTS & SYSTEM INSTRUCTIONS DOCUMENTATION")
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


def create_prompts_documentation_pdf(output_filename="Prompts_Documentation.pdf"):
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
        fontSize=22,
        leading=26,
        textColor=COLOR_TEXT_WHITE,
    )
    style_cover_subtitle = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11.5,
        leading=15.5,
        textColor=COLOR_ACCENT_CYAN,
    )
    style_cover_meta = ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=COLOR_TEXT_MUTED,
    )

    style_h1 = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=COLOR_TEXT_HEADING,
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True,
    )
    style_h2 = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14.5,
        textColor=COLOR_ACCENT_BLUE,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True,
    )
    style_body = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=COLOR_TEXT_BODY,
        spaceAfter=5,
    )
    style_bullet = ParagraphStyle(
        "BulletCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=COLOR_TEXT_BODY,
        leftIndent=12,
        spaceAfter=3,
    )
    style_table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=COLOR_TEXT_BODY,
    )
    style_table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=COLOR_TEXT_WHITE,
    )
    style_code_box = ParagraphStyle(
        "CodeBox",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.5,
        leading=10.5,
        textColor=COLOR_CODE_TEXT,
    )

    story = []

    # =========================================================================
    # 1. COVER / BANNER
    # =========================================================================
    banner_data = [
        [
            Paragraph("<b>KOHLER AI SALES & SPATIAL DESIGN ADVISOR</b>", style_cover_title),
        ],
        [
            Paragraph("Comprehensive AI Prompts, System Instructions & Workflow Architecture Documentation", style_cover_subtitle),
        ],
        [
            Paragraph("<b>Scope:</b> Complete Prompt Engineering Catalog | <b>Persona:</b> Executive Showroom Advisor | <b>Standard:</b> Indian Luxury Plumbing", style_cover_meta),
        ],
    ]
    banner_table = Table(banner_data, colWidths=[504])
    banner_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD_DARK),
        ("PADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 5),
        ("TOPPADDING", (0, 2), (-1, 2), 0),
        ("BOTTOMPADDING", (0, 2), (-1, 2), 10),
        ("LINEBELOW", (0, 1), (-1, 1), 1, COLOR_ACCENT_BLUE),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 2. PROMPT ENGINEERING METHODOLOGY
    # =========================================================================
    story.append(Paragraph("1. Prompt Engineering Methodology & Governance Principles", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT_BLUE, spaceAfter=6, spaceBefore=2))

    method_text = (
        "The Kohler AI Sales Advisor utilizes a hybrid prompt engineering methodology engineered for high-precision luxury commerce. "
        "Unlike open-ended generative chatbots, every prompt across our orchestration pipeline enforces five strict governance principles:"
    )
    story.append(Paragraph(method_text, style_body))

    principles = [
        ("1. Decoupled Logic & Persona Enforcement", "The LLM never calculates room dimensions, building clearances, discounts, or GST taxes directly. All mathematical, spatial, and stock calculations are computed deterministically via Python tools and injected into the prompt context."),
        ("2. Executive Advisor Persona", "Replaced generic 'Concierge' and chatbot personas with a refined, authoritative, and architectural Sales Advisor tone. Absolute zero-emoji policy and complete avoidance of robotic underscores or em dashes in visible outputs."),
        ("3. Strict Currency & Market Normalization", "All prices, quotes, and calculations are strictly bound to Indian Rupees (INR) at fixed 83.50 exchange rate with luxury retail trailing 999 pricing."),
        ("4. Deterministic Tool Signatures", "Every tool prompt is equipped with typed JSON parameter schemas, boundary conditions, and explicit instructions on when to execute."),
        ("5. Dual-Runtime High Resiliency", "Prompts are optimized for both local 3B parameter models (Ollama qwen2.5:3b) and cloud LLMs (OpenRouter) with zero-lag fallback synthesis if cloud limits trigger.")
    ]
    for title, desc in principles:
        story.append(Paragraph(f"• <b>{title}:</b> {desc}", style_bullet))

    story.append(Spacer(1, 8))

    # =========================================================================
    # 3. MASTER AI ADVISOR SYSTEM PROMPT (agent.py)
    # =========================================================================
    story.append(Paragraph("2. Master AI Advisor System Prompt (`agent.py`)", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT_BLUE, spaceAfter=6, spaceBefore=2))

    story.append(Paragraph(
        "The following prompt is injected into the root LlamaIndex `AgentWorkflow` orchestrator. "
        "It establishes the advisor role, spatial consultation directives, pricing rules, and response structure:",
        style_body
    ))

    master_prompt_text = (
        "You are a consultative AI sales advisor, spatial designer, and specifications expert for Kohler luxury bathroom products.<br/>"
        "All catalog prices and quotes are in Indian Rupees (INR, 1 USD = 83.50 INR).<br/><br/>"
        "<b>Sales &amp; Spatial Consultation Mission:</b><br/>"
        "- Your objective is to guide customers toward exploring, designing, and purchasing Kohler bathroom suites.<br/>"
        "- When customers ask about room layouts, dimensions (ranging up to 10ft x 10ft = 100 sq ft), or product fit in a space:<br/>"
        "&nbsp;&nbsp;* Calculate square footage, verify ergonomic clearances (21\"-30\" in front of commodes/vanities), and establish the minimum and maximum pleasing fixture capacity.<br/>"
        "&nbsp;&nbsp;* Deliver design advice (e.g. wall-hung fixtures to expand floor space in compact rooms; focal freestanding tubs and wet/dry zoning in luxury master suites).<br/>"
        "&nbsp;&nbsp;* Recommend curated, matching Kohler product suites with exact dimensions and prices in INR.<br/>"
        "- When customers ask about specific Kohler products, their prices, or quotes:<br/>"
        "&nbsp;&nbsp;* Verify exact specifications, finishes, and catalog prices in INR.<br/>"
        "&nbsp;&nbsp;* When customers ask for multi-item quotes, custom bundles, discounts (e.g. 15% or 20%), or taxes/GST (e.g. 18%), provide exact itemized calculations.<br/>"
        "- When customers ask about stock or shipping lead times, provide transit estimates and stock availability.<br/><br/>"
        "<b>Output &amp; Formatting Guidelines:</b><br/>"
        "- For comprehensive room proposals and multi-product quotes, provide complete, cleanly formatted markdown with:<br/>"
        "&nbsp;&nbsp;1. Spatial &amp; Aesthetic Overview (Room dimensions, fixture capacity, clearance rules).<br/>"
        "&nbsp;&nbsp;2. Curated Fixture Package (Product names, finishes, dimensions, and item prices in INR).<br/>"
        "&nbsp;&nbsp;3. Mathematical Price Quote (Subtotal, Discount savings, GST/Taxes, and Grand Total).<br/>"
        "&nbsp;&nbsp;4. Delivery &amp; Logistics status.<br/>"
        "- Directness: Do NOT output scratchpad thinking. Deliver direct, professional, and clear sales responses without emojis."
    )

    t_master = Table([[Paragraph(master_prompt_text, style_code_box)]], colWidths=[504])
    t_master.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CODE_BG),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_CARD_BORDER),
    ]))
    story.append(t_master)

    story.append(PageBreak())

    # =========================================================================
    # 4. OLLAMA CUSTOM MODELFILE SYSTEM PROMPT
    # =========================================================================
    story.append(Paragraph("3. Local Ollama Modelfile System Prompt (`Modelfile`)", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT_BLUE, spaceAfter=6, spaceBefore=2))

    story.append(Paragraph(
        "For 100% offline edge deployments and showroom kiosks, the custom Ollama `Modelfile` bakes brand identity, "
        "building code clearances, and few-shot examples into the quantized weights of `qwen2.5:3b`:",
        style_body
    ))

    modelfile_prompt_text = (
        "<b>FROM</b> qwen2.5:3b<br/>"
        "<b>PARAMETER</b> temperature 0.2<br/>"
        "<b>PARAMETER</b> top_p 0.9<br/>"
        "<b>PARAMETER</b> num_ctx 4096<br/><br/>"
        "<b>SYSTEM</b> \"\"\"You are the Kohler AI Sales &amp; Spatial Design Advisor for Kohler India.<br/>"
        "You specialize in architectural bathroom space planning, luxury plumbing fixtures, and package pricing in Indian Rupees (INR).<br/><br/>"
        "CORE OPERATING DIRECTIVES:<br/>"
        "1. CURRENCY: Always state prices strictly in Indian Rupees (INR), formatted using standard notation (e.g., INR 1,89,999). Never use USD or other currencies.<br/>"
        "2. CLEARANCE &amp; BUILDING CODES: In every spatial layout, verify and enforce:<br/>"
        "&nbsp;&nbsp;&nbsp;- 15\" minimum toilet centerline clearance from side walls and vanities.<br/>"
        "&nbsp;&nbsp;&nbsp;- 21\" to 30\" minimum unobstructed front clearance for sinks, toilets, and tubs.<br/>"
        "&nbsp;&nbsp;&nbsp;- 30\" minimum entrance door arc swing clearance.<br/>"
        "&nbsp;&nbsp;&nbsp;- Wet / Dry moisture zoning to separate shower enclosures from dry vanity zones.<br/>"
        "3. SIGNATURE KOHLER SUITES: Champion signature Kohler collections including Numi 2.0 smart toilet, Purist brass fixtures, Moxie Bluetooth showerheads, Artifacts vintage fixtures, and Veil wall-hung suites.<br/>"
        "4. TONE &amp; MANNER: Refined, consultative, authoritative, architectural, and concise without emojis.\"\"\"<br/><br/>"
        "<b>MESSAGE</b> user \"What is the Numi 2.0 price and finish?\"<br/>"
        "<b>MESSAGE</b> assistant \"The Kohler Numi 2.0 Flagship Smart Toilet is priced at INR 6,00,999 in a Sculptural vitrified ceramic finish. It features interactive ambient lighting, Bluetooth surround sound, hands-free automated lid operation, and personalized cleansing presets with Kohler Konnect.\""
    )

    t_modelfile = Table([[Paragraph(modelfile_prompt_text, style_code_box)]], colWidths=[504])
    t_modelfile.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CODE_BG),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_CARD_BORDER),
    ]))
    story.append(t_modelfile)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 5. DETERMINISTIC 0ms ROUTER TEMPLATES (router.py)
    # =========================================================================
    story.append(Paragraph("4. Deterministic 0ms Router Templates & Direct Responses", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT_BLUE, spaceAfter=6, spaceBefore=2))

    story.append(Paragraph(
        "To achieve zero latency and zero token usage for frequent conversational patterns, `router.py` bypasses LLM inference "
        "and immediately outputs formatted advisor responses:",
        style_body
    ))

    router_data = [
        [
            Paragraph("Trigger Intent & Regex", style_table_header),
            Paragraph("Routing Action", style_table_header),
            Paragraph("Injected Advisor Markdown Output", style_table_header),
        ],
        [
            Paragraph("<b>Greeting Intent</b><br/><code>^(hi|hello|hey|greetings|namaste)</code>", style_table_cell),
            Paragraph("Bypass LLM<br/>(0ms, 0 Tokens)", style_table_cell),
            Paragraph("<b>Direct Welcome Card:</b> Welcomes customer to Kohler Spatial Studio, highlights Purist brassware, Veil & Numi smart toilets, and invites room dimensions or budget limits.", style_table_cell),
        ],
        [
            Paragraph("<b>Portfolio Intent</b><br/><code>catalog|show.*products|list.*prices</code>", style_table_cell),
            Paragraph("Bypass LLM<br/>(0ms, 0 Tokens)", style_table_cell),
            Paragraph("<b>Structured Portfolio Overview:</b> Renders an itemized Markdown table across Faucets, Commodes, Showers, Vanities, and Tubs with dimensions, finishes, and INR prices.", style_table_cell),
        ],
        [
            Paragraph("<b>Fast-Path Specs</b><br/><code>specs|dimensions|finishes of &lt;sku&gt;</code>", style_table_cell),
            Paragraph("Fast RAG<br/>(1-Step Retrieval)", style_table_cell),
            Paragraph("<b>Precision Product Spec Card:</b> Top-1 Cross-Encoder retrieved product specs formatted with MRP in INR, material, warranty, and lead time.", style_table_cell),
        ],
    ]
    t_router = Table(router_data, colWidths=[120, 94, 290])
    t_router.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_DARK),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT_BG, COLOR_ROW_ALT]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_router)

    story.append(PageBreak())

    # =========================================================================
    # 6. DETERMINISTIC SYNTHESIS & ZERO-LAG RESILIENCY TEMPLATE
    # =========================================================================
    story.append(Paragraph("5. Deterministic Synthesis & Zero-Lag Fallback Template (`agent.py`)", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT_BLUE, spaceAfter=6, spaceBefore=2))

    story.append(Paragraph(
        "When cloud LLMs experience rate limits (HTTP 429) or network timeouts beyond 3.0 seconds, "
        "the orchestrator executes the deterministic synthesis template. This guarantees zero UI hang and 100% factual fidelity:",
        style_body
    ))

    fallback_text = (
        "<b>Deterministic Synthesis Engine Architecture:</b><br/>"
        "<code>def synthesize_proposal(user_query, spatial_context, catalog_context, math_context, inventory_context):</code><br/><br/>"
        "<b>Synthesized Proposal Structure:</b><br/>"
        "### Kohler Spatial Design &amp; Sales Advisory Proposal<br/>"
        "Thank you for consulting the Kohler Sales &amp; Spatial Design Advisor. Based on your requirements (*\"{user_query}\"*), here is your customized proposal:<br/><br/>"
        "<b>[Section 1: Spatial &amp; Architectural Planning]</b> (Included when dimensions or room type detected)<br/>"
        "- Room Dimensions: {width} ft x {length} ft ({sqft} sq ft)<br/>"
        "- Sizing &amp; Capacity: {min_fixtures} to {max_fixtures} fixtures<br/>"
        "- Ergonomic Clearances: 15\" toilet centerline verified; 21\"-30\" front clearance maintained.<br/><br/>"
        "<b>[Section 2: Curated Kohler Package &amp; Specifications]</b> (Injected from 2-Stage Hybrid RAG)<br/>"
        "- {Product_Name} ({Category}) | Price: INR {Price} | Finish: {Finish} | Dimensions: {Dimensions}<br/><br/>"
        "<b>[Section 3: Financial &amp; Package Quotation (INR, 18% GST)]</b> (Injected from calculator.py)<br/>"
        "- Subtotal: INR {Subtotal} | Package Savings (15%): -INR {Savings} | 18% GST: +INR {GST} | Grand Total: INR {Grand_Total}<br/><br/>"
        "<b>[Section 4: Warehouse Logistics &amp; Fulfillment]</b> (Injected from inventory.py)<br/>"
        "- Status: In Stock (Central Distribution Center) | Shipping Transit: 3 to 5 business days."
    )

    t_fallback = Table([[Paragraph(fallback_text, style_code_box)]], colWidths=[504])
    t_fallback.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_CODE_BG),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_CARD_BORDER),
    ]))
    story.append(t_fallback)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 7. TOOL CALLING SCHEMAS & PROMPT INTERFACES
    # =========================================================================
    story.append(Paragraph("6. Tool Parameter Schemas & JSON Signatures", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT_BLUE, spaceAfter=6, spaceBefore=2))

    tools_schema_data = [
        [
            Paragraph("Tool Function", style_table_header),
            Paragraph("Parameter Signature & Constraints", style_table_header),
            Paragraph("Prompt Execution Rule", style_table_header),
        ],
        [
            Paragraph("<code>bundle_optimizer</code><br/>(tools/bundle_optimizer.py)", style_table_cell),
            Paragraph("<code>width_ft: float</code> (4-16)<br/><code>length_ft: float</code> (4-16)<br/><code>budget_inr: float</code> (30k-12L+)<br/><code>theme: str</code> (5 themes)", style_table_cell),
            Paragraph("Executed whenever customer requests a complete bathroom package, room remodel, or clicks 'Transfer to Advisor'.", style_table_cell),
        ],
        [
            Paragraph("<code>calculate_quote</code><br/>(tools/calculator.py)", style_table_cell),
            Paragraph("<code>items: list[dict]</code> (catalog MRPs)<br/><code>discount_pct: float</code> (default 15%)<br/><code>tax_pct: float</code> (default 18% GST)", style_table_cell),
            Paragraph("Mandatory for all pricing math, package calculations, and tax rollups. LLM is strictly prohibited from doing mental arithmetic.", style_table_cell),
        ],
        [
            Paragraph("<code>retrieve_catalog_docs</code><br/>(tools/catalog.py)", style_table_cell),
            Paragraph("<code>query_str: str</code> (product name/sku)<br/><code>top_k: int</code> (default 2 or 3)", style_table_cell),
            Paragraph("Executes ChromaDB vector search + Cross-Encoder reranker with LRU cache.", style_table_cell),
        ],
        [
            Paragraph("<code>inventory_checker</code><br/>(tools/inventory.py)", style_table_cell),
            Paragraph("<code>product_name: str</code><br/><code>zip_code: str</code> (postal PIN)", style_table_cell),
            Paragraph("Resolves regional fulfillment warehouse and estimated transit days.", style_table_cell),
        ],
    ]
    t_tools = Table(tools_schema_data, colWidths=[120, 164, 220])
    t_tools.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_CARD_DARK),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER_LIGHT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT_BG, COLOR_ROW_ALT]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_tools)

    # Build Document with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] Prompts Documentation PDF successfully generated: {output_filename}")


if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else "Prompts_Documentation.pdf"
    create_prompts_documentation_pdf(out_path)
