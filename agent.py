import os
import sys

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

import urllib.request
from dotenv import load_dotenv
load_dotenv()

from llama_index.core import Settings
from llama_index.core.agent import AgentWorkflow
from llama_index.core.workflow import Context
from tools import get_agent_tools, get_catalog_tool
from router import classify_query, QueryRoute

AGENT_SYSTEM_PROMPT = """You are an elite consultative AI sales advisor and specifications expert for Kohler luxury bathroom products.
All catalog prices and quotes are in Indian Rupees (₹ INR, 1 USD = ₹83.50).

Sales & Customer Consultation Mission:
- Your objective is to inspire customers and actively guide them toward exploring and purchasing the right Kohler products.
- When customers engage in general conversation, greet them warmly, introduce yourself as their dedicated Kohler sales consultant, showcase signature products (e.g., Numi 2.0 / Veil intelligent smart toilets, Moxie Bluetooth showerheads, Purist designer faucets), and ask what project or room they are planning (master bath, powder room, full remodel).
- Actively recommend matching sets and complete bathroom bundles (e.g., matching faucets with vanities or spa shower packages).
- Encourage customers to ask for itemized package pricing, seasonal discounts, and live delivery lead times to their location.
- Always quote prices in Indian Rupees (₹ INR). Maintain an upscale, welcoming, and persuasive tone.

You have access to the following tools:
1. kohler_catalog_search: Search product specifications, dimensions, finishes, and catalog prices (in ₹ INR). Input should be a simple search query string (e.g. "Moxie showerhead" or "Purist faucet").
2. price_and_package_calculator: Calculate bundle totals, volume discounts, and taxes in ₹ INR. Input should be item_prices (list of numbers like [15999.0]), optional discount_percent, and optional tax_percent.
3. inventory_and_delivery_checker: Check live warehouse stock status and shipping transit times. Provide product_model_or_name and optional zip_code.
4. aesthetic_combo_recommender: Recommends aesthetically matched fixtures (coordinating metal finishes, complementary styles, and harmonious collections) and calculates promotional package combo discounts (10% to 22% off) in ₹ INR. Input should be query_product_or_style (e.g. "Purist faucet" or "zen spa") and optional target_category (e.g. "vanity" or "shower").
5. space_and_budget_optimizer: Fits bathroom combinations to exact room dimensions (length & width in feet) and budget ceilings in ₹ INR. Enforces building clearances, applies bundle discounts, and generates a Dual-View 2D architectural blueprint and interactive 3D WebGL room model. Input: room_length_ft, room_width_ft, max_budget_inr, optional style_preference, and optional must_have_categories.

Operational Guidelines:
- When the user asks about Kohler products, use 'kohler_catalog_search' to verify the exact details before answering. Always state prices clearly in Indian Rupees (₹ INR).
- When the user asks for quotes, packages, multiple items, or discounts, retrieve the prices first, then call 'price_and_package_calculator' for exact math.
- When the user asks what goes with a product, wants a matching aesthetic/finish, asks for bathroom combination packages, or wants style coordination, call 'aesthetic_combo_recommender' to present the matched suite and combo savings.
- When the user mentions room dimensions (e.g. '8x6', '10 by 7 ft', 'powder room space') or specifies a budget ceiling for a room layout, call 'space_and_budget_optimizer' to calculate the layout and Dual-View 2D/3D visualizer.
- When presenting 'space_and_budget_optimizer' results:
  1. DO NOT output any raw HTML, <iframe>, <svg>, or code tags in your chat text. The architectural blueprint and 3D WebGL model are automatically rendered in the dedicated Spatial Studio on the right.
  2. Deliver an elite consultative sales quote: warmly congratulate the customer, present the curated fixtures with prices in ₹ INR, explain the promotional combo savings, confirm code clearances (15" centerline, 21" front clearance, 30" door swing), and invite them to explore the 2D CAD Blueprint and 3D WebGL model in the Spatial Studio panel on the right.
- When the user asks about delivery or stock, use 'inventory_and_delivery_checker'.
- SPEED INSTRUCTION: Do NOT output your internal thinking scratchpad (no 'Here is my thought process'). Be direct, concise, and professional.
"""

def is_ollama_running(url: str = "http://localhost:11434/api/tags") -> bool:
    """Quick 0.5s health check to verify if Ollama daemon is active."""
    try:
        with urllib.request.urlopen(url, timeout=0.5) as response:
            return response.status == 200
    except Exception:
        return False

def get_llm():
    """
    Configures the LLM for token-free / demo-ready operation:
    1. If LLM_PROVIDER=ollama and Ollama is active -> 100% local, offline, token-free.
    2. Otherwise -> OpenRouter free-tier ('nvidia/nemotron-3.5-lightning:free').
    """
    provider = os.getenv("LLM_PROVIDER", "openrouter").lower()
    
    if provider == "ollama":
        if is_ollama_running():
            from llama_index.llms.ollama import Ollama
            model_name = os.getenv("AGENT_MODEL", "qwen2.5:3b")
            print(f"[LLM] Running 100% token-free local Ollama model: '{model_name}' (RTX 4060 GPU, Flash Attention, Keep-Alive)")
            return Ollama(
                model=model_name,
                base_url="http://localhost:11434",
                request_timeout=60.0,
                context_window=4096,
                additional_kwargs={"num_ctx": 4096, "keep_alive": -1},
            )
        else:
            print("[LLM Warning] Ollama requested but not running at localhost:11434.")
            print("             Falling back to OpenRouter free tier so the demo continues smoothly.")
            print("             (To use Ollama: start the Ollama app or run 'ollama serve')")
    
    # OpenRouter free tier fallback
    from llama_index.llms.openrouter import OpenRouter
    openrouter_model = os.getenv("OPENROUTER_MODEL", "")
    if not openrouter_model or "/" not in openrouter_model:
        openrouter_model = "nvidia/nemotron-3.5-lightning:free"
    model_name = openrouter_model
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set in .env and Ollama is not active.")
    
    return OpenRouter(
        api_key=api_key,
        model=model_name,
        max_tokens=1024,
    )

def create_agent(chroma_path: str = "./chroma_db") -> AgentWorkflow:
    """Instantiates the autonomous AgentWorkflow with all tools loaded."""
    llm = get_llm()
    Settings.llm = llm
    
    tools = get_agent_tools(chroma_path=chroma_path, llm=llm)
    
    agent = AgentWorkflow.from_tools_or_functions(
        tools_or_functions=tools,
        llm=llm,
        system_prompt=AGENT_SYSTEM_PROMPT,
    )
    return agent

_SHARED_CATALOG_TOOL = None

def get_shared_catalog_tool(llm=None):
    global _SHARED_CATALOG_TOOL
    if _SHARED_CATALOG_TOOL is None:
        _SHARED_CATALOG_TOOL = get_catalog_tool(llm=llm, use_cache=True)
    return _SHARED_CATALOG_TOOL

import re

def clean_ai_chat_text(text: str) -> str:
    """Strips any stray HTML tags, iframes, svgs, base64 strings, or internal thinking from AI response."""
    if not text:
        return ""
    # Strip iframes, svgs, scripts, styles
    text = re.sub(r'<iframe[\s\S]*?</iframe>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<svg[\s\S]*?</svg>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<script[\s\S]*?</script>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<style[\s\S]*?</style>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<div[\s\S]*?>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</div>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'data:text/html;base64,[A-Za-z0-9+/=]+', '', text)
    # Strip raw thinking patterns if any
    text = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.IGNORECASE)
    # Clean whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

async def smart_process_query(agent: AgentWorkflow, user_msg: str, ctx: Context = None):
    """
    Smart Query Dispatcher (Option 3 & 4):
    - Direct: Instant conversational reply for greetings.
    - Fast-Path RAG: Direct Chroma + Cross-Encoder retrieval in 1 LLM stream (~1-2s).
    - Multi-Step Agent: Full tool-calling ReAct workflow for math & inventory.
    """
    route = classify_query(user_msg)
    llm = Settings.llm

    if route == QueryRoute.GREETING:
        yield {"type": "route", "badge": "[Direct] Conversation"}
        # Proactive consultative sales prompt to lead the customer to buy Kohler products, matching slang and tone
        sales_prompt = (
            f"You are the Kohler Design & Purchasing Specialist (never say 'Qwen' or '[Your Name]'). "
            f"The customer said: '{user_msg}'. "
            f"Respond naturally, matching their conversational vibe. If they use casual slang like 'yo', 'ye', 'wassup', or 'sup', "
            f"greet them back with high energy, cool enthusiasm, and friendly warmth (e.g. 'Yo! Great to connect with you', 'Hey, what's up!'), "
            f"then smoothly pivot to show them what Kohler has to offer. "
            f"Introduce yourself as their Kohler Design & Purchasing Specialist, and spotlight our most exciting products "
            f"(such as the Moxie Bluetooth showerhead with built-in Harman Kardon audio, the futuristic Numi 2.0 / Veil smart toilets, or sleek Purist faucets). "
            f"Ask what space or project they are looking to upgrade (master bathroom, guest bath, or new house), "
            f"and mention that you can hook them up with itemized package quotes, custom bundles, and seasonal discounts in Indian Rupees (₹ INR). "
            f"Keep it concise (1-2 short paragraphs), upbeat, and focused on getting them excited to buy Kohler fixtures."
        )
        response = await llm.acomplete(sales_prompt)
        clean_text = clean_ai_chat_text(str(response))
        yield {"type": "final", "content": clean_text, "visual_html": None}

    elif route == QueryRoute.FAST_PATH_RAG:
        yield {"type": "route", "badge": "[Fast-Path] 1-Step Retrieval & Reranking"}
        
        # Pull the pre-warmed shared catalog tool directly (0ms initialization)
        catalog_tool = get_shared_catalog_tool(llm=llm)
        query_engine = catalog_tool.query_engine
        
        yield {"type": "activity", "msg": "Searching Kohler catalog with local BGE embeddings & Cross-Encoder reranker..."}
        
        response = await query_engine.aquery(user_msg)
        clean_text = clean_ai_chat_text(str(response))
        yield {"type": "final", "content": clean_text, "visual_html": None}

    else:
        # Complex multi-step Agentic Path
        yield {"type": "route", "badge": "[Agent] Multi-Step Autonomous Tools & Reasoning"}
        
        handler = agent.run(user_msg=user_msg, ctx=ctx)
        async for event in handler.stream_events():
            if hasattr(event, "tool_name"):
                kwargs = getattr(event, "tool_kwargs", "")
                yield {"type": "tool_call", "name": event.tool_name, "args": kwargs}
            elif hasattr(event, "tool_output"):
                out = str(getattr(event, "tool_output", ""))[:180].replace("\n", " ")
                yield {"type": "tool_result", "output": out}

        final_response = await handler
        final_text = str(final_response)

        visual_html = None
        try:
            from tools.space_optimizer import get_latest_visual_layout, clear_latest_visual_layout
            visual_html = get_latest_visual_layout()
            clear_latest_visual_layout()
        except Exception:
            pass

        clean_text = clean_ai_chat_text(final_text)

        # If visual layout was produced and LLM didn't mention checking the studio, append a polite callout
        if visual_html and "spatial studio" not in clean_text.lower() and "right panel" not in clean_text.lower():
            clean_text += "\n\n📐 *I have rendered your custom 2D CAD Blueprint and interactive 3D WebGL Room Model in the Spatial Studio on the right panel. Feel free to rotate, zoom, and inspect clearances!*"

        yield {"type": "final", "content": clean_text, "visual_html": visual_html}

if __name__ == "__main__":
    import asyncio
    
    async def main():
        agent = create_agent()
        test_query = "What is the price of the Purist faucet?"
        print(f"Query: {test_query}\n")
        async for step in smart_process_query(agent, test_query):
            print(step)

    asyncio.run(main())
