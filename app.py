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

# 4. Gradio Blocks Interface
with gr.Blocks(title="Kohler Autonomous AI Agent") as demo:
    gr.Markdown(
        """
        # 🛁 Kohler Autonomous Shopping & Specs Agent (INR Edition)
        **High-Speed RAG + Smart Fast-Path Router + Autonomous Multi-Tool Calling**  
        *All prices natively quoted in Indian Rupees (₹ INR at 1 USD = ₹83.50). Equipped with In-Memory LRU Cache, Local BGE Embeddings, Cross-Encoder Reranker, Price Calculator, and Stock Checker.*
        """
    )
    
    session_state = gr.State(value={})

    chat_interface = gr.ChatInterface(
        fn=chat_handler,
        additional_inputs=[session_state],
        examples=[
            ["What is the price in INR and finishes for the Purist faucet?"],
            ["What is the price of the Purist faucet, and what would it cost with a 15% discount and 18% GST?"],
            ["Do you have the Veil smart toilet in stock, and how long will shipping take to ZIP 90210?"],
            ["Can you give me an itemized quote in INR for the Moxie showerhead and Poplin vanity?"],
            ["Hello! What kind of products do you specialize in?"],
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
        theme=gr.themes.Soft(),
    )
