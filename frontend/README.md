# Kohler Design Studio

Build "Kohler Design Concierge & Spatial Studio" — a split-screen web app: an AI sales chat on the left, an interactive spatial design studio on the right.

DESIGN SYSTEM (strict — no bright/neon colors, no glow effects, no gradients):

- Palette: warm off-white background (#FAFAF8), charcoal text (#1C1C1E), one muted accent — dusty slate blue (#5B7290) — used sparingly for active states, links, and the one primary CTA. Borders in soft gray (#E4E2DD). No pure black, no saturated blue/cyan, no drop shadows beyond a barely-there 1px border + faint ambient shadow (0 1px 3px rgba(0,0,0,0.06)).

- Typography — two-font system:

  - Display/headings: a distinctive serif (e.g. "Fraunces" or "Canela"-style) — used for the app title, section headers, and the studio header. Gives it a boutique, architectural-studio feel rather than a SaaS-dashboard feel.

  - Body/UI: a clean grotesk sans (e.g. "Inter" or "General Sans") for chat text, buttons, labels, tables.

  - Establish a clear scale: serif headers noticeably larger/looser tracking, sans body tight and readable at 14-15px.

- Unique design touch: give the app a quiet "architect's notebook" identity — thin hairline rules instead of boxed cards where possible, a small corner tick-mark or plus (+) motif at card corners instead of shadows, subtle grid-paper texture (very low opacity) behind the 2D blueprint viewport only. Avoid generic rounded-card-with-shadow SaaS look.

- Motion: minimal — fades and 150-200ms ease transitions only, no bounce/spring effects.

LAYOUT:

- Top bar: serif wordmark/title on the left, 3-4 small plain-text status indicators on the right (no colored pill badges — just muted text with a small dot).

- Two-column layout, ~45/55 split, stacking vertically on mobile.

- Left: chat panel — message list (user bubbles: subtle accent-tinted background; AI bubbles: plain surface with hairline border, no bright bubble colors), text input + send button, a row of 4 quick-action chips (outlined, not filled) plus a text-only "Clear" action.

- Right: "Spatial Studio" panel — small header (room type, dimensions, primary finish, budget status as plain text, not a badge), 3 tabs (3D View / 2D Blueprint / Specs & Clearances) styled as underlined text tabs rather than filled pill tabs, and a ~480px viewport area below.

CORE FEATURES TO IMPLEMENT:

1. Chat-driven intent handling: greetings get a short concierge-style reply; single-product questions return a focused product card; design/budget requests trigger the spatial optimizer below.

2. Product catalog: ~60 bathroom fixtures (faucets, vanities, toilets, showers, tubs/sinks) with name, category, price in ₹ INR, finish, dimensions, features, stock status — store as static JSON data, searchable by keyword/category/finish.

3. Aesthetic & combo matcher: group products by style family (Modern Minimalist, Heritage Traditional, Industrial Luxury, Zen Spa, High-Tech Futuristic) and finish family (Brass, Matte Black, Chrome, Nickel, Titanium, Rose Gold); apply tiered bundle discounts — 2 items 10%, 3 items 15%, 4-5 items 18%, 6+ items 22%.

4. Delivery estimator: given a PIN code, look up an estimated delivery window from a small static table (major metros 1-3 days, rest of India 4-6 days).

5. Spatial & budget optimizer (hero feature): given room length/width (ft), budget (₹), and optional style/must-have fixtures — classify the room (≤32 sqft Powder Room, 33-58 Standard Bath, >58 Master Suite), pick a fixture set within budget, and check simple pass/fail clearance rules (15" centerline, 21" front clearance, 30" door swing arc).

6. Studio output:

   - "3D View" tab: a simple Three.js (or react-three-fiber) scene — flat-shaded low-poly room box with basic fixture placeholders, muted material colors matching the palette (no shiny/metallic PBR needed), orbit controls.

   - "2D Blueprint" tab: an SVG top-down floorplan — 1ft grid, dimension callouts, dashed clearance zones, door swing arc — rendered in charcoal/gray linework with the single accent color for clearance zones only.

   - "Specs & Clearances" tab: a plain table (SKU, category, price, discount, GST at 18%, grand total vs. budget) plus a simple checklist (checkmark or x, no colored badges) for the 4 compliance rules.

PRESET QUICK-ACTIONS (auto-submit on click):

1. "8×6 Modern Bath" → "Design an 8x6 ft modern bathroom under ₹2,50,000 with matte black fixtures"

2. "Purist Brass Suite" → "Recommend a matching Purist faucet and vanity package in Vibrant Moderne Brass with package discount"

3. "Numi 2.0 Specs" → "Tell me about the Numi 2.0 smart toilet features, price in INR, and stock availability"

4. "Zen Spa Master Bath" → "Design a 10x7 ft luxury zen spa master bathroom under ₹4,00,000 with soaking tub and shower"

TECH NOTES:

- React + TypeScript + Tailwind + shadcn/ui components, but override shadcn's default theme tokens to match the palette/fonts above rather than using default shadcn styling out of the box.

- Keep chat and product logic client-side/mocked for now (static data + simple matching functions), structured so a real LLM/backend call can be swapped in later.

- Format all prices in ₹ INR with Indian digit grouping (e.g., ₹1,89,999).

Prioritize restraint over decoration everywhere — if a component looks like a default SaaS template, simplify it further.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/71ca0c5b-2cee-486a-81b1-b64af31df715).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
