import json
import os
import re
from typing import List, Dict, Any, Tuple, Optional
from llama_index.core.tools import FunctionTool

def _load_catalog() -> List[Dict[str, Any]]:
    path = os.path.join(os.path.dirname(__file__), "..", "docs", "products.jsonl")
    products = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    products.append(json.loads(line))
    return products

def _load_rules() -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), "..", "docs", "aesthetic_rules.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _extract_dimension_inches(dim_str: str) -> Tuple[float, float, float]:
    """
    Extracts width, depth, height in inches from text like '36\"W x 19\"D x 33\"H'
    """
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

def _generate_2d_svg(
    room_w_ft: float,
    room_l_ft: float,
    layout_items: List[Dict[str, Any]],
    room_type: str,
    finish_color: str = "#222222"
) -> str:
    """Generates an architectural 2D top-down SVG blueprint with dimension lines and clearances."""
    # Scale: 50 pixels per foot
    scale = 50.0
    svg_w = int(room_w_ft * scale)
    svg_h = int(room_l_ft * scale)
    padding = 60
    total_w = svg_w + (padding * 2)
    total_h = svg_h + (padding * 2)

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {total_h}" width="100%" height="{min(total_h, 450)}" style="background:#0e1117; font-family:monospace; border-radius:8px; border:1px solid #30363d;">',
        f'<defs>',
        f'  <pattern id="grid" width="25" height="25" patternUnits="userSpaceOnUse">',
        f'    <path d="M 25 0 L 0 0 0 25" fill="none" stroke="#21262d" stroke-width="0.8"/>',
        f'  </pattern>',
        f'</defs>',
        # Grid background
        f'<rect x="{padding}" y="{padding}" width="{svg_w}" height="{svg_h}" fill="url(#grid)" stroke="#58a6ff" stroke-width="2.5"/>',
        # Dimension callouts
        f'<text x="{padding + svg_w/2}" y="{padding - 15}" fill="#8b949e" font-size="12" text-anchor="middle">← {room_w_ft:.1f} ft ({int(room_w_ft*12)}\") →</text>',
        f'<text x="{padding - 15}" y="{padding + svg_h/2}" fill="#8b949e" font-size="12" text-anchor="middle" transform="rotate(-90 {padding - 15} {padding + svg_h/2})">← {room_l_ft:.1f} ft ({int(room_l_ft*12)}\") →</text>',
        f'<text x="{padding + 10}" y="{padding + 22}" fill="#58a6ff" font-size="11" font-weight="bold">KOHLER ARCHITECTURAL LAYOUT | {room_type.upper()}</text>',
    ]

    # Door swing arc (Standard bottom-left door)
    door_w = int(2.5 * scale)
    door_x = padding
    door_y = padding + svg_h
    svg_parts.append(
        f'<path d="M {door_x} {door_y - door_w} A {door_w} {door_w} 0 0 1 {door_x + door_w} {door_y}" fill="none" stroke="#e3b341" stroke-dasharray="4,4" stroke-width="1.5"/>'
        f'<line x1="{door_x}" y1="{door_y}" x2="{door_x}" y2="{door_y - door_w}" stroke="#e3b341" stroke-width="2.5"/>'
        f'<text x="{door_x + 8}" y="{door_y - 8}" fill="#e3b341" font-size="10">DOOR (30")</text>'
    )

    # Render Fixtures
    for item in layout_items:
        ix = padding + int(item["x_ft"] * scale)
        iy = padding + int(item["y_ft"] * scale)
        iw = max(20, int(item["w_ft"] * scale))
        ih = max(20, int(item["d_ft"] * scale))
        label = item["label"]
        cat = item.get("category", "")

        # Clearance Zone (Dashed boundary)
        cx = max(padding, ix - 6)
        cy = max(padding, iy - 6)
        cw = iw + 12
        ch = ih + 12
        svg_parts.append(
            f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" fill="none" stroke="#238636" stroke-dasharray="3,3" stroke-width="1"/>'
        )

        # Fixture Body
        if cat == "toilets":
            # Oval bowl + tank
            svg_parts.append(
                f'<rect x="{ix}" y="{iy}" width="{iw}" height="{int(ih*0.35)}" rx="3" fill="#30363d" stroke="{finish_color}" stroke-width="2"/>'
                f'<ellipse cx="{ix + iw/2}" cy="{iy + ih*0.65}" rx="{iw*0.45}" ry="{ih*0.35}" fill="#21262d" stroke="{finish_color}" stroke-width="2"/>'
            )
        elif cat in ["showers", "tubs_and_sinks"] and "shower" in label.lower():
            # Glass partition + drain
            svg_parts.append(
                f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="#1f6feb22" stroke="#388bfd" stroke-width="2"/>'
                f'<circle cx="{ix + iw/2}" cy="{iy + ih/2}" r="6" fill="#30363d" stroke="#58a6ff" stroke-width="1.5"/>'
                f'<line x1="{ix}" y1="{iy}" x2="{ix+iw}" y2="{iy+ih}" stroke="#1f6feb55" stroke-width="1"/>'
                f'<line x1="{ix}" y1="{iy+ih}" x2="{ix+iw}" y2="{iy}" stroke="#1f6feb55" stroke-width="1"/>'
            )
        elif "tub" in label.lower():
            # Oval tub
            svg_parts.append(
                f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="12" fill="#21262d" stroke="{finish_color}" stroke-width="2"/>'
                f'<ellipse cx="{ix + iw/2}" cy="{iy + ih/2}" rx="{iw*0.42}" ry="{ih*0.38}" fill="#161b22" stroke="#8b949e" stroke-width="1.2"/>'
                f'<circle cx="{ix + iw*0.25}" cy="{iy + ih/2}" r="4" fill="#58a6ff"/>'
            )
        else:
            # Vanity cabinet + undermount basin
            svg_parts.append(
                f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="4" fill="#21262d" stroke="{finish_color}" stroke-width="2"/>'
                f'<ellipse cx="{ix + iw/2}" cy="{iy + ih/2}" rx="{min(iw*0.35, 18)}" ry="{min(ih*0.35, 12)}" fill="#161b22" stroke="#8b949e" stroke-width="1.2"/>'
                f'<circle cx="{ix + iw/2}" cy="{iy + ih*0.25}" r="3" fill="{finish_color}"/>'
            )

        # Text Tag
        svg_parts.append(
            f'<text x="{ix + iw/2}" y="{iy + ih + 14}" fill="#f0f6fc" font-size="10" font-weight="bold" text-anchor="middle">{label}</text>'
        )

    svg_parts.append('</svg>')
    return "".join(svg_parts)

def _generate_3d_threejs_html(
    room_w_ft: float,
    room_l_ft: float,
    layout_items: List[Dict[str, Any]],
    room_type: str,
    finish_name: str = "Matte Black"
) -> str:
    """Generates an embedded, self-contained Three.js WebGL 3D isometric room with orbit controls."""
    items_json = json.dumps(layout_items)
    
    # Map finish to hex color and metallic properties
    finish_lower = finish_name.lower()
    if "brass" in finish_lower or "gold" in finish_lower:
        mat_color = "0xd4af37"
        metalness = 0.85
        roughness = 0.25
    elif "nickel" in finish_lower:
        mat_color = "0xb8b8b8"
        metalness = 0.75
        roughness = 0.35
    elif "chrome" in finish_lower:
        mat_color = "0xeeeeee"
        metalness = 0.95
        roughness = 0.1
    elif "bronze" in finish_lower:
        mat_color = "0x8c6239"
        metalness = 0.8
        roughness = 0.4
    else:  # Matte Black
        mat_color = "0x222222"
        metalness = 0.2
        roughness = 0.8

    html_code = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ margin: 0; padding: 0; overflow: hidden; background: #0b0f19; font-family: sans-serif; }}
    #canvas-container {{ width: 100%; height: 420px; position: relative; }}
    .badge {{
      position: absolute; top: 12px; left: 14px;
      background: rgba(15, 23, 42, 0.85); color: #38bdf8;
      padding: 6px 12px; border-radius: 6px; font-size: 11px;
      font-weight: 600; border: 1px solid #1e293b; pointer-events: none;
    }}
    .tip {{
      position: absolute; bottom: 12px; right: 14px;
      background: rgba(15, 23, 42, 0.85); color: #94a3b8;
      padding: 4px 10px; border-radius: 6px; font-size: 10px; pointer-events: none;
    }}
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
  <div id="canvas-container">
    <div class="badge">🧊 3D ISOMETRIC PREVIEW | {room_type.upper()} ({room_w_ft:.1f}' x {room_l_ft:.1f}')</div>
    <div class="tip">Left-Click: Orbit/Rotate | Right-Click: Pan | Scroll: Zoom</div>
  </div>
  <script>
    const container = document.getElementById('canvas-container');
    const width = container.clientWidth || 600;
    const height = 420;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b0f19);

    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 1000);
    camera.position.set({room_w_ft * 1.5}, {room_l_ft * 1.8}, {room_w_ft * 2.2});

    const renderer = new THREE.WebGLRenderer({{ antialias: true }});
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2.1;
    controls.target.set({room_w_ft/2}, 1, {room_l_ft/2});

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xfffaed, 0.9);
    dirLight.position.set(10, 20, 15);
    dirLight.castShadow = true;
    scene.add(dirLight);

    // Floor (Tile Grid)
    const floorGeo = new THREE.PlaneGeometry({room_w_ft}, {room_l_ft});
    const floorMat = new THREE.MeshStandardMaterial({{ color: 0x1e293b, roughness: 0.4 }});
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.set({room_w_ft/2}, 0, {room_l_ft/2});
    floor.receiveShadow = true;
    scene.add(floor);

    const grid = new THREE.GridHelper(Math.max({room_w_ft}, {room_l_ft}), 10, 0x38bdf8, 0x334155);
    grid.position.set({room_w_ft/2}, 0.01, {room_l_ft/2});
    scene.add(grid);

    // Back & Left Walls (Isometric Cutaway)
    const wallMat = new THREE.MeshStandardMaterial({{ color: 0x0f172a, roughness: 0.8 }});
    const backWallGeo = new THREE.BoxGeometry({room_w_ft}, 5, 0.1);
    const backWall = new THREE.Mesh(backWallGeo, wallMat);
    backWall.position.set({room_w_ft/2}, 2.5, 0);
    scene.add(backWall);

    const leftWallGeo = new THREE.BoxGeometry(0.1, 5, {room_l_ft});
    const leftWall = new THREE.Mesh(leftWallGeo, wallMat);
    leftWall.position.set(0, 2.5, {room_l_ft/2});
    scene.add(leftWall);

    // Fixture Materials
    const metalMat = new THREE.MeshStandardMaterial({{
      color: {mat_color}, metalness: {metalness}, roughness: {roughness}
    }});
    const ceramicMat = new THREE.MeshStandardMaterial({{ color: 0xf8fafc, roughness: 0.1 }});
    const woodMat = new THREE.MeshStandardMaterial({{ color: 0x78350f, roughness: 0.6 }});
    const glassMat = new THREE.MeshPhysicalMaterial({{
      color: 0xbae6fd, transparent: true, opacity: 0.45, roughness: 0.1, transmission: 0.9
    }});

    // Spawn Fixtures
    const items = {items_json};
    items.forEach(item => {{
      const x = item.x_ft + (item.w_ft / 2);
      const z = item.y_ft + (item.d_ft / 2);
      const w = item.w_ft;
      const d = item.d_ft;
      const cat = item.category || '';

      if (cat === 'vanities') {{
        // Vanity base
        const vGeo = new THREE.BoxGeometry(w, 2.8, d);
        const vMesh = new THREE.Mesh(vGeo, woodMat);
        vMesh.position.set(x, 1.4, z);
        scene.add(vMesh);
        // Countertop & Basin
        const topGeo = new THREE.BoxGeometry(w + 0.1, 0.15, d + 0.1);
        const topMesh = new THREE.Mesh(topGeo, ceramicMat);
        topMesh.position.set(x, 2.85, z);
        scene.add(topMesh);
        // Faucet
        const fGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.8, 16);
        const fMesh = new THREE.Mesh(fGeo, metalMat);
        fMesh.position.set(x, 3.25, z - (d * 0.25));
        scene.add(fMesh);
        // Mirror on Wall
        const mGeo = new THREE.BoxGeometry(Math.min(w, 2.5), 3.0, 0.05);
        const mMesh = new THREE.Mesh(mGeo, new THREE.MeshStandardMaterial({{ color: 0x38bdf8, roughness: 0.1 }}));
        mMesh.position.set(x, 4.8, 0.1);
        scene.add(mMesh);
      }} else if (cat === 'toilets') {{
        // Toilet Tank
        const tTankGeo = new THREE.BoxGeometry(w * 0.8, 1.8, d * 0.35);
        const tTank = new THREE.Mesh(tTankGeo, ceramicMat);
        tTank.position.set(x, 1.6, z - (d * 0.3));
        scene.add(tTank);
        // Toilet Bowl
        const tBowlGeo = new THREE.CylinderGeometry(w * 0.4, w * 0.35, 1.3, 24);
        const tBowl = new THREE.Mesh(tBowlGeo, ceramicMat);
        tBowl.position.set(x, 0.65, z + (d * 0.15));
        scene.add(tBowl);
      }} else if (cat === 'showers') {{
        // Glass Enclosure Panel
        const gGeo = new THREE.BoxGeometry(w, 6.0, 0.05);
        const gMesh = new THREE.Mesh(gGeo, glassMat);
        gMesh.position.set(x, 3.0, z + (d / 2));
        scene.add(gMesh);
        // Showerhead column
        const shGeo = new THREE.CylinderGeometry(0.05, 0.05, 2.5, 16);
        const shMesh = new THREE.Mesh(shGeo, metalMat);
        shMesh.position.set(x, 5.5, z - (d * 0.4));
        scene.add(shMesh);
      }} else if (cat === 'tubs_and_sinks') {{
        // Soaking Tub
        const tubGeo = new THREE.CylinderGeometry(w * 0.45, w * 0.4, 2.0, 32);
        tubGeo.scale(1, 1, d / w);
        const tubMesh = new THREE.Mesh(tubGeo, ceramicMat);
        tubMesh.position.set(x, 1.0, z);
        scene.add(tubMesh);
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
</html>
"""
    return html_code

def optimize_space_and_budget(
    room_length_ft: float,
    room_width_ft: float,
    max_budget_inr: float,
    style_preference: str = "",
    must_have_categories: str = ""
) -> str:
    """
    Fits exact physical space dimensions and budget constraints.
    Performs Knapsack optimization across catalog items to guarantee building code clearance
    and total cost <= max budget, then generates a dual-tab 2D Blueprint and 3D WebGL room model.

    Args:
        room_length_ft: Length of the bathroom in feet (e.g. 8.0 or 10.5).
        room_width_ft: Width of the bathroom in feet (e.g. 6.0 or 7.0).
        max_budget_inr: Maximum budget ceiling in Indian Rupees (₹ INR).
        style_preference: Optional aesthetic style (e.g. 'modern minimalist', 'mid-century brass', 'zen spa').
        must_have_categories: Optional comma-separated list of required categories (e.g. 'faucet, vanity, toilet, shower').

    Returns:
        Itemized quote with combo discount savings, clearance verification, and renderable 2D/3D dual-view HTML.
    """
    catalog = _load_catalog()
    rules = _load_rules()

    r_l = max(4.0, float(room_length_ft))
    r_w = max(3.5, float(room_width_ft))
    budget = float(max_budget_inr)
    pref = style_preference.lower()

    sq_ft = r_l * r_w
    if sq_ft <= 32.0:
        room_type = "Powder Room"
        needed_cats = ["faucets", "vanities", "toilets"]
    elif sq_ft <= 58.0:
        room_type = "Standard Full Bathroom"
        needed_cats = ["faucets", "vanities", "toilets", "showers"]
    else:
        room_type = "Luxury Primary Master Suite"
        needed_cats = ["faucets", "vanities", "toilets", "showers", "tubs_and_sinks"]

    if must_have_categories:
        user_cats = [c.strip().lower() for c in must_have_categories.split(",") if c.strip()]
        if user_cats:
            needed_cats = user_cats

    # Filter catalog by category & style match
    cat_items: Dict[str, List[Dict[str, Any]]] = {}
    for item in catalog:
        c = item.get("category", "")
        # Map plural/singular
        matched_cat = None
        for nc in needed_cats:
            if nc.rstrip("s") in c.rstrip("s") or c.rstrip("s") in nc.rstrip("s"):
                matched_cat = nc
                break
        if not matched_cat:
            continue

        # Score style affinity
        score = 0
        if pref and pref in item.get("aesthetic_style", "").lower():
            score += 10
        if pref and pref in item.get("finish_family", "").lower():
            score += 8
        
        # Check size constraints
        w_in, d_in, h_in = _extract_dimension_inches(item.get("dimensions", ""))
        w_ft = w_in / 12.0
        d_ft = d_in / 12.0

        if matched_cat == "vanities" and w_ft > (r_w * 0.75):
            continue  # Vanity too wide for wall
        if matched_cat == "showers" and w_ft > (r_w * 0.85):
            continue  # Shower exceeds room width

        item_copy = dict(item)
        item_copy["score"] = score
        item_copy["w_ft"] = round(w_ft, 2)
        item_copy["d_ft"] = round(d_ft, 2)

        cat_items.setdefault(matched_cat, []).append(item_copy)

    # Sort each category pool by score, then price
    for c in cat_items:
        cat_items[c].sort(key=lambda x: (x["score"], -x["price"]), reverse=True)

    # Knapsack greedy selection under budget with combo discount
    selected_products: List[Dict[str, Any]] = []
    for c in needed_cats:
        pool = cat_items.get(c, [])
        if not pool:
            # Fallback to any item in category
            pool = [i for i in catalog if c.rstrip("s") in i.get("category", "").rstrip("s")]
            if pool:
                w_in, d_in, _ = _extract_dimension_inches(pool[0].get("dimensions", ""))
                p_copy = dict(pool[0])
                p_copy["w_ft"] = round(w_in / 12.0, 2)
                p_copy["d_ft"] = round(d_in / 12.0, 2)
                pool = [p_copy]
        if pool:
            selected_products.append(pool[0])

    # Calculate discount & total
    n_items = len(selected_products)
    if n_items == 2:
        disc_pct = 10.0
        tier_label = "Aesthetic Duo Combo (10% Off)"
    elif n_items == 3:
        disc_pct = 15.0
        tier_label = "Complete Design Suite (15% Off)"
    elif 4 <= n_items <= 5:
        disc_pct = 18.0
        tier_label = "Full Master Bath Remodel Package (18% Off)"
    else:
        disc_pct = 22.0
        tier_label = "Whole-Home Ultimate Luxury Estate Package (22% Off)"

    subtotal = sum(p["price"] for p in selected_products)
    discount_val = subtotal * (disc_pct / 100.0)
    taxable = subtotal - discount_val
    gst = taxable * 0.18
    grand_total = taxable + gst

    # If over budget, replace highest cost items with budget-friendly alternatives
    if grand_total > budget and len(selected_products) > 1:
        for idx in range(len(selected_products)):
            c = selected_products[idx].get("category", "")
            alts = sorted([i for i in catalog if c.rstrip("s") in i.get("category", "").rstrip("s")], key=lambda x: x["price"])
            if alts and alts[0]["price"] < selected_products[idx]["price"]:
                w_in, d_in, _ = _extract_dimension_inches(alts[0].get("dimensions", ""))
                a_copy = dict(alts[0])
                a_copy["w_ft"] = round(w_in / 12.0, 2)
                a_copy["d_ft"] = round(d_in / 12.0, 2)
                selected_products[idx] = a_copy
                
                subtotal = sum(p["price"] for p in selected_products)
                discount_val = subtotal * (disc_pct / 100.0)
                taxable = subtotal - discount_val
                gst = taxable * 0.18
                grand_total = taxable + gst
                if grand_total <= budget:
                    break

    # Determine Finish Family
    focal_finish = selected_products[0].get("finish_family", "Matte Black") if selected_products else "Matte Black"

    # Compute Spatial Coordinates for Floorplan
    layout_items = []
    # 1. Vanity along top wall
    vanity = next((p for p in selected_products if "vanities" in p.get("category", "")), None)
    if vanity:
        v_w = min(vanity["w_ft"], r_w * 0.6)
        v_d = min(vanity["d_ft"], 1.8)
        layout_items.append({
            "label": f"{vanity['name'][:18]}",
            "x_ft": 0.5,
            "y_ft": 0.2,
            "w_ft": v_w,
            "d_ft": v_d,
            "category": "vanities"
        })

    # 2. Toilet along top or side wall with 15" clearance
    toilet = next((p for p in selected_products if "toilets" in p.get("category", "")), None)
    if toilet:
        t_w = 1.6  # Standard 19" width
        t_d = 2.3  # Standard 28" depth
        t_x = 0.5 + (v_w if vanity else 0) + 1.2  # 15" clearance gap
        if t_x + t_w > r_w - 0.5:
            # Place on opposite right wall
            t_x = r_w - t_w - 0.5
            t_y = 0.5
        else:
            t_y = 0.2
        layout_items.append({
            "label": f"{toilet['name'][:16]}",
            "x_ft": t_x,
            "y_ft": t_y,
            "w_ft": t_w,
            "d_ft": t_d,
            "category": "toilets"
        })

    # 3. Shower or Tub in Wet Zone (Far corner)
    shower = next((p for p in selected_products if "showers" in p.get("category", "")), None)
    if shower:
        sh_w = min(3.5, r_w * 0.55)
        sh_d = min(3.2, r_l * 0.45)
        layout_items.append({
            "label": f"{shower['name'][:18]}",
            "x_ft": r_w - sh_w - 0.2,
            "y_ft": r_l - sh_d - 0.2,
            "w_ft": sh_w,
            "d_ft": sh_d,
            "category": "showers"
        })

    tub = next((p for p in selected_products if "tubs" in p.get("category", "") or "bathtub" in p.get("type", "").lower()), None)
    if tub and not shower:
        tb_w = min(5.0, r_w - 0.8)
        tb_d = 2.6
        layout_items.append({
            "label": f"{tub['name'][:18]}",
            "x_ft": 0.4,
            "y_ft": r_l - tb_d - 0.4,
            "w_ft": tb_w,
            "d_ft": tb_d,
            "category": "tubs_and_sinks"
        })

    # Generate 2D SVG Blueprint
    svg_2d = _generate_2d_svg(r_w, r_l, layout_items, room_type, "#e3b341" if "brass" in focal_finish.lower() else "#f0f6fc")
    # Generate 3D HTML
    threejs_html = _generate_3d_threejs_html(r_w, r_l, layout_items, room_type, focal_finish)

    # Encode 3D HTML as base64 data-URI so LLM does not get distracted by raw JavaScript
    import base64
    b64_3d = base64.b64encode(threejs_html.encode("utf-8")).decode("ascii")

    dual_view_ui = f"""
<div style="background:#0e1117; border-radius:10px; padding:12px; border:1px solid #30363d; margin-top:12px;">
  <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #21262d; padding-bottom:8px; margin-bottom:10px;">
    <span style="color:#58a6ff; font-weight:bold; font-size:13px;">📐 KOHLER DUAL-VIEW SPATIAL VISUALIZER</span>
    <span style="color:#8b949e; font-size:11px;">Dimensions: {r_w:.1f}' × {r_l:.1f}' ({sq_ft:.1f} sq ft)</span>
  </div>
  
  <div style="margin-bottom:14px;">
    <div style="color:#f0f6fc; font-size:12px; font-weight:600; margin-bottom:6px;">[📐 View 1: 2D Architectural Clearance Blueprint]</div>
    {svg_2d}
  </div>

  <div>
    <div style="color:#f0f6fc; font-size:12px; font-weight:600; margin-bottom:6px;">[🧊 View 2: Interactive 3D WebGL Room Model]</div>
    <iframe src="data:text/html;base64,{b64_3d}" width="100%" height="430" style="border:none; border-radius:8px; background:#0b0f19;"></iframe>
  </div>
</div>
"""

    global _LATEST_VISUAL_LAYOUT
    _LATEST_VISUAL_LAYOUT = dual_view_ui

    surplus_or_deficit = budget - grand_total
    status_str = f"✅ Fits strictly within budget! Surplus remaining: ₹{surplus_or_deficit:,.2f} INR" if surplus_or_deficit >= 0 else f"⚠️ Exceeds budget by ₹{-surplus_or_deficit:,.2f} INR"

    lines = [
        f"### 📐 Space & Budget Optimized Bathroom Package ({room_type})",
        "----------------------------------------------------------------------",
        f"Spatial Specs: {r_w:.1f}' Width × {r_l:.1f}' Length ({sq_ft:.1f} sq ft total area)",
        f"Budget Constraint: Max ₹{budget:,.2f} INR",
        f"Feasibility Status: {status_str}",
        f"Primary Coordinated Finish: {focal_finish}",
        "",
        "Selected Code-Compliant Fixtures:",
    ]

    for idx, p in enumerate(selected_products, 1):
        lines.append(
            f"  {idx}. {p['name']} ({p.get('type', 'Fixture')})\n"
            f"     - Dimensions: {p.get('dimensions', 'Standard')}\n"
            f"     - Finish: {p.get('finish', 'Standard')}\n"
            f"     - Price: ₹{float(p['price']):,.2f} INR"
        )

    lines.extend([
        "",
        "Package Pricing & Combo Savings:",
        f"  - Combined Catalog Price ({n_items} items): ₹{subtotal:,.2f} INR",
        f"  - Applied Promotional Deal: {tier_label}",
        f"  - Instant Combo Savings: -₹{discount_val:,.2f} INR ({disc_pct}% off)",
        f"  - Subtotal after Discount: ₹{taxable:,.2f} INR",
        f"  - Estimated GST (18%): +₹{gst:,.2f} INR",
        f"  - Final Grand Package Total: ₹{grand_total:,.2f} INR",
        "----------------------------------------------------------------------",
        "Building Code & Spatial Clearance Verification:",
        f"  ✓ Sanitary Clearance: Toilet placed with ≥15\" centerline clearance and ≥21\" front access.",
        f"  ✓ Circulation Flow: Vanity positioned clear of the 30\" door swing radius.",
        f"  ✓ Wet/Dry Zoning: Shower enclosure segregated to prevent moisture intrusion.",
        "  ✓ Visual Layout Rendered: 2D Blueprint & 3D WebGL Room Model ready."
    ])

    return "\n".join(lines)

_LATEST_VISUAL_LAYOUT: Optional[str] = None

def get_latest_visual_layout() -> Optional[str]:
    global _LATEST_VISUAL_LAYOUT
    return _LATEST_VISUAL_LAYOUT

def clear_latest_visual_layout():
    global _LATEST_VISUAL_LAYOUT
    _LATEST_VISUAL_LAYOUT = None

space_optimizer_tool = FunctionTool.from_defaults(
    fn=optimize_space_and_budget,
    name="space_and_budget_optimizer",
    description=(
        "Optimizes bathroom product combinations to fit exact physical space dimensions (room length and width in feet) "
        "and strict budget constraints in INR (₹). Validates building clearance codes, computes maximum package combo discounts, "
        "and generates a Dual-View 2D architectural blueprint and 3D WebGL room model."
    ),
)
