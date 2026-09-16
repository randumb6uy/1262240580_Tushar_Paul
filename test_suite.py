import asyncio
import os
import sys
import time
from dotenv import load_dotenv

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

load_dotenv()

from agent import create_agent, smart_process_query
from llama_index.core.workflow import Context

TEST_QUESTIONS = [
    # 1. General greeting & capabilities
    {
        "category": "General Conversation",
        "question": "Hello! Who are you and what Kohler products can you help me with?",
    },
    # 2. Specific product specs & pricing (Fast-Path)
    {
        "category": "Specific Faucet Specs & Finish (INR)",
        "question": "What finishes, dimensions, and price in INR are available for the Purist faucet?",
    },
    # 3. High-tech smart toilet specifications (Fast-Path)
    {
        "category": "Specific Smart Toilet Features (INR)",
        "question": "Tell me about the Numi 2.0 smart toilet and what luxury features it includes.",
    },
    # 4. Multi-hop tool calculation: Product + Discount + Tax (Agentic)
    {
        "category": "Multi-Step Calculation & Quote (INR & GST)",
        "question": "What is the price of the Moxie Bluetooth showerhead in INR, and what would it cost with a 20% discount and 18% GST?",
    },
    # 5. Inventory & Shipping estimate (Agentic)
    {
        "category": "Inventory & Logistics",
        "question": "Do you have the Veil intelligent toilet in stock, and how long does delivery take to ZIP 90210?",
    },
    # 6. Multi-product bundle quote across categories (Agentic / Fast-Path)
    {
        "category": "Multi-Product Package Quote (INR)",
        "question": "How much would it cost to buy both the Veer faucet and the Poplin vanity together in INR?",
    },
    # 7. Out-of-catalog boundary check
    {
        "category": "Out-of-Catalog Boundary Test",
        "question": "Do you sell Kohler kitchen refrigerators or dishwashers?",
    },
]

async def run_test_suite():
    print("================================================================================")
    print(" [TEST SUITE] RUNNING COMPREHENSIVE QUESTION EVALUATION")
    print("================================================================================\n")
    
    agent = create_agent()
    ctx = Context(agent)
    
    results = []

    for idx, item in enumerate(TEST_QUESTIONS, 1):
        cat = item["category"]
        q = item["question"]
        print(f"\n--- [Test {idx}/7: {cat}] ---")
        print(f"Question: \"{q}\"")
        
        t0 = time.perf_counter()
        route_badge = "Unknown"
        tools_called = []
        final_answer = ""
        
        async for update in smart_process_query(agent, q, ctx=ctx):
            u_type = update.get("type")
            if u_type == "route":
                route_badge = update.get("badge", "")
                print(f"  Route: {route_badge}")
            elif u_type == "tool_call":
                call_str = f"{update.get('name')}({update.get('args', '')})"
                tools_called.append(call_str)
                print(f"  -> Tool Call: {call_str}")
            elif u_type == "final":
                final_answer = update.get("content", "")

        elapsed = time.perf_counter() - t0
        print(f"  Latency: {elapsed:.2f} s")
        print(f"  Answer Preview: {final_answer[:140].strip()}...\n")
        
        results.append({
            "index": idx,
            "category": cat,
            "question": q,
            "route": route_badge,
            "tools": tools_called,
            "latency": elapsed,
            "answer": final_answer.strip(),
        })

    print("\n================================================================================")
    print(" [SUMMARY OF ALL TEST RESULTS]")
    print("================================================================================")
    for r in results:
        tools_str = ", ".join(r["tools"]) if r["tools"] else "None (Direct/1-step)"
        print(f"\n[#{r['index']}] Category: {r['category']}")
        print(f"Q: {r['question']}")
        print(f"Route: {r['route']} | Latency: {r['latency']:.2f}s | Tools: {tools_str}")
        print(f"Answer:\n{r['answer']}")
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(run_test_suite())
