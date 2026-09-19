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

COMPREHENSIVE_TEST_SUITE = [
    # 1. Pure greeting & capabilities
    {
        "category": "1. Pure Greeting & Brand Introduction",
        "question": "Hello! Who are you and what Kohler products can you help me with?",
    },
    # 2. Mixed greeting with buying intent
    {
        "category": "2. Mixed Greeting + Buying Intent",
        "question": "Hello, I would like to buy something for my bathroom renovation.",
    },
    # 3. Catalog Discovery & Category Browsing
    {
        "category": "3. Full Catalog Discovery",
        "question": "Show me the catalogue and all available product categories.",
    },
    # 4. Custom Room Size: Compact Powder Room (4x5 ft)
    {
        "category": "4. Spatial Fit: Compact Powder Room (4x5 ft)",
        "question": "I have a 4x5 ft powder room, what products will fit nicely without looking cramped?",
    },
    # 5. Custom Room Size: Standard Full Bath (6x8 ft)
    {
        "category": "5. Spatial Fit: Standard Bath (6x8 ft)",
        "question": "What is the best aesthetic setup and fixture layout for a 6x8 ft bathroom?",
    },
    # 6. Custom Room Size: Grand Master Suite (10x10 ft)
    {
        "category": "6. Spatial Fit: Grand Master Suite (10x10 ft)",
        "question": "Plan a luxury 10x10 ft master bathroom suite with the best Kohler products.",
    },
    # 7. Minimum vs Maximum Product Fit in Custom Space
    {
        "category": "7. Minimum vs Maximum Pleasing Product Capacity",
        "question": "What is the minimum and maximum number of products I can fit into a 7x7 ft bathroom while keeping it pleasing?",
    },
    # 8. Long Output Proposal with Multi-Tool Math & Clearance Analysis
    {
        "category": "8. Long Output Proposal (Layout + Clearances + 15% Discount + 18% GST)",
        "question": "Provide a complete master bathroom remodel proposal for a 10x10 ft space with fixture dimensions, clearances, a 15% package discount, and 18% GST calculated.",
    },
    # 9. Specific product specs & finishes (Fast-Path)
    {
        "category": "9. Specific Product Specs & Finish (Purist)",
        "question": "What finishes, dimensions, and price in INR are available for the Purist faucet?",
    },
    # 10. Multi-step calculation with discount & tax (Agentic)
    {
        "category": "10. Multi-Step Calculation & Quote (Moxie + 20% + 18% GST)",
        "question": "What is the price of the Moxie Bluetooth showerhead in INR, and what would it cost with a 20% discount and 18% GST?",
    },
    # 11. Inventory & logistics lead time
    {
        "category": "11. Inventory & Delivery Transit Time",
        "question": "Do you have the Veil intelligent toilet in stock, and how long does delivery take to ZIP 90210?",
    },
    # 12. Out-of-catalog boundary check
    {
        "category": "12. Out-of-Catalog Boundary Check",
        "question": "Do you sell Kohler kitchen refrigerators or dishwashers?",
    },
]

async def run_test_suite():
    print("================================================================================", flush=True)
    print(" [TEST SUITE] RUNNING EXPANDED COMPREHENSIVE QUESTION EVALUATION (12 TESTS)", flush=True)
    print("================================================================================\n", flush=True)
    
    agent = create_agent()
    results = []

    for idx, item in enumerate(COMPREHENSIVE_TEST_SUITE, 1):
        cat = item["category"]
        q = item["question"]
        print(f"\n--- [Test {idx}/12: {cat}] ---", flush=True)
        print(f"Question: \"{q}\"", flush=True)
        
        ctx = None
        t0 = time.perf_counter()

        route_badge = "Unknown"
        tools_called = []
        final_answer = ""
        
        async for update in smart_process_query(agent, q, ctx=ctx):
            u_type = update.get("type")
            if u_type == "route":
                route_badge = update.get("badge", "")
                print(f"  Route: {route_badge}", flush=True)
            elif u_type == "tool_call":
                call_str = f"{update.get('name')}({update.get('args', '')})"
                tools_called.append(call_str)
                print(f"  -> Tool Call: {call_str}", flush=True)
            elif u_type == "final":
                final_answer = update.get("content", "")

        elapsed = time.perf_counter() - t0
        print(f"  Latency: {elapsed:.2f} s", flush=True)
        print(f"  Answer Preview:\n{final_answer[:220].strip()}...\n", flush=True)
        
        results.append({
            "index": idx,
            "category": cat,
            "question": q,
            "route": route_badge,
            "tools": tools_called,
            "latency": elapsed,
            "answer": final_answer.strip(),
        })

    print("\n================================================================================", flush=True)
    print(" [SUMMARY OF ALL 12 TEST EVALUATION RESULTS]", flush=True)
    print("================================================================================", flush=True)
    for r in results:
        tools_str = ", ".join(r["tools"]) if r["tools"] else "None (Direct/Catalog/1-step)"
        print(f"\n[#{r['index']}] Category: {r['category']}", flush=True)
        print(f"Q: {r['question']}", flush=True)
        print(f"Route: {r['route']} | Latency: {r['latency']:.2f}s | Tools: {tools_str}", flush=True)
        print(f"Answer:\n{r['answer']}", flush=True)
        print("-" * 80, flush=True)

if __name__ == "__main__":
    asyncio.run(run_test_suite())
