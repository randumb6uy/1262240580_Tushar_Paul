from llama_index.core.tools import FunctionTool

import re

def calculate_quote(
    item_prices,
    discount_percent: float = 0.0,
    tax_percent: float = 0.0,
) -> str:
    """
    Computes an itemized price quote for product packages or single items in INR (₹).
    
    Args:
        item_prices: List of individual item prices in INR (e.g. [15030.0, 43420.0]) or single float.
        discount_percent: Optional percentage discount to deduct (e.g. 10.0 for 10% off).
        tax_percent: Optional sales tax / GST rate to apply (e.g. 18.0 for 18% GST).
    
    Returns:
        A detailed breakdown of subtotal, discount savings, tax/GST, and final grand total in INR (₹).
    """
    cleaned_prices = []
    if isinstance(item_prices, (int, float)):
        cleaned_prices = [float(item_prices)]
    elif isinstance(item_prices, list):
        for p in item_prices:
            try:
                if isinstance(p, dict):
                    p = p.get("price", p.get("value", 0))
                cleaned_str = str(p).replace("₹", "").replace("$", "").replace("INR", "").replace("Rs.", "").replace("Rs", "").replace(",", "").strip()
                cleaned_prices.append(float(cleaned_str))
            except Exception:
                continue
    elif isinstance(item_prices, str):
        matches = re.findall(r"\d+(?:\.\d+)?", item_prices.replace(",", ""))
        cleaned_prices = [float(m) for m in matches]
    elif isinstance(item_prices, dict):
        val = item_prices.get("value") or item_prices.get("price") or item_prices.get("prices")
        if isinstance(val, list):
            for x in val:
                cleaned_str = str(x).replace("₹", "").replace("$", "").replace("INR", "").replace("Rs.", "").replace("Rs", "").replace(",", "").strip()
                if cleaned_str:
                    cleaned_prices.append(float(cleaned_str))
        elif val:
            cleaned_str = str(val).replace("₹", "").replace("$", "").replace("INR", "").replace("Rs.", "").replace("Rs", "").replace(",", "").strip()
            cleaned_prices = [float(cleaned_str)]

    try:
        discount_percent = float(str(discount_percent).replace("%", "").strip())
    except Exception:
        discount_percent = 0.0

    try:
        tax_percent = float(str(tax_percent).replace("%", "").strip())
    except Exception:
        tax_percent = 0.0

    if not cleaned_prices:
        return "No valid item prices found to compute quote."

    subtotal = sum(cleaned_prices)
    discount_amount = subtotal * (discount_percent / 100.0)
    taxable_amount = subtotal - discount_amount
    tax_amount = taxable_amount * (tax_percent / 100.0)
    grand_total = taxable_amount + tax_amount

    breakdown = [
        f"Item Count: {len(cleaned_prices)}",
        f"Items Sum: ₹{subtotal:,.2f} INR",
        f"Discount ({discount_percent}%): -₹{discount_amount:,.2f}",
        f"Subtotal after Discount: ₹{taxable_amount:,.2f}",
        f"Estimated Tax/GST ({tax_percent}%): +₹{tax_amount:,.2f}",
        f"Final Grand Total: ₹{grand_total:,.2f} INR",
    ]
    return "\n".join(breakdown)

calculator_tool = FunctionTool.from_defaults(
    fn=calculate_quote,
    name="price_and_package_calculator",
    description=(
        "Calculate accurate totals, bundles, multi-product discounts, and taxes in Indian Rupees (₹ INR). "
        "Provide a list of floating-point prices in INR and optional discount/tax percentages."
    ),
)
