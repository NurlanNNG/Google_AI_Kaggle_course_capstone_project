"""
MedGuard MCP Server
===================
A Model Context Protocol (MCP) server that exposes MedGuard's curated
drug-interaction knowledge base as callable tools.

WHY MCP (Day 2 & Day 5):
    MCP is the "one integration, every framework" layer. By packaging the
    interaction knowledge base behind a standard MCP interface, the exact same
    server can be consumed by our ADK agent today, by a different framework
    tomorrow, or by a coding agent during development -- with zero rewrites.

Transport: stdio (the server is launched as a subprocess by the ADK client).

Run standalone for manual testing:
    python -m mcp_server.server
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_server import interactions_db as db

# The server name is what clients see during MCP "discovery".
mcp = FastMCP("medguard-interactions")


@mcp.tool()
def check_drug_pair(drug_a: str, drug_b: str) -> dict:
    """Check two medications for a known interaction.

    Args:
        drug_a: A medication name (brand or generic), e.g. "Coumadin" or "warfarin".
        drug_b: A second medication name to compare against drug_a.

    Returns a structured result including severity, mechanism, and advice, or a
    clear "unknown_drug" / "no_known_interaction" status.
    """
    return db.check_pair(drug_a, drug_b)


@mcp.tool()
def check_medication_list(medications: list[str]) -> dict:
    """Check an entire medication list for interactions between every pair.

    Args:
        medications: A list of medication names (brand or generic).

    Returns all interactions found plus the highest severity, so the caller can
    surface the most important risk first.
    """
    return db.check_medication_list(medications)


@mcp.tool()
def lookup_drug(name: str) -> dict:
    """Look up basic reference info for a single medication.

    Args:
        name: A medication name (brand or generic).

    Returns the canonical name, drug class, common uses, and known aliases, or an
    "unknown" status if the drug is not in the demo knowledge base.
    """
    info = db.get_drug_info(name)
    if info is None:
        return {"status": "unknown", "query": name, "disclaimer": db.DISCLAIMER}
    return {
        "status": "found",
        "canonical": info.canonical,
        "drug_class": info.drug_class,
        "common_uses": info.common_uses,
        "aliases": info.aliases,
        "disclaimer": db.DISCLAIMER,
    }


@mcp.tool()
def list_known_drugs() -> dict:
    """List every medication available in the demo knowledge base."""
    return {"drugs": db.list_known_drugs(), "disclaimer": db.DISCLAIMER}


def main() -> None:
    # stdio transport: the ADK McpToolset spawns this process and speaks MCP
    # over stdin/stdout. No network port is opened (least-privilege by default).
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
