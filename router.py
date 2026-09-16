import re
from enum import Enum

class QueryRoute(str, Enum):
    GREETING = "greeting"
    FAST_PATH_RAG = "fast_path_rag"
    AGENTIC = "agentic"

# Trigger patterns for multi-step agent actions
MATH_PATTERNS = [
    r"\bdiscount\b", r"\b\d+%\b", r"\bpercent\b", r"\bquote\b", r"\btax\b",
    r"\btotal\b", r"\bbundle\b", r"\bpackage\b", r"\bsum\b", r"\bcost with\b",
    r"\bcalculate\b", r"\bhow much for both\b", r"\bcheaper\b", r"\bhow much would it cost with\b"
]

INVENTORY_PATTERNS = [
    r"\bin stock\b", r"\bstock\b", r"\binventory\b", r"\blead time\b",
    r"\bship\b", r"\bshipping\b", r"\bdelivery\b", r"\bzip\b", r"\bwarehouse\b",
    r"\bavailable in stock\b", r"\bavailability\b"
]

GREETING_PATTERNS = [
    r"\b(hello|hi|hey|heyy|heyyy|hiya|howdy|greetings|good morning|good afternoon|good evening)\b",
    r"\b(yo|ye|wassup|whatsup|what's up|whats up|wazzup|sup|what's good|whats good)\b",
    r"\b(who are you|what do you do|how can you help me|what are your capabilities)\b",
    r"^\s*(yo|ye|sup|wassup|whatsup|hi|hello|hey|help)\s*$",
]

def classify_query(query: str) -> QueryRoute:
    """
    Fast, deterministic intent classifier (0ms overhead, 0 tokens).
    Routes queries to the fastest optimal execution path.
    """
    clean_q = query.strip().lower()

    # 1. Direct Chit-Chat / Greeting
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, clean_q):
            return QueryRoute.GREETING

    # 2. Complex Agentic Path (Calculator or Inventory tools required)
    has_math = any(re.search(p, clean_q) for p in MATH_PATTERNS)
    has_inventory = any(re.search(p, clean_q) for p in INVENTORY_PATTERNS)
    
    if has_math or has_inventory:
        return QueryRoute.AGENTIC

    # 3. Fast-Path RAG (Standard product specifications, features, finishes, dimensions, single-item prices)
    return QueryRoute.FAST_PATH_RAG
