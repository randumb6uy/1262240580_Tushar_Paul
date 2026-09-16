import os
import sys
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

from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from agent import get_llm

def main():
    print("=========================================================")
    print(" [KOHLER] Classic Chat-Based Assistant (Side Baseline)")
    print(" Uses basic ContextChatEngine without autonomous tool calling")
    print(" Type 'exit' to quit.")
    print("=========================================================\n")

    # 1. Setup local offline embedding and LLM
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    Settings.embed_model = embed_model
    llm = get_llm()
    Settings.llm = llm

    # 2. Connect to ChromaDB
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    chroma_collection = chroma_client.get_or_create_collection("kohler_agent")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

    # 3. Simple ContextChatEngine
    SYSTEM_PROMPT = (
        "You are a helpful customer service chat assistant for Kohler products in India. "
        "All prices in the catalog are in Indian Rupees (₹ INR). Answer questions politely using the context."
    )
    chat_engine = index.as_chat_engine(
        chat_mode="context",
        similarity_top_k=3,
        system_prompt=SYSTEM_PROMPT,
    )

    while True:
        try:
            q = input("\nYou: ")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
        if not q.strip():
            continue
        if q.strip().lower() in ["exit", "quit", "q"]:
            break
        res = chat_engine.chat(q)
        print(f"\nAssistant: {res}\n")

if __name__ == "__main__":
    main()
