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

from agent import create_agent, smart_process_query
from ingest import ingest_documents
from router import extract_text_query
from tools.bundle_optimizer import (
    optimize_bundle,
    format_bundle_markdown,
    AESTHETIC_THEMES,
)

load_dotenv()

# 1. Self-bootstrapping: Ingestion check
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
        print("[Bootstrap] Auto-indexing docs/products.jsonl with local BGE embeddings...", flush=True)
        ingest_documents(jsonl_path="docs/products.jsonl", chroma_path=chroma_path, collection_name=collection_name)
    else:
        print("[OK] Existing ChromaDB vector store detected.", flush=True)

ensure_indexed()

# 2. Instantiate Agent
print("Initializing Kohler AI Sales & Spatial Design Advisor...", flush=True)
agent = create_agent()

# 3. Professional Architectural Dark Mode Theme (Custom Dark Scrollbars, High Contrast)
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Global Canvas */
body, html, .gradio-container {
    background-color: #090d16 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #f8fafc !important;
    max-width: 1140px !important;
    margin: 0 auto !important;
}

/* Eliminate Footers */
footer { display: none !important; }

/* ── Custom Theme Scrollbars (Global & Chatbot) ── */
::-webkit-scrollbar {
    width: 7px !important;
    height: 7px !important;
}
::-webkit-scrollbar-track {
    background: #090d16 !important;
    border-radius: 6px !important;
}
::-webkit-scrollbar-thumb {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 6px !important;
}
::-webkit-scrollbar-thumb:hover {
    background: #38bdf8 !important;
    border-color: #38bdf8 !important;
}
::-webkit-scrollbar-corner {
    background: #090d16 !important;
}

/* Firefox standard scrollbars */
* {
    scrollbar-width: thin !important;
    scrollbar-color: #334155 #090d16 !important;
}

/* Tabs Bar */
.tabs {
    border-bottom: 1px solid #1e293b !important;
    margin-bottom: 14px !important;
}
.tab-nav button {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: #94a3b8 !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 20px !important;
    transition: all 0.15s ease !important;
}
.tab-nav button.selected {
    color: #38bdf8 !important;
    border-bottom: 2px solid #38bdf8 !important;
    background: #0f172a !important;
}

/* Executive Header */
.header-card {
    background: #0f172a !important;
    border: 1px solid #1e293b !important;
    border-radius: 12px;
    padding: 16px 24px;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 14px rgba(0,0,0,0.35);
}

.brand-title {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 1.35rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.12em !important;
    color: #f8fafc !important;
    margin: 0;
}

.brand-subtitle {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    color: #38bdf8 !important;
    font-weight: 500 !important;
    margin-top: 2px;
}

.reset-btn {
    background: #1e293b !important;
    color: #cbd5e1 !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    padding: 6px 14px !important;
    transition: all 0.2s ease !important;
}
.reset-btn:hover {
    background: #334155 !important;
    color: #ffffff !important;
    border-color: #38bdf8 !important;
}

/* Cards */
.control-card {
    background: #0d1322 !important;
    border: 1px solid #1e293b !important;
    border-radius: 16px !important;
    padding: 22px !important;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

.deliverables-card {
    background: #0d1322 !important;
    border: 1px solid #1e293b !important;
    border-radius: 16px !important;
    padding: 22px !important;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

/* Typography & Labels */
h1, h2, h3, h4, h5, p, span, label, .label, .block-label {
    color: #f8fafc !important;
}

.control-card h3, .deliverables-card h3 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #f8fafc !important;
    margin-bottom: 16px !important;
    letter-spacing: -0.01em !important;
}

.info, .form .info, .gr-slider .info, div[data-testid="slider"] .info {
    color: #64748b !important;
    font-size: 0.78rem !important;
}

/* ── 1. Luxury Sliders ── */
.gr-slider, div[data-testid="slider"] {
    background: transparent !important;
    border: none !important;
    padding: 4px 0 10px 0 !important;
}

.gr-slider label, div[data-testid="slider"] label {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    color: #e2e8f0 !important;
}

.gr-slider input[type="number"], div[data-testid="slider"] input[type="number"] {
    background: #1e293b !important;
    color: #38bdf8 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    padding: 4px 8px !important;
    text-align: center !important;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    transition: all 0.2s ease !important;
}

.gr-slider input[type="number"]:focus, div[data-testid="slider"] input[type="number"]:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25) !important;
}

input[type="range"] {
    -webkit-appearance: none !important;
    appearance: none !important;
    width: 100% !important;
    height: 6px !important;
    background: #1e293b !important;
    border-radius: 9999px !important;
    outline: none !important;
    border: 1px solid #334155 !important;
    margin: 8px 0 !important;
    cursor: pointer !important;
}

input[type="range"]::-webkit-slider-runnable-track {
    height: 6px !important;
    background: linear-gradient(90deg, #0284c7 0%, #38bdf8 100%) !important;
    border-radius: 9999px !important;
}

input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none !important;
    appearance: none !important;
    width: 18px !important;
    height: 18px !important;
    border-radius: 50% !important;
    background: #ffffff !important;
    border: 3px solid #0284c7 !important;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.6) !important;
    cursor: pointer !important;
    margin-top: -6px !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}

input[type="range"]::-webkit-slider-thumb:hover {
    transform: scale(1.2) !important;
    box-shadow: 0 0 14px rgba(56, 189, 248, 0.9) !important;
}

input[type="range"]::-moz-range-track {
    height: 6px !important;
    background: linear-gradient(90deg, #0284c7 0%, #38bdf8 100%) !important;
    border-radius: 9999px !important;
    border: none !important;
}

input[type="range"]::-moz-range-thumb {
    width: 18px !important;
    height: 18px !important;
    border-radius: 50% !important;
    background: #ffffff !important;
    border: 3px solid #0284c7 !important;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.6) !important;
    cursor: pointer !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}

/* ── 2. Preset Budget Pill Buttons ── */
.preset-btn {
    background: #131d31 !important;
    color: #94a3b8 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    padding: 7px 12px !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
    text-align: center !important;
}

.preset-btn:hover {
    background: #1e293b !important;
    border-color: #38bdf8 !important;
    color: #38bdf8 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(56, 189, 248, 0.25) !important;
}

/* ── 3. Luxury Dropdown Selector ── */
.gr-dropdown, div[data-testid="dropdown"] {
    background: transparent !important;
    margin: 6px 0 12px 0 !important;
}

.gr-dropdown select, .gr-dropdown input, div[data-testid="dropdown"] select, div[data-testid="dropdown"] input {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    padding: 10px 14px !important;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.25) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

.gr-dropdown select:focus, div[data-testid="dropdown"] select:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25) !important;
}

/* ── 4. Checkbox Cards Group ── */
.gr-checkbox-group, div[data-testid="checkbox-group"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    margin: 8px 0 14px 0 !important;
}

.gr-checkbox, div[data-testid="checkbox-group"] label {
    background: #131d31 !important;
    border: 1px solid #1e293b !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
}

.gr-checkbox:hover, div[data-testid="checkbox-group"] label:hover {
    background: #1e293b !important;
    border-color: #38bdf8 !important;
}

.gr-checkbox input[type="checkbox"], div[data-testid="checkbox-group"] input[type="checkbox"] {
    appearance: none !important;
    -webkit-appearance: none !important;
    width: 18px !important;
    height: 18px !important;
    background: #090d16 !important;
    border: 1.5px solid #475569 !important;
    border-radius: 5px !important;
    cursor: pointer !important;
    position: relative !important;
    transition: all 0.15s ease !important;
    margin: 0 !important;
}

.gr-checkbox input[type="checkbox"]:checked, div[data-testid="checkbox-group"] input[type="checkbox"]:checked {
    background: #38bdf8 !important;
    border-color: #38bdf8 !important;
    box-shadow: 0 0 8px rgba(56, 189, 248, 0.5) !important;
}

.gr-checkbox input[type="checkbox"]:checked::after, div[data-testid="checkbox-group"] input[type="checkbox"]:checked::after {
    content: '' !important;
    position: absolute !important;
    left: 5px !important;
    top: 2px !important;
    width: 5px !important;
    height: 9px !important;
    border: solid #090d16 !important;
    border-width: 0 2.5px 2.5px 0 !important;
    transform: rotate(45deg) !important;
}

.gr-checkbox span, div[data-testid="checkbox-group"] label span {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: #e2e8f0 !important;
}

/* ── 5. Image & Floorplan Upload Box ── */
.gr-image, div[data-testid="image"], .upload-container {
    background: #111827 !important;
    border: 1.5px dashed #334155 !important;
    border-radius: 12px !important;
    padding: 12px !important;
    transition: all 0.2s ease !important;
    box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.3) !important;
}

.gr-image:hover, div[data-testid="image"]:hover, .upload-container:hover {
    border-color: #38bdf8 !important;
    background: #141f36 !important;
    box-shadow: 0 0 12px rgba(56, 189, 248, 0.15) !important;
}

/* ── 6. Action & Recommendation Buttons ── */
.plan-btn {
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
    color: #ffffff !important;
    border: 1px solid #38bdf8 !important;
    border-radius: 12px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.98rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em !important;
    padding: 13px 24px !important;
    box-shadow: 0 4px 18px rgba(2, 132, 199, 0.4) !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    margin-top: 10px !important;
    width: 100% !important;
}

.plan-btn:hover {
    background: linear-gradient(135deg, #0369a1 0%, #075985 100%) !important;
    border-color: #7dd3fc !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px rgba(56, 189, 248, 0.5) !important;
}

.secondary-action-btn {
    background: #131d31 !important;
    color: #38bdf8 !important;
    border: 1.5px solid #38bdf8 !important;
    border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    padding: 11px 20px !important;
    margin-top: 14px !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 2px 10px rgba(56, 189, 248, 0.2) !important;
    width: 100% !important;
    text-align: center !important;
}

.secondary-action-btn:hover {
    background: #38bdf8 !important;
    color: #090d16 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(56, 189, 248, 0.45) !important;
}

/* ── Modern Architectural Chatbot Viewport ── */
#kohler-chatbot, .gr-chatbot, [data-testid="chatbot"] {
    background: #0b1120 !important;
    border: 1px solid #1e293b !important;
    border-radius: 16px !important;
    padding: 16px !important;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
    scrollbar-width: thin !important;
    scrollbar-color: #334155 #0b1120 !important;
}

#kohler-chatbot::-webkit-scrollbar-track,
.gr-chatbot::-webkit-scrollbar-track,
[data-testid="chatbot"]::-webkit-scrollbar-track,
#kohler-chatbot *::-webkit-scrollbar-track {
    background: #0b1120 !important;
}

#kohler-chatbot::-webkit-scrollbar-thumb,
.gr-chatbot::-webkit-scrollbar-thumb,
[data-testid="chatbot"]::-webkit-scrollbar-thumb,
#kohler-chatbot *::-webkit-scrollbar-thumb {
    background: #334155 !important;
    border: 1px solid #1e293b !important;
    border-radius: 6px !important;
}

#kohler-chatbot::-webkit-scrollbar-thumb:hover,
.gr-chatbot::-webkit-scrollbar-thumb:hover,
[data-testid="chatbot"]::-webkit-scrollbar-thumb:hover,
#kohler-chatbot *::-webkit-scrollbar-thumb:hover {
    background: #38bdf8 !important;
    box-shadow: 0 0 8px rgba(56, 189, 248, 0.4) !important;
}

/* Chat Message Rows & Spacing */
.message-row, .message-wrap, .wrap {
    gap: 16px !important;
    padding: 6px 0 !important;
}

/* User Chat Bubble */
.message.user, .message-user, [data-testid="user"], div[class*="user"] > div.message, div[class*="user"] > div.bubble {
    background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(96, 165, 250, 0.3) !important;
    border-radius: 16px 16px 4px 16px !important;
    font-size: 0.94rem !important;
    line-height: 1.6 !important;
    padding: 12px 18px !important;
    box-shadow: 0 4px 14px rgba(29, 78, 216, 0.3) !important;
}

/* Advisor Bot Bubble */
.message.bot, .message-bot, [data-testid="bot"], div[class*="bot"] > div.message, div[class*="bot"] > div.bubble {
    background: #0f172a !important;
    color: #f1f5f9 !important;
    border: 1px solid #1e293b !important;
    border-left: 3px solid #38bdf8 !important;
    border-radius: 16px 16px 16px 4px !important;
    font-size: 0.94rem !important;
    line-height: 1.65 !important;
    padding: 16px 20px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;
}

/* Advisor Typography inside Chat */
.message.bot h1, .message.bot h2, .message.bot h3, .message.bot h4,
.message-bot h1, .message-bot h2, .message-bot h3, .message-bot h4 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    color: #38bdf8 !important;
    margin-top: 14px !important;
    margin-bottom: 8px !important;
    letter-spacing: -0.01em !important;
}

.message.bot p, .message-bot p {
    margin-bottom: 10px !important;
    color: #e2e8f0 !important;
}

.message.bot strong, .message-bot strong {
    color: #ffffff !important;
    font-weight: 600 !important;
}

.message.bot ul, .message.bot ol, .message-bot ul, .message-bot ol {
    margin: 8px 0 12px 20px !important;
    color: #cbd5e1 !important;
}

.message.bot li, .message-bot li {
    margin-bottom: 4px !important;
}

.message.bot pre, .message.bot code,
.message-bot pre, .message-bot code {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    background-color: #020617 !important;
    color: #38bdf8 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
}

.message.bot pre, .message-bot pre {
    padding: 14px !important;
    overflow-x: auto !important;
}

/* Tables in Chat & Deliverables Card */
.message.bot table, .message-bot table, .deliverables-card table {
    border-collapse: separate !important;
    border-spacing: 0 !important;
    width: 100% !important;
    margin: 14px 0 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    border: 1px solid #334155 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
}

.message.bot th, .message-bot th, .deliverables-card th {
    background: #1e293b !important;
    color: #38bdf8 !important;
    font-weight: 700 !important;
    font-size: 0.86rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    border-bottom: 1px solid #334155 !important;
    padding: 10px 14px !important;
}

.message.bot td, .message-bot td, .deliverables-card td {
    background: #0f172a !important;
    color: #f8fafc !important;
    border-bottom: 1px solid #1e293b !important;
    padding: 10px 14px !important;
    font-size: 0.88rem !important;
}

.message.bot tr:last-child td, .message-bot tr:last-child td {
    border-bottom: none !important;
}

.message.bot tr:hover td, .message-bot tr:hover td {
    background: #172338 !important;
}

/* Suggestion Chips */
.suggestion-wrap {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin: 12px 0 8px 0;
}

.suggest-chip {
    background: #1e293b !important;
    color: #cbd5e1 !important;
    border: 1px solid #334155 !important;
    border-radius: 9999px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 6px 16px !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
}

.suggest-chip:hover {
    background: #334155 !important;
    border-color: #38bdf8 !important;
    color: #38bdf8 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(56, 189, 248, 0.2) !important;
}

/* Input Bar & Send Button */
.input-row {
    background: #0f172a !important;
    border: 1px solid #334155 !important;
    border-radius: 14px !important;
    padding: 6px 8px !important;
    display: flex;
    align-items: center;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

.input-row:focus-within {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25), 0 4px 16px rgba(0, 0, 0, 0.35) !important;
}

.msg-textbox textarea, .msg-textbox input {
    background: transparent !important;
    border: none !important;
    color: #ffffff !important;
    font-size: 0.95rem !important;
    padding: 8px 12px !important;
    box-shadow: none !important;
}

.msg-textbox textarea:focus, .msg-textbox input:focus {
    outline: none !important;
    box-shadow: none !important;
}

.send-btn {
    background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%) !important;
    color: #090d16 !important;
    border-radius: 10px !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    padding: 10px 22px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(56, 189, 248, 0.3) !important;
}

.send-btn:hover {
    background: linear-gradient(135deg, #7dd3fc 0%, #38bdf8 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(56, 189, 248, 0.45) !important;
}
"""

# Initial default recommendation proposal text
INITIAL_PROPOSAL = format_bundle_markdown(
    optimize_bundle(
        width_ft=8.0,
        length_ft=7.0,
        budget_inr=350000.0,
        aesthetic_theme="Modern Minimalist",
        include_thermostatic_shower=True,
    )
)

# 4. Interactive Application Layout
with gr.Blocks(title="Kohler AI Sales & Spatial Design Advisor") as demo:
    # Header
    with gr.Row(elem_classes=["header-card"]):
        with gr.Column(scale=8):
            gr.Markdown(
                """
                <div class="brand-title">K O H L E R</div>
                <div class="brand-subtitle">AI Sales & Spatial Design Advisor</div>
                """
            )
        with gr.Column(scale=2, min_width=90):
            reset_btn = gr.Button("Reset", elem_classes=["reset-btn"], size="sm")

    # Navigation Tabs
    with gr.Tabs() as tabs:
        
        # TAB 1: SPATIAL STUDIO & SUITE OPTIMIZER
        with gr.TabItem("Spatial Studio & Suite Optimizer", id="tab_studio"):
            with gr.Row():
                # LEFT COLUMN: Customer Constraints Panel
                with gr.Column(scale=5, elem_classes=["control-card"]):
                    gr.Markdown("### Customer Constraints & Specifications")
                    
                    with gr.Row():
                        in_width = gr.Slider(
                            minimum=4.0, maximum=16.0, value=8.0, step=0.5,
                            label="Room Width (ft)", info="e.g. 4 ft for powder room, 8 ft for master bath"
                        )
                        in_length = gr.Slider(
                            minimum=4.0, maximum=16.0, value=7.0, step=0.5,
                            label="Room Length (ft)", info="e.g. 5 ft for powder room, 10 ft for master suite"
                        )

                    in_budget = gr.Slider(
                        minimum=30000, maximum=1200000, value=350000, step=10000,
                        label="Target Budget Limit",
                        info="Includes catalog fixtures, 15% package discount and 18% GST"
                    )

                    with gr.Row():
                        preset_1 = gr.Button("1.5L (Powder)", elem_classes=["preset-btn"], size="sm")
                        preset_2 = gr.Button("3.5L (Modern)", elem_classes=["preset-btn"], size="sm")
                        preset_3 = gr.Button("6.5L (Zen Spa)", elem_classes=["preset-btn"], size="sm")
                        preset_4 = gr.Button("10L+ (Flagship)", elem_classes=["preset-btn"], size="sm")

                    in_theme = gr.Dropdown(
                        choices=[
                            "Modern Minimalist",
                            "Classic Luxury",
                            "Japanese Zen",
                            "Mid-Century Luxury",
                            "Smart High-Tech"
                        ],
                        value="Modern Minimalist",
                        label="Aesthetic Theme & Finish Harmonies",
                        info="Curates matching brassware, ceramic profiles, and vanity finishes"
                    )

                    in_preferences = gr.CheckboxGroup(
                        choices=[
                            "Include Freestanding/Alcove Bathtub",
                            "Include Intelligent Smart Toilet",
                            "Include Thermostatic Spa Shower"
                        ],
                        value=["Include Thermostatic Spa Shower"],
                        label="Fixture Preferences (Subject to physical space capacity)"
                    )

                    in_image = gr.Image(
                        type="pil",
                        label="Optional: Upload Architectural Floorplan / Sketch / Photo",
                        height=130,
                    )

                    generate_btn = gr.Button(
                        "Generate Suite Recommendation",
                        elem_classes=["plan-btn"],
                        size="lg"
                    )

                # RIGHT COLUMN: Solution Deliverables (Product Table, Financial Quote, Clearance Checks)
                with gr.Column(scale=6, elem_classes=["deliverables-card"]):
                    gr.Markdown("### Recommended Product Package & Quotation")
                    
                    proposal_summary = gr.Markdown(
                        value=INITIAL_PROPOSAL
                    )

                    consult_chat_btn = gr.Button(
                        "Transfer this Suite Plan to AI Advisor for Questions",
                        elem_classes=["secondary-action-btn"]
                    )

        # TAB 2: CONVERSATIONAL AI ADVISOR
        with gr.TabItem("Conversational AI Advisor", id="tab_chat"):
            # Chatbot Viewport
            chatbot = gr.Chatbot(
                elem_id="kohler-chatbot",
                height=530,
                show_label=False,
                render_markdown=True,
                layout="bubble",
                placeholder="### Kohler AI Sales & Spatial Design Advisor\n\nAsk about personalized suites, room dimensions, budgets, or catalog specifications...",
            )

            # Suggestion Chips
            with gr.Row(elem_classes=["suggestion-wrap"]):
                chip1 = gr.Button("8x7 ft Master Bath Suite with 3L Budget", elem_classes=["suggest-chip"], size="sm")
                chip2 = gr.Button("Japanese Zen Spa Suite for 6x8 ft Space", elem_classes=["suggest-chip"], size="sm")
                chip3 = gr.Button("Full Portfolio Catalogue Overview", elem_classes=["suggest-chip"], size="sm")
                chip4 = gr.Button("Veil Smart Toilet Specifications & Pricing", elem_classes=["suggest-chip"], size="sm")

            # Input Bar
            with gr.Row(elem_classes=["input-row"]):
                msg_input = gr.Textbox(
                    placeholder="Ask about personalized suites, room dimensions, budgets, or catalog specs...",
                    show_label=False,
                    container=False,
                    scale=9,
                    elem_classes=["msg-textbox"],
                    autofocus=True,
                )
                send_btn = gr.Button("Send", elem_classes=["send-btn"], scale=1)

    # 5. Handlers

    def on_generate_suite(width, length, budget, theme, preferences, image):
        has_tub = "Include Freestanding/Alcove Bathtub" in (preferences or [])
        has_smart = "Include Intelligent Smart Toilet" in (preferences or [])
        has_shower = "Include Thermostatic Spa Shower" in (preferences or [])

        result = optimize_bundle(
            width_ft=float(width),
            length_ft=float(length),
            budget_inr=float(budget),
            aesthetic_theme=theme,
            include_bathtub=has_tub,
            include_smart_toilet=has_smart,
            include_thermostatic_shower=has_shower,
        )
        return format_bundle_markdown(result)

    def user_submit(message: str, history: list):
        if not message or not str(message).strip():
            return "", history
        clean_msg = extract_text_query(message).strip()
        if not clean_msg:
            return "", history
        history = (history or []) + [{"role": "user", "content": clean_msg}]
        return "", history

    async def bot_respond(history: list):
        if not history:
            return
        
        user_msg = ""
        for item in reversed(history):
            if isinstance(item, dict) and item.get("role") == "user":
                user_msg = extract_text_query(item.get("content", ""))
                break
            elif isinstance(item, (list, tuple)) and len(item) > 0:
                user_msg = extract_text_query(item[0])
                break

        if not user_msg.strip():
            return

        final_text = ""
        history = history + [{"role": "assistant", "content": "Consulting Kohler spatial and pricing engines..."}]
        yield history

        try:
            async for update in smart_process_query(agent, user_msg):
                u_type = update.get("type")
                if u_type == "activity":
                    msg = update.get("msg", "")
                    history[-1]["content"] = f"{msg}"
                    yield history
                elif u_type == "tool_call":
                    tool_name = update.get("name", "")
                    if "bundle" in tool_name or "room" in tool_name:
                        history[-1]["content"] = "Sizing room dimensions, clearances, and optimizing bundle..."
                    elif "catalog" in tool_name:
                        history[-1]["content"] = "Retrieving Kohler specifications and finishes..."
                    elif "calculator" in tool_name:
                        history[-1]["content"] = "Computing package discounts and 18% GST..."
                    elif "inventory" in tool_name:
                        history[-1]["content"] = "Checking warehouse stock and transit lead times..."
                    else:
                        history[-1]["content"] = f"Processing {tool_name}..."
                    yield history
                elif u_type == "final":
                    final_text = update.get("content", "")
        except Exception as e:
            print(f"[Error in bot_respond] {e}", flush=True)
            final_text = f"An error occurred while processing: {e}. Please try again."

        if final_text:
            step = max(4, len(final_text) // 100)
            for i in range(0, len(final_text), step):
                history[-1]["content"] = final_text[: i + step]
                yield history
                await asyncio.sleep(0.01)
            history[-1]["content"] = final_text
            yield history

    def transfer_to_chat(width, length, budget, theme, history):
        prompt_text = f"Can you review my customized {theme} bathroom plan for a {width}x{length} ft space with a {budget:,.0f} budget limit?"
        history = (history or []) + [{"role": "user", "content": prompt_text}]
        return gr.Tabs(selected="tab_chat"), history, ""

    # Button & Event Bindings
    generate_btn.click(
        fn=on_generate_suite,
        inputs=[in_width, in_length, in_budget, in_theme, in_preferences, in_image],
        outputs=[proposal_summary],
    )

    preset_1.click(fn=lambda: 150000, outputs=[in_budget])
    preset_2.click(fn=lambda: 350000, outputs=[in_budget])
    preset_3.click(fn=lambda: 650000, outputs=[in_budget])
    preset_4.click(fn=lambda: 1000000, outputs=[in_budget])

    consult_chat_btn.click(
        fn=transfer_to_chat,
        inputs=[in_width, in_length, in_budget, in_theme, chatbot],
        outputs=[tabs, chatbot, msg_input],
    ).then(
        fn=bot_respond,
        inputs=[chatbot],
        outputs=[chatbot],
    )

    msg_input.submit(
        fn=user_submit,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot],
    ).then(
        fn=bot_respond,
        inputs=[chatbot],
        outputs=[chatbot],
    )

    send_btn.click(
        fn=user_submit,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot],
    ).then(
        fn=bot_respond,
        inputs=[chatbot],
        outputs=[chatbot],
    )

    # Chip Actions
    chip_queries = {
        chip1: "Plan a luxury 8x7 ft master bathroom suite with a 3,00,000 budget and modern minimalist theme.",
        chip2: "Recommend an authentic Japanese Zen organic spa bathroom suite for a 6x8 ft space with teak vanity and rainhead.",
        chip3: "Show me the catalogue and all product categories with pricing.",
        chip4: "What finishes, dimensions, and pricing are available for the Veil smart toilet?",
    }

    for chip_btn, prompt_text in chip_queries.items():
        chip_btn.click(
            fn=lambda h, p=prompt_text: ("", (h or []) + [{"role": "user", "content": p}]),
            inputs=[chatbot],
            outputs=[msg_input, chatbot],
        ).then(
            fn=bot_respond,
            inputs=[chatbot],
            outputs=[chatbot],
        )

    # Reset
    def on_reset():
        return [], "", INITIAL_PROPOSAL

    reset_btn.click(
        fn=on_reset,
        outputs=[chatbot, msg_input, proposal_summary]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--share", action="store_true", help="Generate a public 72-hour temporary URL")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the prototype server on")
    args = parser.parse_args()

    share_flag = args.share or os.getenv("SHARE_PROTOTYPE", "false").lower() in ["true", "1", "yes"]
    
    print(f"Launching Kohler AI Sales & Spatial Design Advisor (Port={args.port})...", flush=True)
    demo.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=share_flag,
        css=CUSTOM_CSS,
        theme=gr.themes.Base(),
        show_error=True,
    )
