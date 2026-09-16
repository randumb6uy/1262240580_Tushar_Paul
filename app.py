import argparse
import asyncio
import os
import sys

# Silence warnings and force offline cache mode
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

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

# 3. Gradio Chat Handler (Output Only)
async def chat_handler(message: str, history: list, session_ctx: dict):
    if not session_ctx or "ctx" not in session_ctx:
        session_ctx["ctx"] = Context(agent)
    
    ctx = session_ctx["ctx"]
    final_text = ""

    async for update in smart_process_query(agent, message, ctx=ctx):
        if update.get("type") == "final":
            final_text = update.get("content", "")

    yield final_text

# 4. Clean & Compact Customer UI
CUSTOM_CSS = """
.gradio-container { max-width: 900px !important; margin: 0 auto !important; }
footer { display: none !important; }
"""

with gr.Blocks(title="Kohler Concierge") as demo:
    gr.Markdown(
        """
        ### 🛁 Kohler Design & Purchasing Concierge
        *Your personal assistant for Kohler luxury bathroom products, specifications, custom bundle quotes, and availability in India (₹ INR).*
        """
    )
    
    session_state = gr.State(value={})

    chat_interface = gr.ChatInterface(
        fn=chat_handler,
        additional_inputs=[session_state],
        chatbot=gr.Chatbot(height=480, render_markdown=True),
        textbox=gr.Textbox(placeholder="Ask about Kohler products, finishes, dimensions, bundle quotes, or stock...", container=False, scale=7),
        examples=[
            ["What finishes and dimensions are available for the Purist faucet?"],
            ["Tell me about the Numi 2.0 smart toilet and its luxury features."],
            ["What would the Moxie Bluetooth showerhead cost with a 15% discount and 18% GST?"],
            ["Do you have the Veil intelligent toilet in stock for delivery?"],
            ["Can you recommend a matching faucet and vanity package for a modern bathroom?"],
        ],
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--share", action="store_true", help="Generate a public 72-hour temporary URL")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the prototype server on")
    args = parser.parse_args()

    # Allow sharing via command line flag or .env SHARE_PROTOTYPE=true
    share_flag = args.share or os.getenv("SHARE_PROTOTYPE", "false").lower() in ["true", "1", "yes"]
    
    print(f"Launching Gradio prototype (Share={share_flag}) on port {args.port}...")
    demo.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=share_flag,
        theme=gr.themes.Soft(spacing_size="sm", text_size="sm"),
        css=CUSTOM_CSS,
    )
