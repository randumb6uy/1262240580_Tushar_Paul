import os
import sys
from dotenv import load_dotenv

# Ensure UTF-8 output in Windows terminal
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.openrouter import OpenRouter
import chromadb

# 1. Load environment variables (this is where the API key comes from)
load_dotenv()

# 2. Set up the embedding model — OpenRouter Embeddings API (matches ingest.py)
embed_model = OpenAIEmbedding(
    model_name="nvidia/nemotron-3-embed-1b:free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    api_base="https://openrouter.ai/api/v1",
)
Settings.embed_model = embed_model

# 3. Set up the LLM — OpenRouter, using the free router
llm = OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="nvidia/nemotron-3.5-lightning:free",
    max_tokens=1024,
)
Settings.llm = llm

# 4. Reconnect to the existing ChromaDB collection (no re-embedding needed)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = chroma_client.get_or_create_collection("kohler_products")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

# 5. Load the index FROM the existing vector store
index = VectorStoreIndex.from_vector_store(vector_store)

# 6. Turn the index into a query engine
query_engine = index.as_query_engine(similarity_top_k=3)

# 7. Ask questions in a loop
if __name__ == "__main__":
    print("Ask a question about the Kohler product catalog (type 'exit' to quit)")
    while True:
        try:
            question = input("\nYou: ")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
        if not question.strip():
            continue
        if question.strip().lower() == "exit":
            break
        response = query_engine.query(question)
        print("\nAssistant:", response)