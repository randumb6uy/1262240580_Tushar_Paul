import asyncio
import os
import sys
import time

# Silence warnings and force offline cache mode
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

from agent import create_agent, smart_process_query
from router import classify_query

async def run_benchmark():
    print("==========================================================")
    print(" [BENCHMARK] AGENTIC AI & FAST-PATH OPTIMIZATION SUITE")
    print("==========================================================\n")
    
    agent = create_agent()
    
    test_cases = [
        (
            "1. Direct Greeting (Chit-Chat)",
            "Hello! Who are you?",
            "Bypasses RAG & tools completely",
        ),
        (
            "2. Fast-Path RAG (Cold Search)",
            "What is the price and finishes for the Purist faucet?",
            "1-step ChromaDB + Cross-Encoder rerank",
        ),
        (
            "3. Fast-Path RAG (Cached Hit)",
            "What is the price and finishes for the Purist faucet?",
            "In-memory LRU cache hit (0ms retrieval)",
        ),
        (
            "4. Multi-Step Agent (Tools Required)",
            "What is the price of the Purist faucet, and what would it cost with a 15% discount?",
            "Full ReAct loop: Catalog + Calculator tools",
        ),
    ]

    results = []

    for name, query, description in test_cases:
        print(f"\n>>> Running: {name}")
        print(f"    Query: \"{query}\"")
        print(f"    Mode: {description}")
        
        route_detected = classify_query(query).value
        print(f"    Router Classification: [{route_detected}]")
        
        t0 = time.perf_counter()
        final_answer = ""
        events_captured = []
        
        async for update in smart_process_query(agent, query):
            u_type = update.get("type")
            if u_type == "tool_call":
                events_captured.append(f"tool:{update.get('name')}")
            elif u_type == "final":
                final_answer = update.get("content", "")

        elapsed = time.perf_counter() - t0
        print(f"    -> Elapsed Time: {elapsed:.2f} s")
        print(f"    -> Response Preview: {final_answer[:90].strip()}...")
        
        results.append({
            "name": name,
            "route": route_detected,
            "latency": elapsed,
            "tools": events_captured,
        })

    print("\n=========================================================================================")
    print(" [BENCHMARK RESULTS] SPEED COMPARISON SUMMARY")
    print("=========================================================================================")
    print(f"{'Test Scenario':<36} | {'Route':<15} | {'Latency':<10} | {'Status'}")
    print("-" * 89)
    for r in results:
        status = "INSTANT (Cache)" if r["name"].startswith("3.") else ("FAST (1-Step)" if "Fast" in r["name"] else "MULTI-STEP")
        print(f"{r['name']:<36} | {r['route']:<15} | {r['latency']:<7.2f} s  | {status}")
    print("=========================================================================================\n")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
