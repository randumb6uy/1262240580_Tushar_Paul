import glob
import json
import os
import re

def convert():
    products = []
    for filepath in sorted(glob.glob("docs/*.txt")):
        cat_name = os.path.splitext(os.path.basename(filepath))[0]
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 6:
                    type_raw = parts[0]
                    # extract bracket tag e.g. [Faucet]
                    tag_match = re.match(r"^\[(.*?)\]\s*(.*)", type_raw)
                    if tag_match:
                        item_type = tag_match.group(1)
                        name = tag_match.group(2)
                    else:
                        item_type = cat_name
                        name = type_raw

                    price_match = re.search(r"\$([0-9,]+)", parts[1])
                    usd_price = float(price_match.group(1).replace(",", "")) if price_match else 0.0
                    USD_TO_INR_RATE = 83.50
                    raw_inr = usd_price * USD_TO_INR_RATE
                    # Round off to multiple of 1,000 and decrease by 1 (e.g., ₹14,999, ₹34,999)
                    rounded_k = round(raw_inr / 1000.0) * 1000
                    inr_price = int(max(999, rounded_k - 1))

                    prod = {
                        "name": name,
                        "type": item_type,
                        "category": cat_name,
                        "price": inr_price,
                        "usd_price": usd_price,
                        "currency": "INR",
                        "finish": parts[2],
                        "dimensions": parts[3],
                        "features": parts[4],
                        "best_for": parts[5],
                        # Concise search text with primary INR pricing and USD reference
                        "text": f"{name} ({item_type}, {cat_name}) | Price: ₹{inr_price:,.0f} INR (${usd_price:,.0f} USD) | Finish: {parts[2]} | Dimensions: {parts[3]} | Features: {parts[4]} | Best for: {parts[5]}",
                    }
                    products.append(prod)

    print(f"Parsed {len(products)} products.")
    out_path = "docs/products.jsonl"
    with open(out_path, "w", encoding="utf-8") as out:
        for p in products:
            out.write(json.dumps(p, separators=(",", ":"), ensure_ascii=False) + "\n")
    
    print(f"Wrote {out_path} ({os.path.getsize(out_path)} bytes).")

if __name__ == "__main__":
    convert()
