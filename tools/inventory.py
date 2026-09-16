from llama_index.core.tools import FunctionTool

def check_product_stock_and_delivery(product_model_or_name: str, zip_code: str = "") -> str:
    """
    Checks real-time warehouse inventory availability and estimated shipping lead times.
    
    Args:
        product_model_or_name: The name or model number of the Kohler product (e.g. 'Purist Faucet', 'Veil').
        zip_code: Optional 5-digit delivery zip code for regional transit time calculation.
    
    Returns:
        Warehouse stock status, quantity category, and estimated delivery timeline.
    """
    name_lower = product_model_or_name.lower()
    
    # Realistic mock inventory rules based on product categories
    if any(k in name_lower for k in ["custom", "tailored", "marble", "cast iron", "artist editions"]):
        status = "Low Stock - Special Handling"
        lead_time = "7 to 10 business days (Freight Delivery)"
    elif any(k in name_lower for k in ["veil", "numi", "smart"]):
        status = "In Stock (Central Distribution Center)"
        lead_time = "3 to 5 business days (Insured Ground Delivery)"
    else:
        status = "In Stock (Ready to Ship)"
        lead_time = "2 to 4 business days (Standard Ground Delivery)"

    destination_info = f" to ZIP {zip_code}" if zip_code else ""
    return (
        f"Inventory Report for '{product_model_or_name}':\n"
        f"- Availability: {status}\n"
        f"- Estimated Shipping Time{destination_info}: {lead_time}\n"
        f"- Return Policy: 30-day hassle-free Kohler guarantee."
    )

inventory_tool = FunctionTool.from_defaults(
    fn=check_product_stock_and_delivery,
    name="inventory_and_delivery_checker",
    description=(
        "Check stock availability, warehouse fulfillment status, and delivery lead times "
        "for Kohler bathroom products by product name/model and optional zip code."
    ),
)
