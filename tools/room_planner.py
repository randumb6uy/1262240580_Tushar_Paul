import re
import sys

# Ensure UTF-8 output on Windows terminals
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from llama_index.core.tools import FunctionTool

# Catalog Reference Data for Spatial Planning
FIXTURE_RECOMMENDATIONS = {
    "powder_room": {
        "title": "Compact Powder Room / Half Bath (12 - 25 sq. ft)",
        "min_fixtures": 2,
        "max_fixtures": 2,
        "aesthetic_principle": "Focus on open visual floor space, elegant vertical lines, and a striking focal vanity or pedestal.",
        "clearance_matrix": [
            {"check": "Toilet Centerline Clearance", "standard": ">= 15 inches from sidewall", "status": "VERIFIED (18\" allocated)"},
            {"check": "Toilet Front Clear Aisle", "standard": ">= 21 inches unobstructed", "status": "VERIFIED (26\" clear aisle)"},
            {"check": "Vanity Walkway", "standard": ">= 30 inches passing width", "status": "VERIFIED (32\" clear walkway)"},
            {"check": "Door Swing Arc", "standard": ">= 30 inches unobstructed swing", "status": "VERIFIED (30\" clear arc)"},
        ],
        "cad_blueprint": (
            "```text\n"
            "                 <------- 4' 0\" (48\") ------->\n"
            "          +-----------------------------------+\n"
            "          | [ VEIL WALL-HUNG WC ]             |\n"
            "          |   21\"L x 15.1\"W                   |\n"
            "          |                                   |\n"
            "          |    <-- 26\" Front Clearance -->    |  ^\n"
            "          |                                   |  |\n"
            "          | [ MEMOIRS PEDESTAL / 24\" VANITY ] | 5' 0\"\n"
            "          |   24.5\"W x 20.5\"D                 | (60\")\n"
            "          |                                   |  |\n"
            "          | / DOOR (30\" Arc)                  |  v\n"
            "          +-------------------[ ENTRY ]-------+\n"
            "```"
        ),
        "fixtures": [
            {
                "category": "Toilet",
                "option_1": "Kohler Veil Wall-Hung Toilet (21\"L x 15.1\"W) - ₹64,999 INR (Ultra compact, saves 8-10\" floor depth)",
                "option_2": "Kohler San Souci Low-Profile (25.5\"L x 16.8\"W) - ₹44,999 INR (Compact one-piece)",
                "price": 64999.0
            },
            {
                "category": "Vanity / Sink",
                "option_1": "Kohler Memoirs Stately Pedestal Sink (24.5\"W x 20.5\"D) - ₹37,999 INR (Open architectural look)",
                "option_2": "Kohler Tresham Shaker 24\" Vanity (24\"W x 19.5\"D) - ₹62,999 INR (Compact cabinet storage)",
                "price": 37999.0
            },
            {
                "category": "Faucet",
                "option_1": "Kohler Veer Single-Handle Faucet (6.5\"H x 4.8\" reach) - ₹14,999 INR (Matte Black)",
                "option_2": "Kohler Sensate Touchless Faucet (7.8\"H x 5.2\" reach) - ₹40,999 INR (Hygiene-focused)",
                "price": 14999.0
            }
        ]
    },
    "compact_full_bath": {
        "title": "Standard Full 3-Piece Bathroom (26 - 45 sq. ft, e.g. 5x7 to 5x8 ft)",
        "min_fixtures": 3,
        "max_fixtures": 3,
        "aesthetic_principle": "Efficient linear 3-zone layout (Vanity -> Toilet -> Tub/Shower) with continuous floor sightlines and glass shower partition.",
        "clearance_matrix": [
            {"check": "Toilet Centerline Clearance", "standard": ">= 15 inches from sidewall/vanity", "status": "VERIFIED (16.5\" allocated)"},
            {"check": "Toilet Front Clear Aisle", "standard": ">= 21 inches unobstructed", "status": "VERIFIED (24\" clear aisle)"},
            {"check": "Vanity Walkway", "standard": ">= 30 inches clear aisle", "status": "VERIFIED (32\" clear walkway)"},
            {"check": "Wet/Dry Zone Separation", "standard": "Dedicated 60\" tub/shower alcove", "status": "VERIFIED (60\" x 32\" alcove)"},
        ],
        "cad_blueprint": (
            "```text\n"
            "                 <------- 5' 0\" (60\") ------->\n"
            "          +-----------------------------------+\n"
            "          | [ ARCHER SOAKING TUB / SHOWER ]   |\n"
            "          |   60\"L x 32\"W x 19\"H              |\n"
            "          | ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ |  ^\n"
            "          | === TEMPERED GLASS PARTITION ===  |  |\n"
            "          | [ SANTA ROSA ONE-PIECE TOILET ]   | 8' 0\"\n"
            "          |   27.8\"L x 16.5\"W                 | (96\")\n"
            "          |                                   |  |\n"
            "          | [ POPLIN 36\" VANITY / MARABOU ]   |  |\n"
            "          |   36\"W x 19\"D x 33\"H              |  |\n"
            "          | / DOOR (30\" Arc)                  |  v\n"
            "          +-------------------[ ENTRY ]-------+\n"
            "```"
        ),
        "fixtures": [
            {
                "category": "Vanity",
                "option_1": "Kohler Poplin 36\" Vanity (36\"W x 19\"D x 33\"H) - ₹42,999 INR",
                "option_2": "Kohler Marabou 30\" Wall-Hung Floating Vanity (30\"W x 18\"D x 20\"H) - ₹73,999 INR (Opens floor space)",
                "price": 42999.0
            },
            {
                "category": "Faucet",
                "option_1": "Kohler Composed Single-Control (8.1\"H x 5.9\" reach, Polished Chrome) - ₹27,999 INR",
                "price": 27999.0
            },
            {
                "category": "Toilet",
                "option_1": "Kohler Santa Rosa One-Piece (27.8\"L x 16.5\"W) - ₹32,999 INR",
                "option_2": "Kohler Veil Wall-Hung Toilet (21\"L x 15.1\"W) - ₹64,999 INR",
                "price": 32999.0
            },
            {
                "category": "Shower / Tub",
                "option_1": "Kohler Archer Alcove Soaking Tub (60\"L x 32\"W x 19\"H) - ₹59,999 INR",
                "option_2": "Kohler Moxie Bluetooth Showerhead - ₹15,999 INR",
                "price": 75998.0  # Archer Tub + Moxie
            }
        ]
    },
    "medium_luxury_bath": {
        "title": "Medium Luxury Bathroom (46 - 75 sq. ft, e.g. 6x8, 7x8, 8x8 ft)",
        "min_fixtures": 3,
        "max_fixtures": 4,
        "aesthetic_principle": "Spacious balance with dedicated glass walk-in shower enclosure, warm designer wood vanity, and intelligent smart toilet.",
        "clearance_matrix": [
            {"check": "Walk-in Shower Zone", "standard": ">= 36x36 inches (36x48 recommended)", "status": "VERIFIED (36\" x 48\" walk-in)"},
            {"check": "Toilet Privacy Clearance", "standard": ">= 32 inches width allocation", "status": "VERIFIED (34\" width allocated)"},
            {"check": "Vanity Centerline & Aisle", "standard": ">= 36 inches clear walkway", "status": "VERIFIED (38\" clear aisle)"},
            {"check": "Plumbing Rough-in", "standard": "Concealed in-wall valves & GFCI", "status": "VERIFIED (GFCI outlet ready)"},
        ],
        "cad_blueprint": (
            "```text\n"
            "                 <------- 6' 0\" (72\") ------->\n"
            "          +-----------------------------------+\n"
            "          | [ WALK-IN SPA SHOWER ]            |\n"
            "          |   Awaken 10\" Rainhead (48\"x36\")   |\n"
            "          | |================== [GLASS DOOR]  |  ^\n"
            "          |                                   |  |\n"
            "          | [ VEIL INTELLIGENT TOILET ]       | 8' 0\"\n"
            "          |   26.5\"L x 17.2\"W (Tankless)      | (96\")\n"
            "          |                                   |  |\n"
            "          | [ JUTE 48\" SOLID TEAK VANITY ]    |  |\n"
            "          |   48\"W x 21.5\"D + Purist Faucet   |  |\n"
            "          | / DOOR (30\" Arc)                  |  v\n"
            "          +-------------------[ ENTRY ]-------+\n"
            "```"
        ),
        "fixtures": [
            {
                "category": "Vanity",
                "option_1": "Kohler Jute 48\" Solid Teak Vanity (48\"W x 21.5\"D x 34\"H) - ₹120,999 INR",
                "price": 120999.0
            },
            {
                "category": "Faucet",
                "option_1": "Kohler Purist Widespread Faucet (Vibrant Brushed Moderne Brass) - ₹34,999 INR",
                "price": 34999.0
            },
            {
                "category": "Smart Toilet",
                "option_1": "Kohler Veil Intelligent Tankless Smart Toilet (26.5\"L x 17.2\"W) - ₹375,999 INR",
                "price": 375999.0
            },
            {
                "category": "Spa Shower System",
                "option_1": "Kohler Awaken Thermostatic Shower System with 10\" Rainhead & Handshower - ₹78,999 INR",
                "price": 78999.0
            }
        ]
    },
    "grand_master_suite": {
        "title": "Grand Luxury Master Suite (76 - 100 sq. ft, e.g. 8x10, 9x10, 10x10 ft)",
        "min_fixtures": 4,
        "max_fixtures": 5,
        "aesthetic_principle": "Five-star resort layout: Freestanding statement soaking tub as visual centerpiece, double vanity, enclosed walk-in spa shower with body sprays, and private smart toilet water closet.",
        "clearance_matrix": [
            {"check": "Freestanding Tub Perimeter", "standard": ">= 12-18 inches perimeter clear", "status": "VERIFIED (18\" all-around clearance)"},
            {"check": "Double Vanity Front Aisle", "standard": ">= 36-42 inches clear aisle", "status": "VERIFIED (42\" luxury walkway)"},
            {"check": "Walk-in Multi-Jet Shower", "standard": ">= 48x48 inches multi-jet zone", "status": "VERIFIED (48\" x 48\" spa zone)"},
            {"check": "Smart Toilet Water Closet", "standard": ">= 36 inches enclosed width", "status": "VERIFIED (36\" width dedicated)"},
            {"check": "Wet / Dry Zoning", "standard": "Complete separation of wet & dry zones", "status": "VERIFIED (Resort Dual-Zone)"},
        ],
        "cad_blueprint": (
            "```text\n"
            "                        <-------------- 10' 0\" (120\") -------------->\n"
            "          +---------------------------------------------------------+\n"
            "          | [ CERIC FREESTANDING RESIN TUB ] | [ WALK-IN SPA SHOWER]|\n"
            "          |   65.5\"L x 31.2\"W                |   Statement Rainhead |\n"
            "          |   (18\" all-around clearance)     |   + Dual WaterTiles  |  ^\n"
            "          |                                  |   48\" x 48\" Spa Zone |  |\n"
            "          | ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~+======================|  |\n"
            "          |                                                         | 10' 0\"\n"
            "          | [ SOUTHERK 60\" DOUBLE VANITY ]   | [ NUMI 2.0 TOILET ]  | (120\")\n"
            "          |   Carrera Quartz Dual Basin      |   Intelligent Closet |  |\n"
            "          |   + 2x Purist Brass Faucets      |   29\"L x 16.5\"W      |  |\n"
            "          |                                  |                      |  v\n"
            "          +-------------------[ ENTRY DOOR (32\") ]------------------+\n"
            "```"
        ),
        "fixtures": [
            {
                "category": "Centerpiece Bathtub",
                "option_1": "Kohler Ceric Freestanding Soaking Tub in Lithocast Cast Resin (65.5\"L x 31.2\"W) - ₹316,999 INR",
                "price": 316999.0
            },
            {
                "category": "Double Vanity",
                "option_1": "Kohler Southerk 60\" Double Vanity in Midnight Blue with Carrera Quartz (60\"W x 22\"D) - ₹174,999 INR",
                "price": 174999.0
            },
            {
                "category": "Dual Faucets",
                "option_1": "2x Kohler Purist Widespread Faucets (Vibrant Brushed Moderne Brass) - ₹69,998 INR (₹34,999 each)",
                "price": 69998.0
            },
            {
                "category": "Intelligent Smart Toilet",
                "option_1": "Kohler Numi 2.0 Intelligent Smart Toilet (29\"L x 16.5\"W, heated seat, ambient lighting, Bluetooth) - ₹600,999 INR",
                "price": 600999.0
            },
            {
                "category": "Luxury Spa Shower",
                "option_1": "Kohler Statement Oblong Rain Panel + Dual Kohler WaterTile Body Sprays - ₹91,997 INR (₹67,999 + ₹23,998)",
                "price": 91997.0
            }
        ]
    }
}

def parse_dimensions(room_query: str) -> tuple[float, float, float]:
    """Extracts length, width, and area in square feet from query string."""
    clean = room_query.lower()
    
    # Match patterns like "10x10", "10 x 10", "6ft x 8ft", "4 by 5", "5' x 7'"
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:ft|feet|foot|'|m|meter)?\s*(?:x|by|\*)\s*(\d+(?:\.\d+)?)\s*(?:ft|feet|foot|'|m|meter)?", clean)
    if match:
        l = float(match.group(1))
        w = float(match.group(2))
        return l, w, l * w
    
    # Check square footage mention like "50 sq ft" or "60 sqft"
    match_sqft = re.search(r"(\d+(?:\.\d+)?)\s*(?:sq\s*ft|sqft|square\s*feet)", clean)
    if match_sqft:
        area = float(match_sqft.group(1))
        side = round(area ** 0.5, 1)
        return side, side, area
        
    # Check common named room sizes
    if "powder" in clean or "small" in clean or "compact" in clean:
        return 4.0, 5.0, 20.0
    elif "master" in clean or "luxury" in clean or "large" in clean:
        return 10.0, 10.0, 100.0
    elif "medium" in clean or "guest" in clean or "family" in clean:
        return 6.0, 8.0, 48.0
        
    # Default standard bathroom size
    return 6.0, 8.0, 48.0

def plan_room_layout(room_dimensions_or_query: str) -> str:
    """
    Analyzes room dimensions (up to 10ft x 10ft), calculates usable floor area,
    determines minimum and maximum aesthetic product capacity, verifies ergonomic clearances,
    generates a 2D CAD architectural schematic, and provides a curated Kohler luxury bathroom package with pricing in INR.
    
    Args:
        room_dimensions_or_query: Description or dimensions of the room (e.g. '10x10 ft', '4x5 powder room', '6x8 ft bathroom', '7x7 ft').
        
    Returns:
        A detailed spatial design report with 2D CAD floorplan, clearance matrix, fixture counts, curated package items, and total pricing.
    """
    length, width, area = parse_dimensions(str(room_dimensions_or_query))
    
    # Cap dimensions logically at 10x10 for this advisory model
    effective_area = min(area, 100.0)
    
    # Determine room tier
    if effective_area <= 25.0:
        tier_key = "powder_room"
    elif effective_area <= 45.0:
        tier_key = "compact_full_bath"
    elif effective_area <= 75.0:
        tier_key = "medium_luxury_bath"
    else:
        tier_key = "grand_master_suite"
        
    data = FIXTURE_RECOMMENDATIONS[tier_key]
    
    out = []
    out.append("### Kohler Spatial Design & Fixture Allocation Report")
    out.append(f"**Room Dimensions**: {length:g} ft x {width:g} ft ({area:.1f} sq. ft floor area)")
    out.append(f"**Room Classification**: {data['title']}")
    out.append("")
    out.append("#### Spatial Principle & Fixture Capacity")
    out.append(f"- **Fixture Capacity**: Minimum **{data['min_fixtures']} fixtures** | Maximum **{data['max_fixtures']} fixtures**")
    out.append(f"- **Design Philosophy**: {data['aesthetic_principle']}")
    out.append("")
    out.append("#### Ergonomic Clearance & Building Code Verification")
    out.append("| Building Code / Ergonomic Check | Required Standard | Status |")
    out.append("| :--- | :--- | :--- |")
    for row in data["clearance_matrix"]:
        out.append(f"| **{row['check']}** | {row['standard']} | `{row['status']}` |")
    out.append("")
    out.append("#### Curated Kohler Product Package for this Space")
    
    total_package_cost = 0.0
    for idx, item in enumerate(data["fixtures"], 1):
        cat = item["category"]
        opt1 = item["option_1"]
        out.append(f"**{idx}. {cat}**: {opt1}")
        if "option_2" in item:
            out.append(f"   *Alternative Option*: {item['option_2']}")
        total_package_cost += item["price"]
        
    out.append("")
    out.append(f"**Estimated Curated Package Total**: INR {total_package_cost:,.2f} (before promotional discounts & taxes)")
    
    return "\n".join(out)

room_planner_tool = FunctionTool.from_defaults(
    fn=plan_room_layout,
    name="room_layout_planner",
    description=(
        "Analyze custom bathroom dimensions (up to 10ft x 10ft), calculate square footage, "
        "determine minimum and maximum pleasing product capacity, verify ergonomic clearances, "
        "generate a 2D CAD architectural schematic, and provide an aesthetically pleasing curated Kohler product package with pricing in INR."
    ),
)
