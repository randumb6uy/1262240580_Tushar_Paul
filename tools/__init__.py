from .catalog import get_catalog_tool
from .calculator import calculator_tool
from .inventory import inventory_tool
from .room_planner import room_planner_tool
from .bundle_optimizer import (
    optimize_bundle,
    format_bundle_markdown,
    AESTHETIC_THEMES,
)

def get_agent_tools(chroma_path: str = "./chroma_db", collection_name: str = "kohler_agent", llm=None):
    """Returns the full suite of agent tools."""
    catalog_tool = get_catalog_tool(chroma_path=chroma_path, collection_name=collection_name, llm=llm)
    return [catalog_tool, calculator_tool, inventory_tool, room_planner_tool]

__all__ = [
    "get_agent_tools",
    "calculator_tool",
    "inventory_tool",
    "get_catalog_tool",
    "room_planner_tool",
    "optimize_bundle",
    "format_bundle_markdown",
    "AESTHETIC_THEMES",
]

