import re
from enum import Enum

class QueryRoute(str, Enum):
    GREETING = "greeting"
    CATALOG_OVERVIEW = "catalog_overview"
    FAST_PATH_RAG = "fast_path_rag"
    AGENTIC = "agentic"

def extract_text_query(query) -> str:
    """Safely extracts clean string text from any data structure (str, list, dict, etc.)."""
    if isinstance(query, str):
        return query
    if isinstance(query, list):
        parts = []
        for item in query:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or item.get("value") or ""))
            else:
                parts.append(str(item))
        return " ".join(p for p in parts if p)
    if isinstance(query, dict):
        return str(query.get("text") or query.get("content") or query.get("value") or "")
    return str(query or "")

# Trigger patterns for multi-step agent actions
MATH_PATTERNS = [
    r"\bdiscount\b", r"\b\d+%\b", r"\bpercent\b", r"\bquote\b", r"\btax\b",
    r"\btotal\b", r"\bbundle\b", r"\bpackage\b", r"\bsum\b", r"\bcost with\b",
    r"\bcalculate\b", r"\bhow much for both\b", r"\bcheaper\b", r"\bhow much would it cost with\b",
    r"\bgst\b", r"\bestimate\b", r"\bprice\b", r"\bpricing\b", r"\bcost\b", r"\bhow much\b",
    r"\bbudget\b", r"\bunder\s*\d+\b", r"\b₹\b", r"\binr\b", r"\brupee\b", r"\brupees\b",
    r"\blakh\b", r"\blacs?\b", r"\bk\b"
]

THEME_PATTERNS = [
    r"\bminimalist\b", r"\bmodern\b", r"\bclassic\b", r"\bzen\b", r"\bjapanese\b",
    r"\bmid-century\b", r"\bheritage\b", r"\bhigh-tech\b", r"\bsmart\b", r"\bluxury\b",
    r"\bcontemporary\b", r"\bvintage\b", r"\btraditional\b", r"\bspa\b"
]

INVENTORY_PATTERNS = [
    r"\bin stock\b", r"\bstock\b", r"\binventory\b", r"\blead time\b",
    r"\bship\b", r"\bshipping\b", r"\bdelivery\b", r"\bzip\b", r"\bpincode\b", r"\bpin\b", r"\bwarehouse\b",
    r"\bavailable in stock\b", r"\bavailability\b", r"\bwhen will it arrive\b", r"\btransit\b"
]

ROOM_PATTERNS = [
    r"\b\d+(?:\.\d+)?\s*(?:ft|feet|foot|'|m|meter)?\s*(?:x|by|\*)\s*\d+(?:\.\d+)?\b",
    r"\b\d+\s*(?:sq\s*ft|sqft|square\s*feet)\b",
    r"\broom size\b", r"\blayout\b", r"\bpowder room\b", r"\bmaster bath\b",
    r"\bmaster suite\b", r"\bfit\b", r"\bfitted\b", r"\bhow many.*(?:products|items|fixtures).*fit\b",
    r"\bhow much.*(?:products|items|fixtures).*fit\b", r"\bfloor plan\b", r"\bpleasing\b",
    r"\bremodel\b", r"\bspace planning\b", r"\bclearance\b", r"\bdesign my\b",
    r"\bfit in a room\b", r"\bfitted in a room\b", r"\bbathroom dimension\b",
    r"\brecommend.*(?:bundle|suite|package|combination|products)\b"
]

CATALOG_PATTERNS = [
    r"\b(?:show|view|give|browse|see)\s+(?:me\s+)?(?:the\s+)?(?:catalog|catalogue|brochure|portfolio|products)\b",
    r"\bwhat\s+(?:products|categories|options|fixtures|items)\s+do you\s+(?:have|sell|offer)\b",
    r"\b(?:show|list)\s+(?:me\s+)?all\s+(?:the\s+)?(?:products|categories|fixtures)\b",
    r"\bwhat\s+do you\s+(?:sell|offer)\b",
    r"\bi (?:would like to|want to|wanna)\s+buy\s+something\b",
    r"\bi am looking to buy\b",
    r"^\s*(?:catalogue|catalog|products|categories)\s*$",
]

GREETING_PATTERNS = [
    r"\b(hello|hi|hey|heyy|heyyy|hiya|howdy|greetings|good morning|good afternoon|good evening)\b",
    r"\b(yo|ye|wassup|whatsup|what's up|whats up|wazzup|sup|what's good|whats good)\b",
    r"\b(who are you|what do you do|how can you help me|what are your capabilities)\b",
    r"^\s*(yo|ye|sup|wassup|whatsup|hi|hello|hey|help)\s*$",
]

# Specific product indicators that should not be intercepted as pure greetings
SPECIFIC_PRODUCT_INDICATORS = [
    r"\bpurist\b", r"\bnumi\b", r"\bveil\b", r"\bmoxie\b", r"\bceric\b", r"\barcher\b",
    r"\bartifacts\b", r"\bcomposed\b", r"\bsensate\b", r"\bcaxton\b", r"\bpoplin\b",
    r"\bjute\b", r"\bsoutherk\b", r"\bmarabou\b", r"\btresham\b", r"\bjacquard\b",
    r"\bwatertile\b", r"\bawaken\b", r"\bdtv\b", r"\bstatement\b", r"\btoilet\b",
    r"\bfaucet\b", r"\bshower\b", r"\bvanity\b", r"\bbathtub\b", r"\btub\b", r"\bsink\b"
]

def classify_query(query) -> QueryRoute:
    """
    Fast, deterministic intent classifier (0ms overhead, 0 tokens).
    Routes queries to the fastest optimal execution path without regex traps.
    Handles any input type (str, list, dict) safely.
    """
    clean_q = extract_text_query(query).strip().lower()

    # 1. Complex Agentic Path (Room Planning, Calculations, or Inventory tools required)
    has_room = any(re.search(p, clean_q) for p in ROOM_PATTERNS)
    has_math = any(re.search(p, clean_q) for p in MATH_PATTERNS)
    has_inventory = any(re.search(p, clean_q) for p in INVENTORY_PATTERNS)
    
    if has_room or has_math or has_inventory:
        return QueryRoute.AGENTIC

    # 2. Comprehensive Catalog / Buying Discovery Route
    for pattern in CATALOG_PATTERNS:
        if re.search(pattern, clean_q):
            return QueryRoute.CATALOG_OVERVIEW

    # 3. Direct Chit-Chat / Greeting (Only if NO specific product or commercial intent is mentioned)
    has_product = any(re.search(p, clean_q) for p in SPECIFIC_PRODUCT_INDICATORS)
    if not has_product:
        for pattern in GREETING_PATTERNS:
            if re.search(pattern, clean_q):
                return QueryRoute.GREETING

    # 4. Fast-Path RAG (Standard single-product specifications, features, finishes, dimensions, single-item prices)
    return QueryRoute.FAST_PATH_RAG
