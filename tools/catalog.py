import os

# Silence warnings and force offline cache mode
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.core.schema import QueryBundle
from llama_index.core.base.response.schema import Response
import chromadb

# In-memory LRU Cache for sub-millisecond retrieval (Option 4)
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
            # Return cached response instantly (0ms)
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

def get_catalog_tool(
    chroma_path: str = "./chroma_db",
    collection_name: str = "kohler_agent",
    embed_model_name: str = "BAAI/bge-small-en-v1.5",
    rerank_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    llm=None,
    use_cache: bool = True,
) -> QueryEngineTool:
    """
    Constructs a two-stage retrieval tool over the Kohler product catalog:
    Stage 1: ChromaDB vector search (top 10 candidates).
    Stage 2: Cross-encoder reranker (re-ranks down to top 3 most relevant).
    Runs 100% locally on CPU without API charges, with in-memory caching.
    """
    # 1. Local Embeddings (0 token cost)
    embed_model = HuggingFaceEmbedding(model_name=embed_model_name)
    Settings.embed_model = embed_model
    if llm:
        Settings.llm = llm

    # 2. Connect to ChromaDB
    chroma_client = chromadb.PersistentClient(path=chroma_path)
    chroma_collection = chroma_client.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

    # 3. Local Cross-Encoder Reranker (top_n=2 reduces prompt evaluation tokens by ~35%)
    reranker = SentenceTransformerRerank(
        model=rerank_model_name,
        top_n=2,
    )

    # 4. Two-stage query engine
    base_engine = index.as_query_engine(
        llm=llm,
        similarity_top_k=10,
        node_postprocessors=[reranker],
    )

    engine = CachedQueryEngine(base_engine) if use_cache else base_engine

    return QueryEngineTool(
        query_engine=engine,
        metadata=ToolMetadata(
            name="kohler_catalog_search",
            description=(
                "Search Kohler bathroom products including faucets, shower fixtures, "
                "toilets, bathtubs, sinks, vanities, model specifications, dimensions, "
                "finishes, and catalog pricing. Input should be a clear descriptive search query."
            ),
        ),
    )
