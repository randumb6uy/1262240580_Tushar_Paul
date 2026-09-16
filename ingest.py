import json
import os
import sys

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

from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

LOCAL_EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "BAAI/bge-small-en-v1.5")
embed_model = HuggingFaceEmbedding(model_name=LOCAL_EMBED_MODEL_NAME)
Settings.embed_model = embed_model

def load_jsonl_documents(jsonl_path: str = "docs/products.jsonl") -> list[Document]:
    """
    Reads structured JSONL catalog with high-speed microsecond parsing.
    Creates discrete per-product Document nodes with structured metadata.
    """
    if not os.path.exists(jsonl_path):
        from convert_to_jsonl import convert
        print(f"[Ingest] '{jsonl_path}' not found. Auto-generating from docs/*.txt...")
        convert()

    documents = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            
            # Text content is purely the single product's specs (~40 words)
            doc = Document(
                doc_id=f"prod_{idx:03d}",
                text=item["text"],
                metadata={
                    "name": item["name"],
                    "type": item["type"],
                    "category": item["category"],
                    "price": float(item["price"]),
                    "currency": item.get("currency", "INR"),
                    "usd_price": float(item.get("usd_price", 0.0)),
                    "finish": item["finish"],
                },
                excluded_llm_metadata_keys=["text"],
            )
            documents.append(doc)
            
    return documents

def ingest_documents(
    jsonl_path: str = "docs/products.jsonl",
    chroma_path: str = "./chroma_db",
    collection_name: str = "kohler_agent",
    force: bool = True
):
    """
    Indexes all atomic product records from products.jsonl into ChromaDB.
    Runs 100% locally with zero token cost.
    """
    documents = load_jsonl_documents(jsonl_path)
    print(f"[Ingest] Loaded {len(documents)} atomic product records from '{jsonl_path}'.")

    chroma_client = chromadb.PersistentClient(path=chroma_path)
    
    if force:
        try:
            chroma_client.delete_collection(collection_name)
            print(f"[Ingest] Cleared existing '{collection_name}' collection.")
        except Exception:
            pass

    chroma_collection = chroma_client.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    print("[Ingest] Building Vector Store Index with local BGE embeddings...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=True,
    )
    print(f"[Ingest] Ingestion complete. Vector store saved to '{chroma_path}' (Collection: '{collection_name}').")
    return index

if __name__ == "__main__":
    ingest_documents(force=True)