import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure UTF-8 output in Windows terminal
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agent import create_agent, smart_process_query
from llama_index.core.workflow import Context

load_dotenv()

async def main():
    print("=========================================================")
    print(" [KOHLER] Autonomous Shopping & Specs Agent (Zero API Cost)")
    print(" Equipped with Fast-Path Router, In-Memory Cache & Tools")
    print(" Type 'exit' to quit.")
    print("=========================================================\n")
    
    agent = create_agent()
    ctx = Context(agent)  # Persistent conversation memory across multi-turn interactions

    while True:
        try:
            question = input("\nYou: ")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
            
        if not question.strip():
            continue
        if question.strip().lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break

        final_response = ""
        async for update in smart_process_query(agent, question, ctx=ctx):
            u_type = update.get("type")
            if u_type == "route":
                print(f"\n[Route] {update['badge']}")
            elif u_type == "activity":
                print(f"  -> {update['msg']}")
            elif u_type == "tool_call":
                args = f"({update['args']})" if update.get("args") else ""
                print(f"  -> [Tool Call] {update['name']}{args}")
            elif u_type == "tool_result":
                print(f"  <- [Tool Output] {update['output']}...")
            elif u_type == "final":
                final_response = update["content"]

        print(f"\nAssistant:\n{final_response}\n")

if __name__ == "__main__":
    asyncio.run(main())