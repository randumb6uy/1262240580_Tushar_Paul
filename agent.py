import asyncio
import os
import sys
import re
import urllib.request
from dotenv import load_dotenv

# Silence warnings and force offline cache mode
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["OLLAMA_FLASH_ATTENTION"] = "1"

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

from llama_index.core import Settings
from tools import get_catalog_tool
from tools.room_planner import plan_room_layout
from tools.calculator import calculate_quote
from tools.inventory import check_product_stock_and_delivery
from tools.catalog import retrieve_catalog_docs
from tools.bundle_optimizer import (
    optimize_bundle,
    format_bundle_markdown,
    AESTHETIC_THEMES,
)
from router import (
    classify_query,
    extract_text_query,
    QueryRoute,
    ROOM_PATTERNS,
    MATH_PATTERNS,
    INVENTORY_PATTERNS,
    THEME_PATTERNS,
)


AGENT_SYSTEM_PROMPT = """You are a consultative AI sales advisor, spatial designer, and specifications expert for Kohler luxury bathroom products.
All catalog prices and quotes are in Indian Rupees (INR, 1 USD = 83.50 INR).

Sales & Spatial Consultation Mission:
- Your objective is to guide customers toward exploring, designing, and purchasing Kohler bathroom suites.
- When customers ask about room layouts, dimensions (ranging up to 10ft x 10ft = 100 sq ft), or product fit in a space:
  * Calculate square footage, verify ergonomic clearances (21"-30" in front of commodes/vanities), and establish the minimum and maximum pleasing fixture capacity.
  * Deliver design advice (e.g. wall-hung fixtures to expand floor space in compact rooms; focal freestanding tubs and wet/dry zoning in luxury master suites).
  * Recommend curated, matching Kohler product suites with exact dimensions and prices in INR.
- When customers ask about specific Kohler products, their prices, or quotes:
  * Verify exact specifications, finishes, and catalog prices in INR.
  * When customers ask for multi-item quotes, custom bundles, discounts (e.g. 15% or 20%), or taxes/GST (e.g. 18%), provide exact itemized calculations.
- When customers ask about stock or shipping lead times, provide transit estimates and stock availability.

Output & Formatting Guidelines:
- For comprehensive room proposals and multi-product quotes, provide complete, cleanly formatted markdown with:
  1. Spatial & Aesthetic Overview (Room dimensions, fixture capacity, clearance rules).
  2. Curated Fixture Package (Product names, finishes, dimensions, and item prices in INR).
  3. Mathematical Price Quote (Subtotal, Discount savings, GST/Taxes, and Grand Total).
  4. Delivery & Logistics status.
- Directness: Do NOT output scratchpad thinking. Deliver direct, professional, and clear sales responses without emojis.
"""

def is_ollama_running() -> bool:
    """Quick 0.5s health check to verify if Ollama daemon is active on 127.0.0.1 or localhost."""
    for host in ["127.0.0.1", "localhost"]:
        try:
            with urllib.request.urlopen(f"http://{host}:11434/api/tags", timeout=0.8) as response:
                if response.status == 200:
                    return True
        except Exception:
            continue
    return False


def get_llm(force_provider: str = None):
    """
    Configures the LLM:
    1. If LLM_PROVIDER=ollama and Ollama is active -> 100% local, offline, token-free.
    2. Otherwise -> OpenRouter.
    """
    provider = (force_provider or os.getenv("LLM_PROVIDER", "ollama")).lower()
    
    if provider == "ollama":
        if is_ollama_running():
            from llama_index.llms.ollama import Ollama
            model_name = os.getenv("AGENT_MODEL", "qwen2.5:3b")
            return Ollama(
                model=model_name,
                base_url="http://127.0.0.1:11434",
                request_timeout=90.0,
                context_window=8192,
                additional_kwargs={"num_ctx": 8192, "num_predict": 2048, "keep_alive": -1},
            )
        else:
            print("[LLM Warning] Ollama requested but not running at 127.0.0.1:11434.", flush=True)
            print("             Falling back to OpenRouter tier so the demo continues smoothly.", flush=True)
    
    # OpenRouter configuration
    from llama_index.llms.openrouter import OpenRouter
    model_name = os.getenv("OPENROUTER_MODEL") or "nex-agi/nex-n2.5-pro:free"
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key.strip() in ["your_openrouter_api_key_here", ""]:
        from llama_index.llms.ollama import Ollama
        return Ollama(
            model="qwen2.5:3b",
            base_url="http://127.0.0.1:11434",
            request_timeout=90.0,
            context_window=8192,
        )
    
    return OpenRouter(
        api_key=api_key,
        model=model_name,
        temperature=0.1,
        max_tokens=2048,
        context_window=32768,
    )


def create_agent(llm=None, chroma_path: str = "./chroma_db"):
    """Instantiates the autonomous Kohler Advisor."""
    if llm is None:
        llm = get_llm()
    Settings.llm = llm
    return llm


_SHARED_CATALOG_TOOL = None

def get_shared_catalog_tool(llm=None):
    global _SHARED_CATALOG_TOOL
    if _SHARED_CATALOG_TOOL is None:
        _SHARED_CATALOG_TOOL = get_catalog_tool(llm=llm, use_cache=True)
    return _SHARED_CATALOG_TOOL

def generate_catalog_overview() -> str:
    """Provides a comprehensive, structured overview of the complete Kohler luxury portfolio."""
    return (
        "### Kohler Luxury Collection Catalogue (India - INR)\n\n"
        "Curated portfolio of architectural fixtures, smart bathroom innovations, and wellness suites:\n\n"
        "#### 1. Designer Faucets & Basin Brassware\n"
        "- **Kohler Veer Single-Handle** (Matte Black, compact single-lever): **INR 14,999**\n"
        "- **Kohler Composed Single-Control** (Polished Chrome, minimalist high-arch): **INR 27,999**\n"
        "- **Kohler Stillness Wall-Mount** (Brushed Nickel, concealed valve): **INR 32,999**\n"
        "- **Kohler Purist Widespread** (Vibrant Brushed Moderne Brass, dual cross handles): **INR 34,999**\n"
        "- **Kohler Sensate Touchless** (Matte Black / Chrome, motion sensor): **INR 40,999**\n"
        "- **Kohler Artifacts Gentleman's** (Oil-Rubbed Bronze, vintage column spout): **INR 42,999**\n\n"
        "#### 2. Commodes & Intelligent Toilets\n"
        "- **Kohler Cimarron Two-Piece** (White vitreous china, Revolution 360 swirl): **INR 23,999**\n"
        "- **Kohler Santa Rosa One-Piece** (Compact elongated, Quiet-Close seat): **INR 32,999**\n"
        "- **Kohler San Souci Low-Profile** (Compact 25.5\" depth for powder rooms): **INR 44,999**\n"
        "- **Kohler Veil Wall-Hung** (Glazed ceramic, concealed in-wall carrier): **INR 64,999**\n"
        "- **Kohler Veil Intelligent Smart Toilet** (Tankless, integrated bidet, UV wand, auto flush): **INR 3,75,999**\n"
        "- **Kohler Numi 2.0 Flagship Smart Toilet** (Heated seat, ambient lighting, Bluetooth audio, foot flush): **INR 6,00,999**\n\n"
        "#### 3. Showers & Hydrotherapy Systems\n"
        "- **Kohler Moxie Bluetooth Showerhead** (Waterproof Harman Kardon audio speaker): **INR 15,999**\n"
        "- **Kohler HydroRail-R Retrofit Column** (Converts single outlet to dual rainhead/handshower): **INR 31,999**\n"
        "- **Kohler WaterTile Square Body Spray** (5\"x5\" flush-mount spa spray): **INR 11,999**\n"
        "- **Kohler Statement Oblong Shower Package** (12\"x8\" rain panel + baton handshower): **INR 67,999**\n"
        "- **Kohler Awaken Thermostatic System** (10\" rainhead + 3-function handshower): **INR 78,999**\n"
        "- **Kohler DTV Prompt Digital Shower** (4-button digital interface & thermostatic valve): **INR 1,12,999**\n\n"
        "#### 4. Statement Bathtubs & Sinks\n"
        "- **Kohler Caxton Oval Undermount Sink** (Classic vitreous china): **INR 9,999**\n"
        "- **Kohler Conical Bell Glass Vessel Sink** (Translucent amber artisan spun glass): **INR 27,999**\n"
        "- **Kohler Memoirs Stately Pedestal Sink** (Crown-molding fireclay ceramic): **INR 37,999**\n"
        "- **Kohler Archer Alcove Soaking Tub** (60\"x32\" comfort depth acrylic): **INR 59,999**\n"
        "- **Kohler Underscore Drop-In Tub** (66\"x36\" luxury deep soak): **INR 95,999**\n"
        "- **Kohler Ceric Freestanding Soaking Tub** (65.5\" Lithocast matte resin): **INR 3,16,999**\n\n"
        "#### 5. Vanities & Cabinetry\n"
        "- **Kohler Poplin 36\" Vanity** (White laminate with resin basin): **INR 42,999**\n"
        "- **Kohler Jacquard Petite 32\" Vanity** (Walnut wood fretwork doors): **INR 52,999**\n"
        "- **Kohler Tresham Shaker 24\" Vanity** (Mohair grey compact shaker): **INR 62,999**\n"
        "- **Kohler Marabou 30\" Floating Vanity** (Shadow oak wall-hung with LED channel): **INR 73,999**\n"
        "- **Kohler Jute 48\" Solid Teak Vanity** (Moisture-resistant oiled teak): **INR 1,20,999**\n"
        "- **Kohler Southerk 60\" Double Vanity** (Midnight blue lacquer, Carrera quartz dual basin): **INR 1,74,999**\n\n"
        "---\n"
        "**How would you like to proceed?**\n"
        "- Share your room dimensions (e.g. 4x5 powder room, 6x8 standard bath, or 10x10 master suite) for a custom plan.\n"
        "- Request an itemized package quote with discounts & 18% GST.\n"
        "- Check warehouse stock availability and delivery lead times to your pincode."
    )

async def run_llm_completion(prompt: str, timeout_seconds: float = 3.5) -> str:
    """
    Safely completes an LLM prompt with a strict timeout and zero hanging.
    Returns None if LLM is unavailable, times out, or is rate-limited.
    """
    # 1. Local Ollama if available
    if is_ollama_running():
        try:
            from llama_index.llms.ollama import Ollama
            model_name = os.getenv("AGENT_MODEL", "qwen2.5:3b")
            local_llm = Ollama(
                model=model_name,
                base_url="http://127.0.0.1:11434",
                request_timeout=timeout_seconds,
            )
            response = await asyncio.wait_for(local_llm.acomplete(prompt), timeout=timeout_seconds)
            res_str = str(response).strip()
            if res_str:
                return res_str
        except Exception:
            pass

    # 2. OpenRouter with strict timeout
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key and api_key.strip() not in ["your_openrouter_api_key_here", ""]:
        try:
            from llama_index.llms.openrouter import OpenRouter
            model_name = os.getenv("OPENROUTER_MODEL") or "nvidia/nemotron-3.5-lightning:free"
            remote_llm = OpenRouter(
                api_key=api_key,
                model=model_name,
                temperature=0.1,
                max_tokens=2048,
                request_timeout=timeout_seconds,
            )
            response = await asyncio.wait_for(remote_llm.acomplete(prompt), timeout=timeout_seconds)
            res_str = str(response).strip()
            if res_str and len(res_str) > 20:
                return res_str
        except Exception:
            pass

    return None

def extract_spatial_constraints(text: str) -> dict:
    """Extracts room dimensions, budget in INR, and aesthetic style from user queries."""
    clean = text.lower()
    
    # 1. Dimensions
    w, l = 6.0, 8.0
    dim_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:ft|feet|foot|'|m)?\s*(?:x|by|\*)\s*(\d+(?:\.\d+)?)", clean)
    if dim_match:
        try:
            w = float(dim_match.group(1))
            l = float(dim_match.group(2))
        except Exception:
            pass
    elif "powder" in clean or "half bath" in clean:
        w, l = 4.0, 5.0
    elif "master" in clean or "grand" in clean:
        w, l = 10.0, 10.0

    # 2. Budget
    budget = None
    lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac|lacs)", clean)
    if lakh_match:
        try:
            budget = float(lakh_match.group(1)) * 100000.0
        except Exception:
            pass
    
    if budget is None:
        k_match = re.search(r"(\d+(?:\.\d+)?)\s*k\b", clean)
        if k_match:
            try:
                budget = float(k_match.group(1)) * 1000.0
            except Exception:
                pass

    if budget is None:
        num_match = re.search(r"(?:budget|under|below|within|upto|up to|₹|inr|rs\.?)\s*:?\s*(\d+(?:,\d+)*(?:\.\d+)?)", clean)
        if num_match:
            try:
                val_str = num_match.group(1).replace(",", "")
                budget = float(val_str)
            except Exception:
                pass

    # 3. Aesthetic Theme
    theme = "Modern Minimalist"
    if "zen" in clean or "japanese" in clean or "organic" in clean:
        theme = "Japanese Zen"
    elif "classic" in clean or "heritage" in clean or "traditional" in clean:
        theme = "Classic Luxury"
    elif "mid-century" in clean or "brass" in clean:
        theme = "Mid-Century Luxury"
    elif "smart" in clean or "high-tech" in clean or "touchless" in clean or "digital" in clean:
        theme = "Smart High-Tech"
    elif "minimalist" in clean or "modern" in clean:
        theme = "Modern Minimalist"

    return {
        "width_ft": w,
        "length_ft": l,
        "budget_inr": budget,
        "aesthetic_theme": theme,
        "include_bathtub": "tub" in clean or "bathtub" in clean,
        "include_smart_toilet": "smart" in clean or "intelligent" in clean or "numi" in clean or "veil" in clean,
        "include_thermostatic_shower": "thermostatic" in clean or "rainhead" in clean or "spa shower" in clean,
    }

async def smart_process_query(agent=None, user_msg: str = "", ctx=None):
    """
    Unified Consultative Dispatcher (100% Deterministic & Zero ReAct Dependency):
    - Normalizes user query safely from any format.
    - Handles greetings and catalog overview instantly.
    - Deterministically runs constraint sizing, math discounts, inventory lead times, and catalog retrieval.
    - Synthesizes a consultative response with zero hanging.
    """
    clean_msg = extract_text_query(user_msg).strip()
    if not clean_msg:
        yield {"type": "final", "content": "Hello. How may I assist you with Kohler luxury bathroom fixtures or room layout designs today?"}
        return

    route = classify_query(clean_msg)
    clean_q = clean_msg.lower()

    if route == QueryRoute.GREETING:
        yield {"type": "route", "badge": "[Direct] Consultation & Greeting"}
        sales_prompt = (
            f"You are the senior Kohler Sales & Spatial Design Advisor. "
            f"The customer said: '{clean_msg}'. "
            f"Respond naturally with professional warmth. Introduce yourself as the Kohler Sales and Spatial Design Advisor. "
            f"Highlight key product collections: Veil / Numi 2.0 Smart Toilets, Awaken Thermostatic Showers, Purist Brassware, and Ceric Freestanding Tubs. "
            f"Invite the customer to share their bathroom dimensions (e.g. 4x5 ft powder room, 8x7 ft master bath), "
            f"budget limits in INR, or aesthetic theme preferences. "
            f"Keep it concise, professional, and without emojis or em dashes."
        )
        response_text = await run_llm_completion(sales_prompt, timeout_seconds=2.5)
        if not response_text:
            response_text = (
                "Welcome to the Kohler Sales & Spatial Design Advisor.\n\n"
                "I am here to assist you with architectural bathroom planning, luxury product selection, "
                "and optimized package proposals in Indian Rupees (INR).\n\n"
                "**Featured Collections:**\n"
                "- **Intelligent Toilets**: Veil and Numi 2.0 with heated seating, integrated cleansing, and touchless sensors.\n"
                "- **Thermostatic Hydrotherapy**: Awaken Systems, Statement Oblong Rain Panels, and Moxie Bluetooth showerheads.\n"
                "- **Architectural Brassware**: Purist, Composed, and Stillness collections in Vibrant Brushed Moderne Brass, Matte Black, and Polished Chrome.\n"
                "- **Artisan Sinks & Tubs**: Ceric Freestanding Lithocast Tub and Conical Bell Spun Glass vessels.\n\n"
                "**How to get started:**\n"
                "- Share your room dimensions (e.g., 4x5 ft powder room, 8x7 ft master bath, or 10x10 ft luxury suite).\n"
                "- Specify a budget limit in INR and your preferred aesthetic theme (Modern Minimalist, Classic Luxury, Japanese Zen, Mid-Century Luxury, Smart High-Tech).\n"
                "- Request an itemized package quotation with 15% discount and 18% GST."
            )
        yield {"type": "final", "content": response_text}

    elif route == QueryRoute.CATALOG_OVERVIEW:
        yield {"type": "route", "badge": "[Catalog] Full Portfolio Overview"}
        yield {"type": "final", "content": generate_catalog_overview()}

    else:
        # Spatial, Pricing, Inventory, Product Search, or General Consultation
        has_room = any(re.search(p, clean_q) for p in ROOM_PATTERNS)
        has_inv = any(re.search(p, clean_q) for p in INVENTORY_PATTERNS)
        has_math = any(re.search(p, clean_q) for p in MATH_PATTERNS)
        has_theme = any(re.search(p, clean_q) for p in THEME_PATTERNS)

        context_blocks = []

        # 1. Deterministic Constraint-Based Bundle Optimizer
        if has_room or (has_theme and (has_math or "suite" in clean_q or "plan" in clean_q or "space" in clean_q)):
            yield {"type": "tool_call", "name": "bundle_and_spatial_optimizer", "args": clean_msg}
            try:
                constraints = extract_spatial_constraints(clean_msg)
                bundle_result = optimize_bundle(
                    width_ft=constraints["width_ft"],
                    length_ft=constraints["length_ft"],
                    budget_inr=constraints["budget_inr"],
                    aesthetic_theme=constraints["aesthetic_theme"],
                    include_bathtub=constraints["include_bathtub"],
                    include_smart_toilet=constraints["include_smart_toilet"],
                    include_thermostatic_shower=constraints["include_thermostatic_shower"],
                )
                bundle_md = format_bundle_markdown(bundle_result)
                context_blocks.append(f"### Spatial Studio Recommendation & Clearances:\n{bundle_md}")
            except Exception as e:
                print(f"[Warning] Bundle optimizer exception: {e}", flush=True)

        # 2. Deterministic Financial Calculator
        if has_math:
            yield {"type": "tool_call", "name": "price_and_package_calculator", "args": clean_msg}
            try:
                math_data = calculate_quote(clean_msg)
                context_blocks.append(f"### Financial & Package Quotation (INR, 18% GST):\n{math_data}")
            except Exception as e:
                print(f"[Warning] Calculator exception: {e}", flush=True)

        # 3. Deterministic Inventory & Logistics
        if has_inv:
            yield {"type": "tool_call", "name": "inventory_and_delivery_checker", "args": clean_msg}
            try:
                inv_data = check_product_stock_and_delivery(clean_msg)
                context_blocks.append(f"### Warehouse Logistics & Fulfillment:\n{inv_data}")
            except Exception as e:
                print(f"[Warning] Inventory exception: {e}", flush=True)

        # 4. Instant Chroma Vector + Cross-Encoder Rerank Lookup
        yield {"type": "tool_call", "name": "kohler_catalog_search", "args": clean_msg}
        try:
            docs_text = retrieve_catalog_docs(clean_msg, top_k=3)
            if docs_text:
                context_blocks.append(f"### Kohler Catalog Fixtures & Verified Specifications:\n{docs_text}")
        except Exception as e:
            print(f"[Warning] Catalog search exception: {e}", flush=True)

        yield {"type": "activity", "msg": "Synthesizing product specifications and proposal..."}

        # Attempt LLM synthesis with a strict 3.0s timeout
        response_text = None
        if context_blocks:
            synthesis_prompt = (
                f"You are the senior Kohler Luxury Spatial Design and Sales Advisor.\n"
                f"Customer Query: \"{clean_msg}\"\n\n"
                f"Below is the verified deterministic design, pricing, and catalog data:\n"
                + "\n\n".join(context_blocks) + "\n\n"
                f"Guidelines:\n"
                f"- State all fixture prices and calculations strictly in INR.\n"
                f"- Deliver a structured, professional, and clearly formatted markdown response without emojis, em dashes, or scratchpad thinking.\n"
                f"- Highlight how the selected Kohler fixtures fit the space, theme, and budget."
            )
            response_text = await run_llm_completion(synthesis_prompt, timeout_seconds=3.0)

        # High-Speed Deterministic Synthesis Fallback
        if not response_text:
            if context_blocks:
                header = (
                    f"### Kohler Spatial Design & Sales Advisory Proposal\n\n"
                    f"Thank you for consulting the Kohler Sales & Spatial Design Advisor. "
                    f"Based on your requirements (*\"{clean_msg}\"*), here is your customized proposal:\n\n"
                )
                footer = (
                    "\n\n---\n"
                    "**Advisory & Fulfillment Notes:**\n"
                    "- All Kohler luxury fixtures include standard manufacturer warranty and certified installation support.\n"
                    "- Package quotes include 15% package discount and 18% GST in Indian Rupees (INR).\n"
                    "- To refine your room dimensions, budget limits, or finish selections, simply reply with your adjustments."
                )
                response_text = header + "\n\n".join(context_blocks) + footer
            else:
                response_text = (
                    "Thank you for consulting the Kohler Sales & Spatial Design Advisor.\n\n"
                    f"I have reviewed your query: *\"{clean_msg}\"*.\n\n"
                    "To generate a customized bathroom suite and quote, please provide:\n"
                    "1. Room dimensions (e.g., 4x5 ft powder room, 8x7 ft standard bath, 10x10 ft master suite)\n"
                    "2. Target budget in INR (e.g., INR 1,50,000 to INR 10,00,000+)\n"
                    "3. Aesthetic theme (Modern Minimalist, Classic Luxury, Japanese Zen, Mid-Century Luxury, Smart High-Tech)"
                )

        yield {"type": "final", "content": response_text}
