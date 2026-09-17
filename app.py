import argparse
import asyncio
import os
import sys
import re

# Silence warnings and force offline cache mode
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["OLLAMA_FLASH_ATTENTION"] = "1"

# Ensure UTF-8 output on Windows terminals
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import chromadb
from dotenv import load_dotenv
import gradio as gr
from llama_index.core.workflow import Context

from agent import create_agent, smart_process_query
from ingest import ingest_documents
from tools.space_optimizer import get_default_visual_layout

load_dotenv()

# 1. Self-bootstrapping: Lazy ingestion check
def ensure_indexed():
    chroma_path = "./chroma_db"
    collection_name = "kohler_agent"
    
    should_ingest = False
    if not os.path.exists(chroma_path):
        should_ingest = True
    else:
        try:
            client = chromadb.PersistentClient(path=chroma_path)
            colls = [c.name for c in client.list_collections()]
            if collection_name not in colls or client.get_collection(collection_name).count() == 0:
                should_ingest = True
        except Exception:
            should_ingest = True

    if should_ingest:
        print("[Bootstrap] No existing vector store found. Auto-indexing docs/products.jsonl with local BGE embeddings...")
        ingest_documents(jsonl_path="docs/products.jsonl", chroma_path=chroma_path, collection_name=collection_name)
    else:
        print("[OK] Existing ChromaDB vector store detected.")

ensure_indexed()

# 2. Instantiate Agent
print("Initializing Autonomous Kohler Agent with Fast-Path Router...")
agent = create_agent()

# 3. High-Contrast Blue & Black Luxury Styling
CUSTOM_CSS = """
/* Base Container & Dark Theme */
body, .gradio-container {
    background-color: #060913 !important;
    color: #F8FAFC !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
    max-width: 1480px !important;
    margin: 0 auto !important;
}

/* Header Container */
.studio-header {
    background: linear-gradient(180deg, #0d1527 0%, #060913 100%);
    border: 1px solid #1e3a8a;
    border-radius: 12px;
    padding: 18px 24px;
    margin-bottom: 16px;
    box-shadow: 0 4px 25px rgba(0, 0, 0, 0.7), 0 0 15px rgba(37, 99, 235, 0.15);
}

/* Chatbot Area */
#kohler-chatbot {
    background-color: #0a0f1d !important;
    border: 1px solid #1e293b !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5) !important;
}

/* Message Bubbles */
#kohler-chatbot [data-testid="user"], #kohler-chatbot .message.user {
    background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%) !important;
    color: #FFFFFF !important;
    border: 1px solid #2563eb !important;
    border-radius: 12px 12px 2px 12px !important;
    box-shadow: 0 2px 12px rgba(37, 99, 235, 0.25) !important;
}

#kohler-chatbot [data-testid="bot"], #kohler-chatbot .message.bot {
    background-color: #0f172a !important;
    color: #F1F5F9 !important;
    border: 1px solid #1e3a8a !important;
    border-radius: 12px 12px 12px 2px !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3) !important;
}

/* Chatbot markdown elements */
#kohler-chatbot h1, #kohler-chatbot h2, #kohler-chatbot h3, #kohler-chatbot h4 {
    color: #38bdf8 !important;
    margin-top: 6px !important;
    margin-bottom: 6px !important;
}

#kohler-chatbot strong {
    color: #60a5fa !important;
}

#kohler-chatbot table {
    border-collapse: collapse !important;
    width: 100% !important;
    margin: 8px 0 !important;
    font-size: 12px !important;
}

#kohler-chatbot th {
    background: #1e293b !important;
    color: #38bdf8 !important;
    padding: 6px 10px !important;
    border: 1px solid #334155 !important;
}

#kohler-chatbot td {
    padding: 6px 10px !important;
    border: 1px solid #1e293b !important;
}

/* Textbox */
#msg-input textarea, #msg-input input {
    background-color: #0f172a !important;
    border: 1px solid #1e293b !important;
    color: #F8FAFC !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    padding: 10px !important;
}

#msg-input textarea:focus, #msg-input input:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 12px rgba(56, 189, 248, 0.35) !important;
    outline: none !important;
}

/* Send Button */
#send-btn {
    background: linear-gradient(135deg, #1d4ed8 0%, #0284c7 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border: 1px solid #38bdf8 !important;
    border-radius: 8px !important;
    box-shadow: 0 0 14px rgba(56, 189, 248, 0.35) !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}

#send-btn:hover {
    box-shadow: 0 0 20px rgba(56, 189, 248, 0.6) !important;
    transform: translateY(-1px);
}

/* Clear Button */
#clear-btn {
    background-color: #0f172a !important;
    border: 1px solid #334155 !important;
    color: #94a3b8 !important;
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
}

#clear-btn:hover {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border-color: #64748b !important;
}

/* Quick Action Chips */
.quick-chip {
    background-color: #0f172a !important;
    border: 1px solid #1e3a8a !important;
    color: #93c5fd !important;
    border-radius: 20px !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    padding: 4px 12px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}

.quick-chip:hover {
    background-color: #1e293b !important;
    border-color: #38bdf8 !important;
    color: #38bdf8 !important;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.35) !important;
}

/* Visualizer Container */
#kohler-visualizer {
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Scrollbars */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #060913;
}
::-webkit-scrollbar-thumb {
    background: #1e3a8a;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #38bdf8;
}

footer { display: none !important; }
"""

# 4. Stream Processors & Helpers
def extract_text(item) -> str:
    """Extracts raw text string from strings, lists, dicts, or tuples."""
    if isinstance(item, dict):
        content = item.get("content", "")
    elif isinstance(item, (list, tuple)) and len(item) > 0:
        content = item[0]
    else:
        content = item

    if isinstance(content, str):
        return content
    if isinstance(content, (list, tuple)):
        parts = []
        for x in content:
            if isinstance(x, dict):
                parts.append(str(x.get("text", x)))
            else:
                parts.append(str(x))
        return " ".join(parts).strip()
    return str(content).strip()

async def user_submit(message: str, history: list):
    """Appends user message and initial bot placeholder, clears textbox."""
    clean_msg = extract_text(message)
    if not clean_msg:
        return "", history
    history = history or []
    history.append({"role": "user", "content": clean_msg})
    history.append({"role": "assistant", "content": "⚡ *Consulting Kohler design tools & specifications...*"})
    return "", history

async def bot_stream(history: list, current_visual_html: str, session_ctx: dict):
    """Processes query with autonomous agent, updating text and right-hand visual studio."""
    if not history or len(history) < 2:
        yield history, current_visual_html, session_ctx
        return

    user_message = extract_text(history[-2])

    if not session_ctx or "ctx" not in session_ctx:
        session_ctx["ctx"] = Context(agent)
    ctx = session_ctx["ctx"]

    new_visual_html = current_visual_html

    async for update in smart_process_query(agent, user_message, ctx=ctx):
        utype = update.get("type")
        if utype == "tool_call":
            tname = update.get("name", "tool")
            history[-1]["content"] = f"🔄 *Running Kohler tool: {tname}...*"
            yield history, new_visual_html, session_ctx
        elif utype == "final":
            final_text = update.get("content", "")
            history[-1]["content"] = final_text
            if update.get("visual_html"):
                new_visual_html = update.get("visual_html")
            yield history, new_visual_html, session_ctx

async def run_preset_query(preset_text: str, history: list, current_visual_html: str, session_ctx: dict):
    """Directly executes a preset query from one of the quick chips."""
    history = history or []
    history.append({"role": "user", "content": preset_text})
    history.append({"role": "assistant", "content": "⚡ *Consulting Kohler design tools & specifications...*"})
    yield history, current_visual_html, session_ctx

    if not session_ctx or "ctx" not in session_ctx:
        session_ctx["ctx"] = Context(agent)
    ctx = session_ctx["ctx"]

    new_visual_html = current_visual_html

    async for update in smart_process_query(agent, preset_text, ctx=ctx):
        utype = update.get("type")
        if utype == "tool_call":
            tname = update.get("name", "tool")
            history[-1]["content"] = f"🔄 *Running Kohler tool: {tname}...*"
            yield history, new_visual_html, session_ctx
        elif utype == "final":
            final_text = update.get("content", "")
            history[-1]["content"] = final_text
            if update.get("visual_html"):
                new_visual_html = update.get("visual_html")
            yield history, new_visual_html, session_ctx

async def click_ex1(h, v, s):
    async for item in run_preset_query("Design an 8x6 ft modern bathroom under ₹2,50,000 with matte black fixtures", h, v, s):
        yield item

async def click_ex2(h, v, s):
    async for item in run_preset_query("Recommend a matching Purist faucet and vanity package in Vibrant Moderne Brass with package discount", h, v, s):
        yield item

async def click_ex3(h, v, s):
    async for item in run_preset_query("Tell me about the Numi 2.0 smart toilet features, price in INR, and stock availability", h, v, s):
        yield item

async def click_ex4(h, v, s):
    async for item in run_preset_query("Design a 10x7 ft luxury zen spa master bathroom under ₹4,00,000 with soaking tub and shower", h, v, s):
        yield item

def clear_chat_handler():
    """Resets chatbot, session context, and default studio layout."""
    return [], get_default_visual_layout(), {}

# 5. Build Gradio UI
with gr.Blocks(title="Kohler Design & Spatial Studio") as demo:
    session_state = gr.State(value={})

    # Header Bar
    gr.HTML(
        """
        <div class="studio-header">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
              <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:26px;">🛁</span>
                <span style="color:#F8FAFC; font-size:22px; font-weight:800; letter-spacing:0.5px;">KOHLER DESIGN CONCIERGE & SPATIAL STUDIO</span>
              </div>
              <div style="color:#94A3B8; font-size:13px; margin-top:4px;">
                Autonomous AI Sales Advisor • Dual-View 2D CAD Blueprint & 3D Interactive WebGL Space Planning Engine
              </div>
            </div>
            
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
              <span style="background:#0F172A; border:1px solid #1E3A8A; color:#38BDF8; font-size:11px; font-weight:600; padding:5px 10px; border-radius:20px;">
                ⚡ Local RTX 4060 (qwen2.5:3b)
              </span>
              <span style="background:#0F172A; border:1px solid #1E3A8A; color:#34D399; font-size:11px; font-weight:600; padding:5px 10px; border-radius:20px;">
                🔒 100% Offline ($0 Cost)
              </span>
              <span style="background:#0F172A; border:1px solid #1E3A8A; color:#F59E0B; font-size:11px; font-weight:600; padding:5px 10px; border-radius:20px;">
                🇮🇳 India Catalog (₹ INR)
              </span>
              <span style="background:#0F172A; border:1px solid #2563EB; color:#60A5FA; font-size:11px; font-weight:600; padding:5px 10px; border-radius:20px;">
                📐 2D CAD & 3D WebGL
              </span>
            </div>
          </div>
        </div>
        """
    )

    # Main Split Screen Layout
    with gr.Row():
        # Left Panel: AI Sales Concierge Chat
        with gr.Column(scale=5, min_width=420):
            chatbot = gr.Chatbot(
                height=520,
                render_markdown=True,
                show_label=False,
                elem_id="kohler-chatbot"
            )

            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="Ask about Kohler products, combo quotes, or 2D/3D bathroom plans...",
                    show_label=False,
                    scale=8,
                    lines=1,
                    max_lines=3,
                    elem_id="msg-input"
                )
                send_btn = gr.Button("Send ↵", variant="primary", scale=2, elem_id="send-btn")

            with gr.Row():
                clear_btn = gr.Button("🗑️ Clear Chat", size="sm", elem_id="clear-btn")
                btn_ex1 = gr.Button("📐 8x6 Modern Bath Plan", size="sm", elem_classes=["quick-chip"])
                btn_ex2 = gr.Button("🛁 Purist Brass Suite", size="sm", elem_classes=["quick-chip"])
                btn_ex3 = gr.Button("🚽 Numi 2.0 Luxury Specs", size="sm", elem_classes=["quick-chip"])
                btn_ex4 = gr.Button("🌿 Zen Spa Master Bath", size="sm", elem_classes=["quick-chip"])

        # Right Panel: Dedicated Spatial Studio (2D CAD Blueprint + 3D WebGL Room)
        with gr.Column(scale=6, min_width=500):
            visualizer = gr.HTML(
                value=get_default_visual_layout(),
                elem_id="kohler-visualizer"
            )

    # Event Chaining for Message Submission
    submit_chain = (
        msg_input.submit(
            user_submit,
            inputs=[msg_input, chatbot],
            outputs=[msg_input, chatbot]
        )
        .then(
            bot_stream,
            inputs=[chatbot, visualizer, session_state],
            outputs=[chatbot, visualizer, session_state]
        )
    )

    send_chain = (
        send_btn.click(
            user_submit,
            inputs=[msg_input, chatbot],
            outputs=[msg_input, chatbot]
        )
        .then(
            bot_stream,
            inputs=[chatbot, visualizer, session_state],
            outputs=[chatbot, visualizer, session_state]
        )
    )

    # Quick Action Chips Direct Event Handlers
    btn_ex1.click(click_ex1, inputs=[chatbot, visualizer, session_state], outputs=[chatbot, visualizer, session_state])
    btn_ex2.click(click_ex2, inputs=[chatbot, visualizer, session_state], outputs=[chatbot, visualizer, session_state])
    btn_ex3.click(click_ex3, inputs=[chatbot, visualizer, session_state], outputs=[chatbot, visualizer, session_state])
    btn_ex4.click(click_ex4, inputs=[chatbot, visualizer, session_state], outputs=[chatbot, visualizer, session_state])

    # Clear Button Handler
    clear_btn.click(
        clear_chat_handler,
        inputs=None,
        outputs=[chatbot, visualizer, session_state]
    )

    # Clear Button Handler
    clear_btn.click(
        clear_chat_handler,
        inputs=None,
        outputs=[chatbot, visualizer, session_state]
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--share", action="store_true", help="Generate a public 72-hour temporary URL")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the prototype server on")
    args = parser.parse_args()

    # Allow sharing via command line flag or .env SHARE_PROTOTYPE=true
    share_flag = args.share or os.getenv("SHARE_PROTOTYPE", "false").lower() in ["true", "1", "yes"]
    
    print(f"Launching Kohler Spatial Studio prototype (Share={share_flag}) on port {args.port}...")
    demo.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=share_flag,
        theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate"),
        css=CUSTOM_CSS,
    )
