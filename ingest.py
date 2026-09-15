import os
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# 1. Load environment variables (reads OPENROUTER_API_KEY)
load_dotenv()

# 2. Set up the embedding model — OpenRouter Embeddings API
embed_model = OpenAIEmbedding(
    model_name="nvidia/nemotron-3-embed-1b:free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    api_base="https://openrouter.ai/api/v1",
)
Settings.embed_model = embed_model

# 3. Load all documents from the docs/ folder
documents = SimpleDirectoryReader("docs").load_data()
print(f"Loaded {len(documents)} documents")

# 4. Set up a persistent ChromaDB client and collection
chroma_client = chromadb.PersistentClient(path="./chroma_db")
try:
    chroma_client.delete_collection("kohler_products")
except Exception:
    pass
chroma_collection = chroma_client.get_or_create_collection("kohler_products")

# 5. Wrap Chroma as a LlamaIndex vector store
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# 6. Build the index — this is where chunking + embedding + storing all happens
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
)

print("Ingestion complete. Vector store saved to ./chroma_db")