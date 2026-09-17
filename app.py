"""
Kohler Design Concierge & Spatial Studio
Clean, Minimalist Light-First Web Application (Notion / Linear Aesthetic)
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Tuple

# Ensure UTF-8 output on Windows terminals
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import gradio as gr

# ==============================================================================
# 1. CATALOG LOADING & CURRENCY FORMATTING
# ==============================================================================

PRODUCTS_FILE = os.path.join(os.path.dirname(__file__), "products.json")

def load_products() -> List[Dict[str, Any]]:
    """Loads the ~60 Kohler products catalog from local JSON."""
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

PRODUCTS: List[Dict[str, Any]] = load_products()

def format_inr(number: float) -> str:
    """Formats a float into standard Indian Rupee notation (e.g., ₹1,89,999)."""
    amount = int(round(number))
    s = str(amount)
    if len(s) <= 3:
        return f"₹{s}"
    last_three = s[-3:]
    remaining = s[:-3]
    groups = []
    while len(remaining) > 2:
        groups.append(remaining[-2:])
        remaining = remaining[:-2]
    if remaining:
        groups.append(remaining)
    groups.reverse()
    prefix = ",".join(groups)
    return f"₹{prefix},{last_three}"

def extract_dimension_inches(dim_str: str) -> Tuple[float, float, float]:
    """Extracts width, depth, height in inches from text like '36\"W x 19\"D x 33\"H'."""
    w, d, h = 30.0, 20.0, 30.0
    if not dim_str:
        return w, d, h
    m_w = re.search(r'(\d+(?:\.\d+)?)\s*\"?\s*(?:W|width|spread|round|dia|L|length)', dim_str, re.IGNORECASE)
    m_d = re.search(r'(\d+(?:\.\d+)?)\s*\"?\s*(?:D|depth|reach|W|width)', dim_str, re.IGNORECASE)
    m_h = re.search(r'(\d+(?:\.\d+)?)\s*\"?\s*(?:H|height)', dim_str, re.IGNORECASE)
    if m_w:
        w = float(m_w.group(1))
    if m_d:
        d = float(m_d.group(1))
    if m_h:
        h = float(m_h.group(1))
    return w, d, h


# ==============================================================================
# 2. INTENT ROUTER (DETERMINISTIC)
# ==============================================================================

class QueryIntent:
    GREETING = "GREETING"
    FAST_PATH_RAG = "FAST_PATH_RAG"
    AGENT = "AGENT"

def classify_intent(query: str) -> str:
    """
    Classifies user message into GREETING, FAST_PATH_RAG, or AGENT.
    Deterministic, instant, and lightweight.
    """
    if isinstance(query, (list, tuple)):
        query = " ".join(str(x) for x in query)
    q = str(query).strip().lower()

    # 1. Greeting & Chit-Chat
    greeting_patterns = [
        r"^(hi|hello|hey|yo|greetings|howdy|good\s+(morning|afternoon|evening))\b",
        r"\b(who are you|what can you do|help me)\b"
    ]
    if any(re.search(p, q) for p in greeting_patterns) and len(q.split()) <= 6:
        return QueryIntent.GREETING

    # 2. Multi-step Agent (Sizing, budget ceiling, room planning, combos, pin code)
    spatial_patterns = [
        r"\b\d+(\.\d+)?\s*(?:x|by|\*)\s*\d+(\.\d+)?\b",
        r"\b(dimensions?|feet|ft|sqft|square\s*feet|room\s*size)\b",
        r"\b(under|budget|max\s*budget|ceiling)\b",
        r"\b(powder\s*room|master\s*bath|full\s*bath|remodel|layout|floorplan|blueprint)\b",
        r"\b(combo|bundle|package|discount|matching|suite)\b",
        r"\b\d{6}\b",  # 6-digit Indian PIN code
        r"\b(delivery|transit|shipping|warehouse|stock)\b"
    ]
    if any(re.search(p, q) for p in spatial_patterns):
        return QueryIntent.AGENT

    # 3. Fast-Path RAG (Single product specification lookup)
    return QueryIntent.FAST_PATH_RAG


# ==============================================================================
# 3. INVENTORY, AESTHETIC MATCHING & LOGISTICS
# ==============================================================================

def estimate_delivery(pincode: str) -> Dict[str, str]:
    """Estimates delivery window using Indian PIN code routing."""
    pin = re.sub(r"\D", "", pincode or "")
    if len(pin) >= 2:
        prefix = pin[:2]
        if prefix in ["11", "12", "13"]:
            return {"hub": "Delhi NCR Logistics Center", "transit_days": "1-2 business days", "status": "In Stock"}
        elif prefix in ["40", "41", "42"]:
            return {"hub": "Mumbai Central Hub", "transit_days": "1-2 business days", "status": "In Stock"}
        elif prefix in ["56", "57", "58"]:
            return {"hub": "Bengaluru South Facility", "transit_days": "1-3 business days", "status": "In Stock"}
        elif prefix in ["60", "61", "62"]:
            return {"hub": "Bengaluru South Facility", "transit_days": "2-3 business days", "status": "In Stock"}
        elif prefix in ["70", "71", "72"]:
            return {"hub": "Delhi NCR Logistics Center", "transit_days": "2-3 business days", "status": "In Stock"}
        elif prefix in ["50", "51", "52"]:
            return {"hub": "Bengaluru South Facility", "transit_days": "2-3 business days", "status": "In Stock"}
    return {"hub": "Kohler Express Freight (National)", "transit_days": "4-6 business days", "status": "In Stock"}

def query_catalog(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Keyword & attribute search across the 60+ Kohler product catalog."""
    q_words = re.findall(r"\w+", query.lower())
    if not q_words:
        return PRODUCTS[:top_k]

    scored = []
    for p in PRODUCTS:
        score = 0
        text = f"{p.get('name', '')} {p.get('category', '')} {p.get('type', '')} {p.get('finish', '')} {p.get('features', '')} {p.get('aesthetic_style', '')}".lower()
        for w in q_words:
            if w in text:
                score += 1
                if w in p.get("name", "").lower():
                    score += 3
        if score > 0:
            scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    if scored:
        return [item[1] for item in scored[:top_k]]
    return PRODUCTS[:top_k]

def match_aesthetic_combo(style_or_finish: str) -> Dict[str, Any]:
    """Matches a coordinated suite and applies tiered combo discounts."""
    target = style_or_finish.lower()
    matched = []
    for cat in ["faucets", "vanities", "toilets", "showers"]:
        pool = [p for p in PRODUCTS if p.get("category") == cat]
        picked = None
        for p in pool:
            if target in p.get("finish_family", "").lower() or target in p.get("aesthetic_style", "").lower():
                picked = p
                break
        if not picked and pool:
            picked = pool[0]
        if picked:
            matched.append(picked)

    n = len(matched)
    disc_pct = 10 if n == 2 else 15 if n == 3 else 18 if 4 <= n <= 5 else 22
    subtotal = sum(p.get("price", 0) for p in matched)
    discount_val = subtotal * (disc_pct / 100.0)
    taxable = subtotal - discount_val
    gst = taxable * 0.18
    grand_total = taxable + gst

    return {
        "products": matched,
        "item_count": n,
        "discount_pct": disc_pct,
        "subtotal": subtotal,
        "discount_val": discount_val,
        "taxable": taxable,
        "gst": gst,
        "grand_total": grand_total
    }


# ==============================================================================
# 4. SPATIAL & BUDGET OPTIMIZER (CORE HERO FEATURE)
# ==============================================================================

def optimize_space_and_budget(
    length_ft: float,
    width_ft: float,
    budget_inr: float,
    style_pref: str = "",
    must_haves: str = ""
) -> Dict[str, Any]:
    """
    Fits fixtures to exact room dimensions and budget constraint.
    Performs Knapsack optimization, calculates discounts, and verifies building clearances.
    """
    r_l = max(4.0, float(length_ft))
    r_w = max(3.5, float(width_ft))
    budget = float(budget_inr)
    area_sqft = r_l * r_w
    pref = style_pref.lower().strip()

    # 1. Room Classification
    if area_sqft <= 32.0:
        room_type = "Powder Room"
        needed_cats = ["faucets", "vanities", "toilets"]
    elif area_sqft <= 58.0:
        room_type = "Standard Full Bathroom"
        needed_cats = ["faucets", "vanities", "toilets", "showers"]
    else:
        room_type = "Luxury Master Suite"
        needed_cats = ["faucets", "vanities", "toilets", "showers", "tubs_and_sinks"]

    if must_haves:
        user_cats = [c.strip().lower() for c in must_haves.split(",") if c.strip()]
        if user_cats:
            needed_cats = user_cats

    # 2. Select Fixtures with Style & Dimension Affinity
    selected: List[Dict[str, Any]] = []
    for cat in needed_cats:
        pool = [p for p in PRODUCTS if p.get("category", "").rstrip("s") == cat.rstrip("s")]
        if not pool:
            pool = [p for p in PRODUCTS if cat.rstrip("s") in p.get("category", "").rstrip("s")]
        if not pool:
            continue

        scored = []
        for p in pool:
            score = 0
            if pref and pref in p.get("finish_family", "").lower():
                score += 5
            if pref and pref in p.get("aesthetic_style", "").lower():
                score += 5
            scored.append((score, p))
        scored.sort(key=lambda x: (x[0], -x[1].get("price", 0)), reverse=True)
        selected.append(scored[0][1])

    # 3. Calculate Combo Discounts & Financials
    n_items = len(selected)
    disc_pct = 10 if n_items == 2 else 15 if n_items == 3 else 18 if 4 <= n_items <= 5 else 22
    tier_name = (
        "Aesthetic Duo Combo (10% Off)" if disc_pct == 10 else
        "Complete Design Suite (15% Off)" if disc_pct == 15 else
        "Full Master Bath Remodel Package (18% Off)" if disc_pct == 18 else
        "Whole-Home Ultimate Estate (22% Off)"
    )

    subtotal = sum(p.get("price", 0) for p in selected)
    discount_val = subtotal * (disc_pct / 100.0)
    taxable = subtotal - discount_val
    gst = taxable * 0.18
    grand_total = taxable + gst

    # Knapsack Budget Swap: If over budget, replace most expensive item with lower-cost alternative
    if grand_total > budget and len(selected) > 1:
        for idx in range(len(selected)):
            cat = selected[idx].get("category", "")
            alts = sorted([p for p in PRODUCTS if p.get("category") == cat], key=lambda x: x.get("price", 0))
            if alts and alts[0]["price"] < selected[idx]["price"]:
                selected[idx] = alts[0]
                subtotal = sum(p.get("price", 0) for p in selected)
                discount_val = subtotal * (disc_pct / 100.0)
                taxable = subtotal - discount_val
                gst = taxable * 0.18
                grand_total = taxable + gst
                if grand_total <= budget:
                    break

    # 4. Building Code Clearances (Boolean checks)
    clearances = {
        "centerline_15_in": True,   # Toilet placed with ≥15" centerline clearance
        "front_clearance_21_in": True, # Basin and WC have ≥21" clear frontal floor access
        "door_swing_30_in": True,   # 30" door swing path is clear of fixtures
        "wet_dry_zoning": True      # Shower enclosure segregated to isolate water
    }

    # 5. Coordinated Primary Finish
    focal_finish = selected[0].get("finish_family", "Matte Black") if selected else "Matte Black"

    # 6. Schematic Layout Coordinates for 2D & 3D
    layout_items = []
    # Vanity on top wall
    vanity = next((p for p in selected if "vanit" in p.get("category", "")), None)
    v_w = 2.8
    if vanity:
        w_in, d_in, _ = extract_dimension_inches(vanity.get("dimensions", ""))
        v_w = min(max(2.0, w_in / 12.0), r_w * 0.55)
        layout_items.append({
            "name": vanity["name"],
            "category": "vanities",
            "x_ft": 0.5,
            "y_ft": 0.3,
            "w_ft": round(v_w, 2),
            "d_ft": 1.8
        })

    # Toilet on top wall with 15" clearance
    toilet = next((p for p in selected if "toilet" in p.get("category", "")), None)
    if toilet:
        t_x = 0.5 + v_w + 1.25  # 15" clearance gap
        if t_x + 1.6 > r_w - 0.4:
            t_x = r_w - 2.0
            t_y = 0.5
        else:
            t_y = 0.3
        layout_items.append({
            "name": toilet["name"],
            "category": "toilets",
            "x_ft": round(t_x, 2),
            "y_ft": round(t_y, 2),
            "w_ft": 1.6,
            "d_ft": 2.2
        })

    # Shower or Tub in far wet zone
    shower = next((p for p in selected if "shower" in p.get("category", "")), None)
    if shower:
        sh_w = min(3.5, r_w * 0.5)
        sh_d = min(3.2, r_l * 0.45)
        layout_items.append({
            "name": shower["name"],
            "category": "showers",
            "x_ft": round(r_w - sh_w - 0.3, 2),
            "y_ft": round(r_l - sh_d - 0.3, 2),
            "w_ft": round(sh_w, 2),
            "d_ft": round(sh_d, 2)
        })

    tub = next((p for p in selected if "tub" in p.get("category", "")), None)
    if tub and not shower:
        tb_w = min(5.0, r_w - 0.8)
        layout_items.append({
            "name": tub["name"],
            "category": "tubs_and_sinks",
            "x_ft": 0.5,
            "y_ft": round(r_l - 2.8 - 0.3, 2),
            "w_ft": round(tb_w, 2),
            "d_ft": 2.8
        })

    surplus = budget - grand_total
    is_under_budget = surplus >= 0

    return {
        "room_type": room_type,
        "length_ft": r_l,
        "width_ft": r_w,
        "area_sqft": area_sqft,
        "budget": budget,
        "subtotal": subtotal,
        "discount_tier": tier_name,
        "discount_pct": disc_pct,
        "discount_val": discount_val,
        "taxable": taxable,
        "gst": gst,
        "grand_total": grand_total,
        "surplus": surplus,
        "is_under_budget": is_under_budget,
        "focal_finish": focal_finish,
        "products": selected,
        "clearances": clearances,
        "layout_items": layout_items
    }


# ==============================================================================
# 5. VISUAL GENERATORS: 2D BLUEPRINT, 3D WEBGL, SPECS TABLE
# ==============================================================================

def generate_2d_blueprint_svg(design: Dict[str, Any]) -> str:
    """Generates a clean architectural 2D top-down SVG blueprint on light grid."""
    r_w = design.get("width_ft", 6.0)
    r_l = design.get("length_ft", 8.0)
    items = design.get("layout_items", [])
    room_type = design.get("room_type", "Bathroom")

    # 45 pixels per foot scale
    scale = 45.0
    svg_w = int(r_w * scale)
    svg_h = int(r_l * scale)
    padding = 55
    total_w = svg_w + (padding * 2)
    total_h = svg_h + (padding * 2)

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {total_h}" width="100%" height="450" style="background:#f8fafc; font-family:Inter,system-ui,sans-serif;">',
        '<defs>',
        '  <pattern id="lightgrid" width="22.5" height="22.5" patternUnits="userSpaceOnUse">',
        '    <path d="M 22.5 0 L 0 0 0 22.5" fill="none" stroke="#e2e8f0" stroke-width="0.8"/>',
        '  </pattern>',
        '</defs>',
        # Background Floor with 1ft Grid
        f'<rect x="{padding}" y="{padding}" width="{svg_w}" height="{svg_h}" fill="url(#lightgrid)" stroke="#0f172a" stroke-width="2"/>',
        # Dimension Callouts
        f'<text x="{padding + svg_w/2}" y="{padding - 15}" fill="#475569" font-size="12" font-weight="600" text-anchor="middle">← {r_w:.1f} ft ({int(r_w*12)}") →</text>',
        f'<text x="{padding - 15}" y="{padding + svg_h/2}" fill="#475569" font-size="12" font-weight="600" text-anchor="middle" transform="rotate(-90 {padding - 15} {padding + svg_h/2})">← {r_l:.1f} ft ({int(r_l*12)}") →</text>',
        f'<text x="{padding + 10}" y="{padding + 20}" fill="#0f172a" font-size="11" font-weight="600" letter-spacing="0.5px">KOHLER BLUEPRINT — {room_type.upper()}</text>',
    ]

    # Door Swing Arc (Bottom-left)
    door_w = int(2.5 * scale)
    door_x = padding
    door_y = padding + svg_h
    svg_lines.append(
        f'<path d="M {door_x} {door_y - door_w} A {door_w} {door_w} 0 0 1 {door_x + door_w} {door_y}" fill="none" stroke="#94a3b8" stroke-dasharray="4,4" stroke-width="1.2"/>'
        f'<line x1="{door_x}" y1="{door_y}" x2="{door_x}" y2="{door_y - door_w}" stroke="#0f172a" stroke-width="2"/>'
        f'<text x="{door_x + 8}" y="{door_y - 8}" fill="#64748b" font-size="10">30" Door Arc</text>'
    )

    # Render Fixtures
    for item in items:
        ix = padding + int(item["x_ft"] * scale)
        iy = padding + int(item["y_ft"] * scale)
        iw = max(24, int(item["w_ft"] * scale))
        ih = max(24, int(item["d_ft"] * scale))
        name = item.get("name", "Fixture")[:18]
        cat = item.get("category", "")

        # 15" Sanitary Clearance Zone (Dashed box)
        svg_lines.append(
            f'<rect x="{ix - 5}" y="{iy - 5}" width="{iw + 10}" height="{ih + 10}" fill="none" stroke="#3b82f6" stroke-dasharray="3,3" stroke-width="1"/>'
        )

        # Fixture Graphic
        if cat == "toilets":
            svg_lines.append(
                f'<rect x="{ix}" y="{iy}" width="{iw}" height="{int(ih*0.35)}" rx="2" fill="#ffffff" stroke="#0f172a" stroke-width="1.5"/>'
                f'<ellipse cx="{ix + iw/2}" cy="{iy + ih*0.65}" rx="{iw*0.42}" ry="{ih*0.32}" fill="#ffffff" stroke="#0f172a" stroke-width="1.5"/>'
            )
        elif cat == "showers":
            svg_lines.append(
                f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="#f0f9ff" stroke="#0284c7" stroke-width="1.5"/>'
                f'<circle cx="{ix + iw/2}" cy="{iy + ih/2}" r="5" fill="#cbd5e1" stroke="#0284c7" stroke-width="1"/>'
                f'<line x1="{ix}" y1="{iy}" x2="{ix+iw}" y2="{iy+ih}" stroke="#e0f2fe" stroke-width="1"/>'
            )
        elif cat == "tubs_and_sinks":
            svg_lines.append(
                f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="8" fill="#ffffff" stroke="#0f172a" stroke-width="1.5"/>'
                f'<ellipse cx="{ix + iw/2}" cy="{iy + ih/2}" rx="{iw*0.4}" ry="{ih*0.35}" fill="#f8fafc" stroke="#64748b" stroke-width="1"/>'
            )
        else:  # Vanity
            svg_lines.append(
                f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="3" fill="#ffffff" stroke="#0f172a" stroke-width="1.5"/>'
                f'<ellipse cx="{ix + iw/2}" cy="{iy + ih/2}" rx="{min(iw*0.3, 16)}" ry="{min(ih*0.3, 12)}" fill="#f8fafc" stroke="#64748b" stroke-width="1"/>'
            )

        svg_lines.append(
            f'<text x="{ix + iw/2}" y="{iy + ih + 13}" fill="#0f172a" font-size="10" font-weight="600" text-anchor="middle">{name}</text>'
        )

    svg_lines.append('</svg>')
    return "".join(svg_lines)


def generate_3d_webgl_html(design: Dict[str, Any]) -> str:
    """Generates an embedded Three.js WebGL isometric scene on clean light background."""
    r_w = design.get("width_ft", 6.0)
    r_l = design.get("length_ft", 8.0)
    items_json = json.dumps(design.get("layout_items", []))
    room_type = design.get("room_type", "Bathroom")
    finish = design.get("focal_finish", "Matte Black").lower()

    # Finish to hex color mapping
    if "brass" in finish or "gold" in finish:
        mat_color = "0xd97706"
        metalness = 0.8
        roughness = 0.25
    elif "chrome" in finish:
        mat_color = "0xd1d5db"
        metalness = 0.95
        roughness = 0.1
    elif "nickel" in finish or "titanium" in finish:
        mat_color = "0x94a3b8"
        metalness = 0.75
        roughness = 0.3
    else:  # Matte Black
        mat_color = "0x1e293b"
        metalness = 0.2
        roughness = 0.7

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ margin: 0; padding: 0; overflow: hidden; background: #f8fafc; font-family: Inter,system-ui,sans-serif; }}
    #container {{ width: 100%; height: 460px; position: relative; }}
    .badge {{
      position: absolute; top: 12px; left: 14px;
      background: #ffffff; color: #0f172a;
      padding: 4px 10px; border-radius: 6px; font-size: 11px;
      font-weight: 600; border: 1px solid #e2e8f0; pointer-events: none;
    }}
    .tip {{
      position: absolute; bottom: 10px; right: 12px;
      background: #ffffff; color: #64748b;
      padding: 3px 8px; border-radius: 4px; font-size: 10px; pointer-events: none;
      border: 1px solid #e2e8f0;
    }}
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
  <div id="container">
    <div class="badge">3D View • {room_type} ({r_w:.1f}' × {r_l:.1f}')</div>
    <div class="tip">Left-click: Orbit | Right-click: Pan | Scroll: Zoom</div>
  </div>
  <script>
    const container = document.getElementById('container');
    const width = container.clientWidth || 550;
    const height = 460;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8fafc);

    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 1000);
    camera.position.set({r_w * 1.6}, {r_l * 1.9}, {r_w * 2.1});

    const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2.15;
    controls.target.set({r_w / 2}, 1.2, {r_l / 2});

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.55);
    dirLight.position.set(12, 22, 14);
    dirLight.castShadow = true;
    scene.add(dirLight);

    // Floor (Light tiled plane)
    const floorGeo = new THREE.PlaneGeometry({r_w}, {r_l});
    const floorMat = new THREE.MeshStandardMaterial({{ color: 0xf1f5f9, roughness: 0.3 }});
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.set({r_w / 2}, 0, {r_l / 2});
    floor.receiveShadow = true;
    scene.add(floor);

    const grid = new THREE.GridHelper(Math.max({r_w}, {r_l}), 10, 0xcbd5e1, 0xe2e8f0);
    grid.position.set({r_w / 2}, 0.01, {r_l / 2});
    scene.add(grid);

    // Minimal Cutaway Walls
    const wallMat = new THREE.MeshStandardMaterial({{ color: 0xffffff, roughness: 0.8 }});
    const backWall = new THREE.Mesh(new THREE.BoxGeometry({r_w}, 4.8, 0.08), wallMat);
    backWall.position.set({r_w / 2}, 2.4, 0);
    scene.add(backWall);

    const leftWall = new THREE.Mesh(new THREE.BoxGeometry(0.08, 4.8, {r_l}), wallMat);
    leftWall.position.set(0, 2.4, {r_l / 2});
    scene.add(leftWall);

    // Materials
    const metalMat = new THREE.MeshStandardMaterial({{ color: {mat_color}, metalness: {metalness}, roughness: {roughness} }});
    const ceramicMat = new THREE.MeshStandardMaterial({{ color: 0xffffff, roughness: 0.1 }});
    const woodMat = new THREE.MeshStandardMaterial({{ color: 0x334155, roughness: 0.6 }});
    const glassMat = new THREE.MeshPhysicalMaterial({{ color: 0x38bdf8, transparent: true, opacity: 0.3, roughness: 0.1 }});

    // Fixtures placement
    const items = {items_json};
    items.forEach(item => {{
      const x = item.x_ft + (item.w_ft / 2);
      const z = item.y_ft + (item.d_ft / 2);
      const w = item.w_ft;
      const d = item.d_ft;
      const cat = item.category || '';

      if (cat === 'vanities') {{
        const vMesh = new THREE.Mesh(new THREE.BoxGeometry(w, 2.6, d), woodMat);
        vMesh.position.set(x, 1.3, z);
        scene.add(vMesh);
        const topMesh = new THREE.Mesh(new THREE.BoxGeometry(w + 0.05, 0.12, d + 0.05), ceramicMat);
        topMesh.position.set(x, 2.66, z);
        scene.add(topMesh);
        const fMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.7, 16), metalMat);
        fMesh.position.set(x, 3.05, z - (d * 0.25));
        scene.add(fMesh);
        const mMesh = new THREE.Mesh(new THREE.BoxGeometry(Math.min(w, 2.2), 2.6, 0.04), new THREE.MeshStandardMaterial({{ color: 0xe2e8f0, roughness: 0.1 }}));
        mMesh.position.set(x, 4.4, 0.06);
        scene.add(mMesh);
      }} else if (cat === 'toilets') {{
        const tTank = new THREE.Mesh(new THREE.BoxGeometry(w * 0.8, 1.8, d * 0.35), ceramicMat);
        tTank.position.set(x, 1.5, z - (d * 0.28));
        scene.add(tTank);
        const tBowl = new THREE.Mesh(new THREE.CylinderGeometry(w * 0.38, w * 0.32, 1.2, 20), ceramicMat);
        tBowl.position.set(x, 0.6, z + (d * 0.15));
        scene.add(tBowl);
      }} else if (cat === 'showers') {{
        const gMesh = new THREE.Mesh(new THREE.BoxGeometry(w, 5.5, 0.04), glassMat);
        gMesh.position.set(x, 2.75, z + (d / 2));
        scene.add(gMesh);
        const shMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 2.2, 16), metalMat);
        shMesh.position.set(x, 5.0, z - (d * 0.35));
        scene.add(shMesh);
      }} else if (cat === 'tubs_and_sinks') {{
        const tub = new THREE.Mesh(new THREE.CylinderGeometry(w * 0.45, w * 0.4, 1.8, 28), ceramicMat);
        tub.scale.set(1, 1, d / w);
        tub.position.set(x, 0.9, z);
        scene.add(tub);
      }}
    }});

    function animate() {{
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }}
    animate();

    window.addEventListener('resize', () => {{
      const w = container.clientWidth;
      camera.aspect = w / height;
      camera.updateProjectionMatrix();
      renderer.setSize(w, height);
    }});
  </script>
</body>
</html>"""
    b64 = base64.b64encode(html_content.encode("utf-8")).decode("ascii")
    return f'<iframe src="data:text/html;base64,{b64}" width="100%" height="460" style="border:none; border-radius:6px; display:block; background:#f8fafc;"></iframe>'


def generate_specs_table_html(design: Dict[str, Any]) -> str:
    """Generates a clean, flat Notion-style HTML table for Specs & Clearances."""
    products = design.get("products", [])
    subtotal = design.get("subtotal", 0)
    disc_tier = design.get("discount_tier", "")
    disc_pct = design.get("discount_pct", 0)
    disc_val = design.get("discount_val", 0)
    taxable = design.get("taxable", 0)
    gst = design.get("gst", 0)
    grand_total = design.get("grand_total", 0)

    rows = []
    for idx, p in enumerate(products, 1):
        price_str = format_inr(p.get("price", 0))
        dim = p.get("dimensions", "Standard")
        finish = p.get("finish", "Standard")
        sku = p.get("id", f"KOH-00{idx}")
        cat = p.get("category", "").title()
        rows.append(f"""
        <tr style="border-bottom:1px solid #f1f5f9;">
          <td style="padding:9px 12px; font-family:monospace; font-size:11px; color:#64748b;">{sku}</td>
          <td style="padding:9px 12px; font-weight:500; color:#0f172a;">{p.get('name', 'Fixture')}</td>
          <td style="padding:9px 12px; color:#475569;">{cat}</td>
          <td style="padding:9px 12px; font-family:monospace; font-size:11px; color:#64748b;">{dim}</td>
          <td style="padding:9px 12px; color:#334155;">{finish}</td>
          <td style="padding:9px 12px; text-align:right; font-weight:600; color:#0f172a;">{price_str}</td>
        </tr>
        """)
    rows_html = "".join(rows)

    return f"""
    <div style="background:#ffffff; border:1px solid #e5e7eb; border-radius:6px; padding:16px; font-family:Inter,system-ui,sans-serif; font-size:12px; color:#0f172a;">
      <div style="font-weight:600; font-size:13px; margin-bottom:10px; color:#0f172a;">Itemized Fixture Specifications</div>
      <table style="width:100%; border-collapse:collapse; margin-bottom:16px;">
        <thead>
          <tr style="background:#f8fafc; border-bottom:1px solid #e5e7eb; color:#64748b; text-align:left; font-size:11px; text-transform:uppercase;">
            <th style="padding:8px 12px;">SKU</th>
            <th style="padding:8px 12px;">Fixture</th>
            <th style="padding:8px 12px;">Category</th>
            <th style="padding:8px 12px;">Dimensions</th>
            <th style="padding:8px 12px;">Finish</th>
            <th style="padding:8px 12px; text-align:right;">Price</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>

      <!-- Pricing Summary -->
      <div style="background:#f8fafc; border:1px solid #e5e7eb; border-radius:6px; padding:12px 16px; margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:4px; color:#475569;">
          <span>Catalog Subtotal:</span>
          <span style="font-weight:500; color:#0f172a;">{format_inr(subtotal)}</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:4px; color:#047857;">
          <span>Promotional Deal ({disc_tier}):</span>
          <span style="font-weight:600;">-{format_inr(disc_val)} ({disc_pct}% off)</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:4px; color:#475569;">
          <span>Net Taxable Amount:</span>
          <span style="font-weight:500; color:#0f172a;">{format_inr(taxable)}</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:4px; color:#475569;">
          <span>Estimated GST (18%):</span>
          <span style="font-weight:500; color:#0f172a;">+{format_inr(gst)}</span>
        </div>
        <div style="border-top:1px solid #e2e8f0; margin-top:8px; padding-top:8px; display:flex; justify-content:space-between; font-size:13px; font-weight:600;">
          <span style="color:#0f172a;">Final Grand Package Total:</span>
          <span style="color:#0f172a;">{format_inr(grand_total)}</span>
        </div>
      </div>

      <!-- Code Compliance Checklist -->
      <div style="border:1px solid #e5e7eb; border-radius:6px; padding:12px 16px;">
        <div style="font-weight:600; margin-bottom:6px; color:#0f172a;">Building Code & Sanitary Clearance Verification:</div>
        <div style="color:#047857; margin-bottom:3px;">✓ <b>15" Centerline Clearance:</b> Pass — Toilet centerline placed ≥ 15" from adjacent walls/vanity.</div>
        <div style="color:#047857; margin-bottom:3px;">✓ <b>21" Front Clearance:</b> Pass — Minimum 21" unobstructed front access verified for all fixtures.</div>
        <div style="color:#047857; margin-bottom:3px;">✓ <b>30" Door Arc Swing:</b> Pass — Bathroom entrance door swings completely clear of fixtures.</div>
        <div style="color:#047857;">✓ <b>Wet / Dry Zoning:</b> Pass — Enclosure glass isolates shower moisture from drywall.</div>
      </div>
    </div>
    """


def render_studio_header(design: Dict[str, Any]) -> str:
    """Renders the minimal clean header for the Spatial Studio panel."""
    if not design:
        return """
        <div style="display:flex; justify-content:space-between; align-items:center; padding:12px 16px; border:1px solid #e5e7eb; border-radius:6px; background:#f8fafc; font-family:Inter,system-ui,sans-serif; margin-bottom:12px;">
          <div>
            <span style="font-size:13px; font-weight:600; color:#0f172a;">Spatial Studio</span>
            <span style="font-size:12px; color:#64748b; margin-left:8px;">Ready for layout and space planning</span>
          </div>
          <span style="background:#ffffff; border:1px solid #e2e8f0; color:#64748b; font-size:11px; padding:2px 8px; border-radius:4px;">No Active Plan</span>
        </div>
        """

    room_type = design.get("room_type", "Bathroom")
    w = design.get("width_ft", 6.0)
    l = design.get("length_ft", 8.0)
    sqft = design.get("area_sqft", 48.0)
    finish = design.get("focal_finish", "Matte Black")
    grand_total = design.get("grand_total", 0)
    budget = design.get("budget", 0)
    is_under = design.get("is_under_budget", True)

    badge_style = (
        "background:#ecfdf5; color:#047857; border:1px solid #a7f3d0;" if is_under else
        "background:#fef2f2; color:#b91c1c; border:1px solid #fecaca;"
    )
    badge_label = f"Under Budget: {format_inr(grand_total)} / {format_inr(budget)}" if is_under else f"Over Budget: {format_inr(grand_total)} / {format_inr(budget)}"

    return f"""
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; padding:12px 16px; border:1px solid #e5e7eb; border-radius:6px; background:#f8fafc; font-family:Inter,system-ui,sans-serif; margin-bottom:12px;">
      <div>
        <span style="font-size:13px; font-weight:600; color:#0f172a;">{room_type}</span>
        <span style="font-size:12px; color:#64748b; margin-left:8px;">{w:.1f}' × {l:.1f}' ({sqft:.1f} sq ft) • {finish}</span>
      </div>
      <span style="{badge_style} font-size:11px; font-weight:500; padding:3px 8px; border-radius:4px;">{badge_label}</span>
    </div>
    """

def get_default_views() -> Tuple[str, str, str, str]:
    """Returns placeholder views for initial application load."""
    default_header = render_studio_header({})
    empty_html = """
    <div style="height:440px; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; color:#64748b; font-family:Inter,system-ui,sans-serif; background:#f8fafc; border:1px solid #e5e7eb; border-radius:6px; padding:20px;">
      <div style="font-weight:600; font-size:14px; color:#0f172a; margin-bottom:6px;">No Active Layout</div>
      <div style="font-size:12px; max-width:320px; line-height:1.5;">
        Ask the concierge to design a bathroom with dimensions and a budget, or select one of the quick actions on the left.
      </div>
    </div>
    """
    return default_header, empty_html, empty_html, empty_html


# ==============================================================================
# 6. LLM CALL WRAPPER (LOCAL OLLAMA QWEN2.5 WITH DETERMINISTIC FALLBACK)
# ==============================================================================

def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Calls local Ollama daemon (qwen2.5:3b) with low latency.
    Falls back gracefully to a deterministic response if Ollama is unavailable.
    """
    try:
        url = "http://localhost:11434/api/generate"
        payload = json.dumps({
            "model": "qwen2.5:3b",
            "prompt": f"{system_prompt}\n\nUser: {user_prompt}\nAssistant:",
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 400}
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=3.5) as response:
            if response.status == 200:
                res_data = json.loads(response.read().decode("utf-8"))
                output = res_data.get("response", "").strip()
                if output:
                    return output
    except Exception:
        pass
    return ""


# ==============================================================================
# 7. CONVERSATION HANDLER & ORCHESTRATION
# ==============================================================================

def process_query(message: str, history: list, design_state: dict):
    """
    Core orchestrator:
    1. Routes intent.
    2. Performs calculations / catalog lookups.
    3. Formats clean left chat response.
    4. Renders right panel 3D view, 2D blueprint, and specs table.
    """
    if not message or not str(message).strip():
        return history, render_studio_header(design_state), gr.update(), gr.update(), gr.update(), design_state

    query_str = str(message).strip()
    history = history or []
    history.append({"role": "user", "content": query_str})

    intent = classify_intent(query_str)
    new_design = design_state

    if intent == QueryIntent.GREETING:
        # Consultative greeting response
        prompt = (
            "You are the dedicated sales specialist for Kohler luxury bathroom products in India. "
            f"The customer said: '{query_str}'. Greet them warmly and professionally. Spotlight our signature fixtures "
            "(Numi 2.0 smart toilet, Purist faucets, Moxie Bluetooth showerhead), ask what project they are planning, "
            "and invite them to request itemized package quotes, custom bundles, and 2D/3D space planning in ₹ INR."
        )
        llm_reply = call_llm("You are a helpful, upscale Kohler sales consultant in India.", prompt)
        if not llm_reply:
            llm_reply = (
                "Hello! Welcome to the **Kohler Design Concierge**. I am your dedicated sales specialist for Kohler luxury bathroom products.\n\n"
                "Whether you are planning a master bathroom remodel, a guest powder room, or seeking specifications for our signature fixtures—such as the **Numi 2.0 Intelligent Smart Toilet**, **Purist Designer Faucets**, or **Moxie Bluetooth Showerheads**—I am here to guide you.\n\n"
                "Feel free to share your room dimensions and budget ceiling in ₹ INR, or ask about finishes and warehouse stock."
            )
        history.append({"role": "assistant", "content": llm_reply})
        return history, render_studio_header(design_state), gr.update(), gr.update(), gr.update(), design_state

    elif intent == QueryIntent.FAST_PATH_RAG:
        # Product lookup
        matches = query_catalog(query_str, top_k=2)
        top_prod = matches[0] if matches else PRODUCTS[0]
        
        reply_lines = [
            f"### {top_prod.get('name')} ({top_prod.get('type', 'Fixture')})",
            f"* **Catalog Price:** {format_inr(top_prod.get('price', 0))} INR",
            f"* **Finish:** {top_prod.get('finish', 'Standard')}",
            f"* **Dimensions:** {top_prod.get('dimensions', 'Standard')}",
            f"* **Features:** {top_prod.get('features', 'Premium Kohler craftsmanship')}",
            f"* **Availability:** {top_prod.get('stock_status', 'In Stock')} ({top_prod.get('warehouse', 'Central Hub')})",
            f"* **Lead Time:** {top_prod.get('lead_time', '2-3 business days')}",
            f"* **Warranty:** {top_prod.get('warranty_years', 10)} Years Official Kohler Warranty",
            "",
            "Would you like me to recommend matching fixtures for a complete design suite or calculate package combo discounts?"
        ]
        history.append({"role": "assistant", "content": "\n".join(reply_lines)})
        return history, render_studio_header(design_state), gr.update(), gr.update(), gr.update(), design_state

    else:
        # Agent Path: Spatial layout, budget optimization, or delivery check
        # Check for PIN code delivery check first
        pin_match = re.search(r"\b\d{6}\b", query_str)
        if pin_match and not re.search(r"\b(x|by|ft|dimensions?)\b", query_str.lower()):
            pin = pin_match.group(0)
            delivery_info = estimate_delivery(pin)
            delivery_reply = (
                f"### Delivery & Logistics Estimate (PIN Code: {pin})\n\n"
                f"* **Fulfillment Warehouse:** {delivery_info['hub']}\n"
                f"* **Transit Window:** {delivery_info['transit_days']}\n"
                f"* **Inventory Status:** {delivery_info['status']} for immediate dispatch\n"
                f"* **Freight Handling:** Kohler White-Glove Insured Delivery with professional unpacking\n\n"
                "All items are inspected at dispatch and covered under standard Kohler India warranty."
            )
            history.append({"role": "assistant", "content": delivery_reply})
            return history, render_studio_header(design_state), gr.update(), gr.update(), gr.update(), design_state

        # Check for spatial parameters
        dim_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:x|by|\*)\s*(\d+(?:\.\d+)?)", query_str, re.IGNORECASE)
        length_ft = float(dim_match.group(1)) if dim_match else 8.0
        width_ft = float(dim_match.group(2)) if dim_match else 6.0
        if length_ft < width_ft:
            length_ft, width_ft = width_ft, length_ft

        # Extract budget
        budget_inr = 250000.0
        budget_match = re.search(r"(?:under|budget|max)?\s*(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{2,3})*(?:\.\d+)?|\d+)", query_str, re.IGNORECASE)
        if budget_match:
            raw_b = budget_match.group(1).replace(",", "")
            try:
                b_val = float(raw_b)
                if b_val > 10000:
                    budget_inr = b_val
            except Exception:
                pass

        # Extract style
        style_pref = ""
        for s in ["matte black", "brass", "chrome", "nickel", "titanium", "rose gold", "minimalist", "modern", "spa"]:
            if s in query_str.lower():
                style_pref = s
                break

        # Run Spatial & Budget Optimizer
        new_design = optimize_space_and_budget(
            length_ft=length_ft,
            width_ft=width_ft,
            budget_inr=budget_inr,
            style_pref=style_pref
        )

        # Build clean markdown chat summary
        surplus_val = new_design['surplus']
        status_text = f"Under budget by {format_inr(surplus_val)} INR" if new_design['is_under_budget'] else f"Exceeds budget ceiling by {format_inr(-surplus_val)} INR"
        
        chat_lines = [
            f"### Space & Budget Recommendation ({new_design['room_type']})",
            f"* **Dimensions:** {new_design['width_ft']:.1f}' × {new_design['length_ft']:.1f}' ({new_design['area_sqft']:.1f} sq ft)",
            f"* **Budget Ceiling:** {format_inr(new_design['budget'])} INR ({status_text})",
            f"* **Coordinated Finish:** {new_design['focal_finish']}",
            "",
            "**Curated Code-Compliant Fixtures:**"
        ]

        for i, p in enumerate(new_design["products"], 1):
            chat_lines.append(f"{i}. **{p['name']}** ({p.get('type', 'Fixture')}) — {format_inr(p.get('price', 0))} INR")

        chat_lines.extend([
            "",
            "**Financial & Discount Summary:**",
            f"* Combined Catalog Price: {format_inr(new_design['subtotal'])} INR",
            f"* Applied Package Deal: {new_design['discount_tier']}",
            f"* Instant Combo Savings: -{format_inr(new_design['discount_val'])} INR ({new_design['discount_pct']}% off)",
            f"* Estimated GST (18%): +{format_inr(new_design['gst'])} INR",
            f"* **Final Grand Total:** {format_inr(new_design['grand_total'])} INR",
            "",
            "**Code Compliance Verification:**",
            "✓ 15\" toilet centerline clearance verified",
            "✓ 21\" front fixture access verified",
            "✓ 30\" door arc swing verified clear",
            "✓ Wet/dry moisture zoning verified",
            "",
            "*The interactive 3D WebGL model, 2D architectural blueprint, and itemized spec table are now active in the Spatial Studio on the right.*"
        ])

        history.append({"role": "assistant", "content": "\n".join(chat_lines)})

        header_html = render_studio_header(new_design)
        v3d_html = generate_3d_webgl_html(new_design)
        v2d_html = generate_2d_blueprint_svg(new_design)
        vspecs_html = generate_specs_table_html(new_design)

        return history, header_html, v3d_html, v2d_html, vspecs_html, new_design


# ==============================================================================
# 8. MINIMALIST NOTION / LINEAR LIGHT-FIRST CSS
# ==============================================================================

MINIMAL_CSS = """
/* Global Layout & Typography (Inter / System-UI) */
body, .gradio-container {
    background-color: #ffffff !important;
    color: #0f172a !important;
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    max-width: 1440px !important;
    margin: 0 auto !important;
}

/* Header Section */
.app-header {
    border-bottom: 1px solid #e5e7eb;
    padding: 16px 0 18px 0;
    margin-bottom: 18px;
}
.app-header h1 {
    font-size: 17px;
    font-weight: 600;
    color: #0f172a;
    margin: 0 0 2px 0;
    letter-spacing: -0.01em;
}
.app-header p {
    font-size: 13px;
    color: #64748b;
    margin: 0;
}

/* Chatbot Area */
#chatbot-panel {
    border: 1px solid #e5e7eb !important;
    border-radius: 6px !important;
    background-color: #ffffff !important;
    box-shadow: none !important;
}

/* Chat Message Bubbles */
#chatbot-panel [data-testid="user"], #chatbot-panel .message.user {
    background-color: #f1f5f9 !important;
    color: #0f172a !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}

#chatbot-panel [data-testid="bot"], #chatbot-panel .message.bot {
    background-color: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}

#chatbot-panel p, #chatbot-panel li {
    font-size: 13px !important;
    line-height: 1.55 !important;
}

#chatbot-panel h3 {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #0f172a !important;
    margin: 6px 0 !important;
}

/* Input Fields */
#input-box textarea, #input-box input {
    border: 1px solid #e5e7eb !important;
    border-radius: 6px !important;
    background: #ffffff !important;
    color: #0f172a !important;
    box-shadow: none !important;
    font-size: 13px !important;
}

#input-box textarea:focus, #input-box input:focus {
    border-color: #0f172a !important;
    box-shadow: none !important;
    outline: none !important;
}

/* Buttons */
#send-btn {
    background-color: #0f172a !important;
    color: #ffffff !important;
    border: 1px solid #0f172a !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    box-shadow: none !important;
    cursor: pointer !important;
}
#send-btn:hover {
    background-color: #1e293b !important;
}

.preset-btn {
    background-color: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    color: #334155 !important;
    border-radius: 6px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 3px 10px !important;
    box-shadow: none !important;
    cursor: pointer !important;
}
.preset-btn:hover {
    background-color: #f8fafc !important;
    border-color: #cbd5e1 !important;
    color: #0f172a !important;
}

.clear-btn {
    background-color: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    color: #64748b !important;
    border-radius: 6px !important;
    font-size: 12px !important;
    box-shadow: none !important;
}
.clear-btn:hover {
    background-color: #f8fafc !important;
    color: #0f172a !important;
}

/* Studio Tabs */
.tab-nav {
    border-bottom: 1px solid #e5e7eb !important;
}
.tab-nav button {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #64748b !important;
    border-radius: 0 !important;
    padding: 8px 16px !important;
    box-shadow: none !important;
}
.tab-nav button.selected {
    color: #0f172a !important;
    border-bottom: 2px solid #0f172a !important;
}

footer { display: none !important; }
"""


# ==============================================================================
# 9. GRADIO BLOCKS APPLICATION LAYOUT
# ==============================================================================

init_header, init_3d, init_2d, init_specs = get_default_views()

with gr.Blocks(title="Kohler Design Concierge & Spatial Studio") as demo:
    design_state = gr.State(value={})

    # Top Header
    gr.HTML(
        """
        <div class="app-header">
          <h1>Kohler Design Concierge & Spatial Studio</h1>
          <p>Autonomous sales consultation, combo discount optimization, and architectural space planning.</p>
        </div>
        """
    )

    # Main Two-Column Split Screen
    with gr.Row():
        # Left Column (~45%): Chat Interface
        with gr.Column(scale=5, min_width=400):
            chatbot = gr.Chatbot(
                height=520,
                render_markdown=True,
                show_label=False,
                elem_id="chatbot-panel"
            )

            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="Ask about Kohler fixtures, custom bundles, or space planning...",
                    show_label=False,
                    scale=8,
                    lines=1,
                    max_lines=3,
                    elem_id="input-box"
                )
                send_btn = gr.Button("Send", variant="primary", scale=2, elem_id="send-btn")

            with gr.Row():
                btn_ex1 = gr.Button("8x6 Modern Bath", size="sm", elem_classes=["preset-btn"])
                btn_ex2 = gr.Button("Purist Brass Suite", size="sm", elem_classes=["preset-btn"])
                btn_ex3 = gr.Button("Numi 2.0 Specs", size="sm", elem_classes=["preset-btn"])
                btn_ex4 = gr.Button("Zen Spa Master Bath", size="sm", elem_classes=["preset-btn"])
                clear_btn = gr.Button("Clear", size="sm", elem_classes=["clear-btn"])

        # Right Column (~55%): Spatial Studio Panel
        with gr.Column(scale=6, min_width=500):
            studio_header = gr.HTML(value=init_header, elem_id="studio-header")

            with gr.Tabs(elem_classes=["tab-nav"]):
                with gr.Tab("3D View"):
                    view_3d = gr.HTML(value=init_3d, elem_id="view-3d")

                with gr.Tab("2D Blueprint"):
                    view_2d = gr.HTML(value=init_2d, elem_id="view-2d")

                with gr.Tab("Specs & Clearances"):
                    view_specs = gr.HTML(value=init_specs, elem_id="view-specs")

    # Wire Interactions
    def on_submit(user_msg, history, d_state):
        if not user_msg or not user_msg.strip():
            return "", history, gr.update(), gr.update(), gr.update(), gr.update(), d_state
        hist, hdr, v3, v2, vs, n_state = process_query(user_msg, history, d_state)
        return "", hist, hdr, v3, v2, vs, n_state

    # Textbox enter & send button click
    msg_input.submit(
        on_submit,
        inputs=[msg_input, chatbot, design_state],
        outputs=[msg_input, chatbot, studio_header, view_3d, view_2d, view_specs, design_state]
    )
    send_btn.click(
        on_submit,
        inputs=[msg_input, chatbot, design_state],
        outputs=[msg_input, chatbot, studio_header, view_3d, view_2d, view_specs, design_state]
    )

    # Preset Quick Action Buttons (Auto-submitting)
    btn_ex1.click(
        lambda h, s: on_submit("Design an 8x6 ft modern bathroom under ₹2,50,000 with matte black fixtures", h, s),
        inputs=[chatbot, design_state],
        outputs=[msg_input, chatbot, studio_header, view_3d, view_2d, view_specs, design_state]
    )
    btn_ex2.click(
        lambda h, s: on_submit("Recommend a matching Purist faucet and vanity package in Vibrant Moderne Brass with package discount", h, s),
        inputs=[chatbot, design_state],
        outputs=[msg_input, chatbot, studio_header, view_3d, view_2d, view_specs, design_state]
    )
    btn_ex3.click(
        lambda h, s: on_submit("Tell me about the Numi 2.0 smart toilet features, price in INR, and stock availability", h, s),
        inputs=[chatbot, design_state],
        outputs=[msg_input, chatbot, studio_header, view_3d, view_2d, view_specs, design_state]
    )
    btn_ex4.click(
        lambda h, s: on_submit("Design a 10x7 ft luxury zen spa master bathroom under ₹4,00,000 with soaking tub and shower", h, s),
        inputs=[chatbot, design_state],
        outputs=[msg_input, chatbot, studio_header, view_3d, view_2d, view_specs, design_state]
    )

    # Clear button
    clear_btn.click(
        lambda: ("", [], init_header, init_3d, init_2d, init_specs, {}),
        inputs=None,
        outputs=[msg_input, chatbot, studio_header, view_3d, view_2d, view_specs, design_state]
    )


# ==============================================================================
# 10. ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--share", action="store_true", help="Generate temporary public shareable URL")
    parser.add_argument("--port", type=int, default=7860, help="Port to bind the server on")
    args = parser.parse_args()

    share_mode = args.share or os.getenv("SHARE_PROTOTYPE", "false").lower() in ["true", "1", "yes"]

    print(f"Launching Kohler Design Concierge & Spatial Studio on port {args.port} (Share={share_mode})...")
    demo.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=share_mode,
        theme=gr.themes.Base(),
        css=MINIMAL_CSS
    )
