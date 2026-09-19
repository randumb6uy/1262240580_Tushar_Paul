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

from agent import create_agent, smart_process_query, get_llm
from llama_index.core.workflow import Context

BENCHMARK_PROMPTS = [
    {
        "id": "1. Spatial Fit",
        "query": "I have a 4x5 ft powder room, what products will fit nicely without looking cramped?",
    },
    {
        "id": "2. Long Remodel Proposal",
        "query": "Plan a luxury 10x10 ft master bathroom suite with the best Kohler products, itemized pricing in INR, and delivery timeline.",
    },
    {
        "id": "3. Multi-Tool Math Quote",
        "query": "What would the Moxie Bluetooth showerhead cost with a 20% discount and 18% GST in INR?",
    },
    {
        "id": "4. Fast Specs Lookup",
        "query": "What finishes and dimensions are available for the Purist faucet?",
    }
]

async def benchmark_provider(provider_name: str):
    print(f"\n{'='*80}")
    print(f" [BENCHMARK] TESTING PROVIDER: {provider_name.upper()}")
    print(f"{'='*80}")

    try:
        llm = get_llm(force_provider=provider_name)
    except Exception as e:
        print(f"Failed to initialize provider {provider_name}: {e}")
        return []

    agent = create_agent(llm=llm)
    results = []

    for item in BENCHMARK_PROMPTS:
        p_id = item["id"]
        query = item["query"]
        print(f"\n--- Running: {p_id} ---")
        print(f"Query: \"{query}\"")

        ctx = Context(agent)
        t0 = time.perf_counter()
        tools_used = []
        final_answer = ""
        route = ""

        try:
            async for update in smart_process_query(agent, query, ctx=ctx):
                u_type = update.get("type")
                if u_type == "route":
                    route = update.get("badge", "")
                elif u_type == "tool_call":
                    tools_used.append(f"{update.get('name')}")
                elif u_type == "final":
                    final_answer = update.get("content", "")

            elapsed = time.perf_counter() - t0
            print(f"Result in {elapsed:.2f}s | Route: {route} | Tools: {tools_used}")
            print(f"Snippet: {final_answer[:160].strip()}...\n")

            results.append({
                "id": p_id,
                "provider": provider_name,
                "latency": elapsed,
                "route": route,
                "tools": tools_used,
                "answer": final_answer,
            })
        except Exception as e:
            print(f"Error executing query: {e}")
            results.append({
                "id": p_id,
                "provider": provider_name,
                "latency": 0.0,
                "route": "ERROR",
                "tools": [],
                "answer": str(e),
            })

    return results

async def main():
    print("================================================================================")
    print(" KOHLER AI SALES ASSISTANT - MULTI-PROVIDER BENCHMARK COMPARISON")
    print("================================================================================")

    providers = ["ollama", "openrouter"]
    all_res = {}

    for p in providers:
        all_res[p] = await benchmark_provider(p)

    print("\n\n" + "="*80)
    print(" FINAL COMPARATIVE MATRIX")
    print("="*80)
    print(f"{'Benchmark Query':<28} | {'Provider':<12} | {'Latency (s)':<12} | {'Tools Used':<25}")
    print("-" * 80)
    for p, res_list in all_res.items():
        for r in res_list:
            tools_str = ", ".join(r["tools"]) if r["tools"] else "None"
            print(f"{r['id']:<28} | {p:<12} | {r['latency']:<12.2f} | {tools_str:<25}")

if __name__ == "__main__":
    asyncio.run(main())
