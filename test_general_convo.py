import asyncio
import os
import sys

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from agent import create_agent, smart_process_query

queries = [
    "yo",
    "ye wassup",
    "sup bro",
    "Hello!",
]

async def test():
    agent = create_agent()
    for q in queries:
        print(f"==================================================")
        print(f"USER: {q}")
        print(f"--------------------------------------------------")
        async for item in smart_process_query(agent, q):
            if item.get("type") == "final":
                print(f"AI RESPONSE:\n{item['content']}\n")

if __name__ == "__main__":
    asyncio.run(test())
