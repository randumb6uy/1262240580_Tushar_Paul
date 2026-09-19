import os
import chromadb

# Silence warnings and force offline cache mode
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.tools import FunctionTool
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.core.schema import QueryBundle
from llama_index.core.base.response.schema import Response

# In-memory LRU Cache for sub-millisecond retrieval
_CATALOG_CACHE: dict[str, Response] = {}

def extract_clean_query(raw_query) -> str:
    """Safely extracts clean query string even if LLM passed a nested dict or JSON-string."""
    if isinstance(raw_query, dict):
        val = raw_query.get("value") or raw_query.get("query") or raw_query.get("input")
        if val:
            return extract_clean_query(val)
        for v in raw_query.values():
            if isinstance(v, (str, dict)):
                return extract_clean_query(v)
    elif isinstance(raw_query, str):
        s = raw_query.strip()
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("`{") and s.endswith("}`")):
            import ast, re
            try:
                parsed = ast.literal_eval(s)
                if isinstance(parsed, dict):
                    return extract_clean_query(parsed)
            except Exception:
                pass
            m = re.search(r"['\"]value['\"]\s*:\s*['\"]([^'\"]+)['\"]", s)
            if m:
                return m.group(1)
        return s
    return str(raw_query)

class CachedQueryEngine(BaseQueryEngine):
    """Wraps a query engine with an in-memory cache for 0ms repeat retrievals."""
    def __init__(self, query_engine: BaseQueryEngine):
        super().__init__(callback_manager=query_engine.callback_manager)
        self._engine = query_engine

    def _get_prompt_modules(self):
        return self._engine._get_prompt_modules()

    def _get_prompts(self):
        return self._engine._get_prompts()

    def _update_prompts(self, prompts):
        self._engine._update_prompts(prompts)

    def _clean_bundle(self, query_bundle: QueryBundle) -> QueryBundle:
        clean_text = extract_clean_query(query_bundle.query_str)
        if clean_text != query_bundle.query_str:
            return QueryBundle(
                query_str=clean_text,
                custom_embedding_strs=query_bundle.custom_embedding_strs,
                embedding=query_bundle.embedding,
            )
        return query_bundle

    def _query(self, query_bundle: QueryBundle) -> Response:
        query_bundle = self._clean_bundle(query_bundle)
        cache_key = query_bundle.query_str.strip().lower()
        if cache_key in _CATALOG_CACHE:
            return _CATALOG_CACHE[cache_key]
        
        response = self._engine.query(query_bundle)
        _CATALOG_CACHE[cache_key] = response
        return response

    async def _aquery(self, query_bundle: QueryBundle) -> Response:
        query_bundle = self._clean_bundle(query_bundle)
        cache_key = query_bundle.query_str.strip().lower()
        if cache_key in _CATALOG_CACHE:
            return _CATALOG_CACHE[cache_key]
        
        response = await self._engine.aquery(query_bundle)
        _CATALOG_CACHE[cache_key] = response
        return response

_SINGLETON_EMBED_MODEL = None
_SINGLETON_RERANKER = None
_SINGLETON_INDEX = None

def get_catalog_tool(
    chroma_path: str = "./chroma_db",
    collection_name: str = "kohler_agent",
    embed_model_name: str = "BAAI/bge-small-en-v1.5",
    rerank_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    llm=None,
    use_cache: bool = True,
) -> FunctionTool:
    """
    Constructs a two-stage retrieval tool over the Kohler product catalog:
    Stage 1: ChromaDB vector search (top 10 candidates).
    Stage 2: Cross-encoder reranker (re-ranks down to top 2 most relevant).
    Runs 100% locally on CPU without API charges, with in-memory caching.
    """
    global _SINGLETON_EMBED_MODEL, _SINGLETON_RERANKER, _SINGLETON_INDEX
    
    # 1. Local Embeddings (Singleton cached)
    if _SINGLETON_EMBED_MODEL is None:
        _SINGLETON_EMBED_MODEL = HuggingFaceEmbedding(model_name=embed_model_name)
    embed_model = _SINGLETON_EMBED_MODEL
    Settings.embed_model = embed_model
    if llm:
        Settings.llm = llm

    # 2. Connect to ChromaDB (Singleton cached)
    if _SINGLETON_INDEX is None:
        chroma_client = chromadb.PersistentClient(path=chroma_path)
        chroma_collection = chroma_client.get_or_create_collection(collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        _SINGLETON_INDEX = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
    index = _SINGLETON_INDEX

    # 3. Local Cross-Encoder Reranker (Singleton cached)
    if _SINGLETON_RERANKER is None:
        _SINGLETON_RERANKER = SentenceTransformerRerank(
            model=rerank_model_name,
            top_n=2,
        )
    reranker = _SINGLETON_RERANKER

    # 4. Two-stage query engine
    base_engine = index.as_query_engine(
        llm=llm,
        similarity_top_k=10,
        node_postprocessors=[reranker],
    )

    engine = CachedQueryEngine(base_engine) if use_cache else base_engine

    def search_kohler_catalog(query: str) -> str:
        """Search Kohler bathroom products including faucets, shower fixtures, toilets, bathtubs, sinks, vanities, specifications, dimensions, finishes, and catalog prices in INR."""
        clean_q = extract_clean_query(query)
        response = engine.query(clean_q)
        return str(response)

    async def asearch_kohler_catalog(query: str) -> str:
        clean_q = extract_clean_query(query)
        response = await engine.aquery(clean_q)
        return str(response)

    tool = FunctionTool.from_defaults(
        fn=search_kohler_catalog,
        async_fn=asearch_kohler_catalog,
        name="kohler_catalog_search",
        description=(
            "Search the official Kohler luxury bathroom catalog for product specifications, "
            "available finishes (Matte Black, Polished Chrome, Brushed Bronze), dimensions, "
            "product categories (faucets, showers, toilets, bathtubs, vanities), and exact prices in INR."
        ),
    )
    tool.query_engine = engine
    return tool

def retrieve_catalog_docs(query: str, top_k: int = 3) -> str:
    """Retrieves top matching product records directly from ChromaDB without LLM synthesis in 0ms."""
    global _SINGLETON_INDEX
    if _SINGLETON_INDEX is None:
        get_catalog_tool()
    clean_q = extract_clean_query(query)
    retriever = _SINGLETON_INDEX.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(clean_q)
    return "\n\n".join([f"- {n.node.get_content()}" for n in nodes])
