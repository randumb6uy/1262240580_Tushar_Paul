import json
import os
import re
from typing import List, Dict, Any, Optional
from llama_index.core.tools import FunctionTool

_PRODUCTS_CACHE: Optional[List[Dict[str, Any]]] = None
_RULES_CACHE: Optional[Dict[str, Any]] = None

def _get_catalog() -> List[Dict[str, Any]]:
    global _PRODUCTS_CACHE
    if _PRODUCTS_CACHE is None:
        products = []
        path = os.path.join(os.path.dirname(__file__), "..", "docs", "products.jsonl")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        products.append(json.loads(line))
        _PRODUCTS_CACHE = products
    return _PRODUCTS_CACHE

def _get_rules() -> Dict[str, Any]:
    global _RULES_CACHE
    if _RULES_CACHE is None:
        path = os.path.join(os.path.dirname(__file__), "..", "docs", "aesthetic_rules.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                _RULES_CACHE = json.load(f)
        else:
            _RULES_CACHE = {}
    return _RULES_CACHE

def _clean_input(val: Any) -> str:
    if isinstance(val, dict):
        return _clean_input(val.get("query") or val.get("value") or val.get("input") or list(val.values())[0])
    return str(val).strip()

def _matches_category(target: str, cat: str, p_type: str = "") -> bool:
    if not target:
        return True
    t = target.lower().strip()
    c = cat.lower().strip()
    ty = p_type.lower().strip()
    if t in c or c in t or t in ty or ty in t:
        return True
    if t.rstrip("s") in c.rstrip("s") or c.rstrip("s") in t.rstrip("s"):
        return True
    if (t.endswith("y") and t[:-1] in c) or (c.endswith("ies") and c[:-3] in t):
        return True
    return False

def recommend_aesthetic_matches(
    query_product_or_style: str,
    target_category: str = "",
) -> str:
    """
    Recommends aesthetically matched Kohler fixtures (coordinating metal finishes,
    matching design aesthetics, and complementary collections) and calculates
    exclusive package combo discounts in Indian Rupees (₹ INR).

    Args:
        query_product_or_style: Name of a Kohler product (e.g. 'Purist faucet', 'Veer', 'Moxie')
                                OR an aesthetic theme (e.g. 'modern minimalist', 'organic zen spa', 'matte black', 'mid-century brass').
        target_category: Optional specific category to match (e.g. 'vanities', 'showers', 'toilets', 'faucets').

    Returns:
        Curated aesthetic bundle with design synergy explanation, itemized pricing, combo discount savings, and final total in INR.
    """
    raw_query = _clean_input(query_product_or_style)
    target_cat = _clean_input(target_category).lower()
    catalog = _get_catalog()
    rules = _get_rules()

    if not catalog:
        return "Error: Product catalog not loaded."

    style_suites = rules.get("style_suites", {})
    finish_coordination = rules.get("finish_coordination", {})
    discount_tiers = rules.get("discount_tiers", {})

    q_lower = raw_query.lower()

    # 1. Check if query matches a curated style suite directly
    matched_suite_key = None
    for s_key, suite_data in style_suites.items():
        if (s_key in q_lower or
            suite_data["name"].lower() in q_lower or
            any(w in q_lower for w in s_key.split("_")) and ("suite" in q_lower or "theme" in q_lower or "style" in q_lower or "bathroom" in q_lower)):
            matched_suite_key = s_key
            break

    # Specific theme keyword overrides
    if not matched_suite_key:
        if "zen" in q_lower or "spa" in q_lower or "japanese" in q_lower:
            matched_suite_key = "organic_zen_spa"
        elif "scandinavian" in q_lower or "nordic" in q_lower:
            matched_suite_key = "scandinavian_warm_modern"
        elif "powder" in q_lower or "compact" in q_lower or "loft" in q_lower:
            matched_suite_key = "modern_powder_room"
        elif "artisan" in q_lower or "bourbon" in q_lower or "derring" in q_lower:
            matched_suite_key = "artisan_brass_powder"
        elif "touchless" in q_lower or "hygiene" in q_lower:
            matched_suite_key = "touchless_hygiene"
        elif "two-tone" in q_lower or "two tone" in q_lower or "dual-tone" in q_lower:
            matched_suite_key = "two_tone_designer"
        elif "brass" in q_lower or "bronze" in q_lower or "mid-century" in q_lower or "mid century" in q_lower:
            matched_suite_key = "mid_century_luxury"
        elif "minimal" in q_lower or "urban" in q_lower or "black" in q_lower:
            matched_suite_key = "modern_minimalist"
        elif "smart" in q_lower or "high tech" in q_lower or "high-tech" in q_lower or "tech" in q_lower:
            matched_suite_key = "smart_high_tech"
        elif "traditional" in q_lower or "heritage" in q_lower or "classic" in q_lower or "farmhouse" in q_lower:
            matched_suite_key = "classic_heritage"

    # If curated style suite identified:
    if matched_suite_key:
        suite = style_suites[matched_suite_key]
        suite_product_names = suite.get("recommended_products", [])
        selected_products = [p for p in catalog if p["name"] in suite_product_names]
        
        # If target_category specified, filter or prioritize
        if target_cat:
            cat_filtered = [p for p in selected_products if target_cat in p.get("category", "").lower()]
            if cat_filtered:
                selected_products = cat_filtered

        return _build_combo_response(
            title=f"Curated Aesthetic Suite: {suite['name']}",
            design_rationale=f"Design Philosophy: {suite['style_vibe']}\nFocal Finish: {suite['focal_finish']}",
            products=selected_products,
            discount_tiers=discount_tiers
        )

    # 2. Product-driven aesthetic matching
    # Find the anchor product
    anchor_product = None
    for p in catalog:
        if p["name"].lower() in q_lower or any(part in q_lower for part in p["name"].lower().split() if len(part) > 3):
            anchor_product = p
            break

    # Fallback search if exact name didn't match
    if not anchor_product:
        # Search by words
        q_tokens = [w for w in re.split(r"\W+", q_lower) if len(w) > 2]
        scored_prods = []
        for p in catalog:
            score = sum(1 for t in q_tokens if t in p["name"].lower() or t in p.get("type", "").lower())
            if score > 0:
                scored_prods.append((score, p))
        if scored_prods:
            scored_prods.sort(key=lambda x: x[0], reverse=True)
            anchor_product = scored_prods[0][1]

    if not anchor_product:
        # Fallback to modern minimalist if no product could be parsed
        anchor_product = catalog[0]

    anchor_name = anchor_product["name"]
    anchor_finish = anchor_product.get("finish", "")
    anchor_family = anchor_product.get("finish_family", "")
    anchor_style = anchor_product.get("aesthetic_style", "")
    anchor_cat = anchor_product.get("category", "")

    # Look up compatible finishes from rules
    compatible_finishes = []
    finish_desc = ""
    for fam_key, fam_data in finish_coordination.items():
        if fam_key.lower() in anchor_family.lower() or anchor_family.lower() in fam_key.lower():
            compatible_finishes = [f.lower() for f in fam_data.get("compatible_finishes", [])]
            finish_desc = fam_data.get("description", "")
            break

    # Score complementary candidates from other categories
    candidate_list = []
    for p in catalog:
        if p["name"] == anchor_name:
            continue
        
        p_cat = p.get("category", "")
        p_type = p.get("type", "")
        # If user asked for a specific category, only pick from that category
        if target_cat and not _matches_category(target_cat, p_cat, p_type):
            continue
        elif not target_cat and p_cat == anchor_cat:
            # Prefer cross-category pairings (e.g. faucet with vanity, shower, toilet)
            continue

        score = 0
        p_finish = p.get("finish", "").lower()
        p_family = p.get("finish_family", "").lower()
        p_style = p.get("aesthetic_style", "").lower()

        # Direct finish match
        if anchor_family and anchor_family.lower() in p_family:
            score += 15
        elif any(comp in p_finish for comp in compatible_finishes):
            score += 10

        # Aesthetic style alignment
        if anchor_style and anchor_style.lower() in p_style:
            score += 10

        candidate_list.append((score, p))

    candidate_list.sort(key=lambda x: x[0], reverse=True)

    # Pick top complementary products ensuring diversity across categories
    selected_products = [anchor_product]
    used_categories = {anchor_cat}

    max_picks = 1 if target_cat else 3  # 2 items if specific category requested, 4 items for full suite

    for score, p in candidate_list:
        p_cat = p.get("category", "")
        if target_cat or (p_cat not in used_categories):
            selected_products.append(p)
            used_categories.add(p_cat)
            if len(selected_products) >= max_picks + 1:
                break

    # Construct design rationale
    rationale = (
        f"Aesthetic Coordination Rationale:\n"
        f"  - Anchor Fixture: {anchor_name} ({anchor_finish})\n"
        f"  - Design Style: {anchor_style} | Finish Palette: {anchor_family}\n"
        f"  - Styling Note: {finish_desc or 'Carefully coordinated metallic accents and complementary silhouettes ensure seamless visual harmony across your bathroom space.'}"
    )

    return _build_combo_response(
        title=f"Aesthetic Combination: Coordinated {anchor_family} Collection",
        design_rationale=rationale,
        products=selected_products,
        discount_tiers=discount_tiers
    )

def _build_combo_response(
    title: str,
    design_rationale: str,
    products: List[Dict[str, Any]],
    discount_tiers: Dict[str, Any],
) -> str:
    n_items = len(products)
    if n_items == 0:
        return "No matching products found."

    # Determine discount tier
    if n_items == 2:
        tier = discount_tiers.get("2_items", {"discount_percent": 10.0, "tier_name": "Aesthetic Duo Combo (10% Off)"})
    elif n_items == 3:
        tier = discount_tiers.get("3_items", {"discount_percent": 15.0, "tier_name": "Complete Design Suite (15% Off)"})
    elif 4 <= n_items <= 5:
        tier = discount_tiers.get("4_or_5_items", {"discount_percent": 18.0, "tier_name": "Full Master Bath Remodel Package (18% Off)"})
    elif n_items >= 6:
        tier = discount_tiers.get("6_or_more_items", {"discount_percent": 22.0, "tier_name": "Whole-Home Ultimate Luxury Estate Package (22% Off)"})
    else:
        tier = {"discount_percent": 0.0, "tier_name": "Single Item"}

    discount_percent = tier["discount_percent"]
    tier_name = tier["tier_name"]

    subtotal = sum(float(p["price"]) for p in products)
    discount_amount = subtotal * (discount_percent / 100.0)
    taxable = subtotal - discount_amount
    tax_amount = taxable * 0.18  # 18% GST
    grand_total = taxable + tax_amount

    output_lines = [
        f"### {title}",
        "----------------------------------------------------------------------",
        design_rationale,
        "",
        "Coordinated Product Combination:",
    ]

    for idx, p in enumerate(products, 1):
        output_lines.append(
            f"  {idx}. {p['name']} ({p.get('type', 'Fixture')})\n"
            f"     - Finish: {p.get('finish', 'Standard')}\n"
            f"     - Style: {p.get('aesthetic_style', 'Designer')}\n"
            f"     - Catalog Price: ₹{float(p['price']):,.2f} INR"
        )

    output_lines.extend([
        "",
        "Package Pricing & Combo Discount Breakdown:",
        f"  - Combined Catalog Total ({n_items} items): ₹{subtotal:,.2f} INR",
        f"  - Applied Promotional Deal: {tier_name}",
        f"  - Instant Combo Savings: -₹{discount_amount:,.2f} INR ({discount_percent}% off)",
        f"  - Subtotal after Discount: ₹{taxable:,.2f} INR",
        f"  - Estimated GST (18%): +₹{tax_amount:,.2f} INR",
        f"  - Final Grand Package Total: ₹{grand_total:,.2f} INR",
        "----------------------------------------------------------------------",
        "Design & Purchasing Guidance: Ordering these fixtures together as a coordinated suite guarantees 100% finish matching and locks in this package discount."
    ])

    return "\n".join(output_lines)

aesthetic_tool = FunctionTool.from_defaults(
    fn=recommend_aesthetic_matches,
    name="aesthetic_combo_recommender",
    description=(
        "Recommends aesthetically matched Kohler bathroom fixtures (coordinating metal finishes, "
        "matching aesthetic styles like modern minimalist, mid-century brass, or zen spa) and calculates "
        "promotional package combo discounts (10% to 18% off) with itemized pricing in INR (₹)."
    ),
)
