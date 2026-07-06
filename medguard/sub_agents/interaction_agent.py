"""
sub_agents/interaction_agent.py
===============================
The interaction specialist. Its tools come entirely from the MedGuard MCP server,
consumed through ADK's McpToolset over a stdio transport.

This is the Day 2 pattern in practice: the agent doesn't embed drug knowledge; it
discovers and calls tools exposed by a standalone MCP server. Swap the server and
the agent is unchanged.
"""

from __future__ import annotations

import sys

from google.adk.agents import LlmAgent
from google.adk.tools import McpToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from mcp import StdioServerParameters

from medguard import prompts
from medguard.config import MODEL, REPO_ROOT
from medguard.security.guardrails import before_model_guardrail, before_tool_guardrail

# Launch the MedGuard MCP server as a subprocess and expose its tools.
# tool_filter is an extra least-privilege boundary: even if the server later adds
# tools, this agent only ever sees the four it is meant to use.
_medguard_mcp = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_server.server"],
            cwd=str(REPO_ROOT),
        )
    ),
    tool_filter=[
        "check_drug_pair",
        "check_medication_list",
        "lookup_drug",
        "list_known_drugs",
    ],
)

interaction_agent = LlmAgent(
    name="interaction_agent",
    model=MODEL,
    description="Checks medications for known interactions using the MedGuard MCP server.",
    instruction=prompts.INTERACTION_INSTRUCTION,
    tools=[_medguard_mcp],
    # Guardrails run on this sub-agent too, so tool calls made after a hand-off
    # are still screened (defence in depth).
    before_model_callback=before_model_guardrail,
    before_tool_callback=before_tool_guardrail,
)
