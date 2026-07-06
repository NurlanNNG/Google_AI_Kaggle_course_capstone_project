"""
agent.py
========
MedGuard root agent — the coordinator of a multi-agent system (Day 2).

ADK discovers `root_agent` from this module (e.g. `adk web`, `adk run medguard`,
`adk api_server`). The coordinator owns the conversation and delegates to two
specialists via ADK's built-in agent transfer:

    root_agent (coordinator)
    ├── interaction_agent   (tools via MCP server)
    └── schedule_agent      (deterministic tool + prep-sheet skill)

Security guardrails (Day 4) are attached at every level so both the coordinator's
input screening and each specialist's tool calls are checked.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent

from medguard import prompts
from medguard.config import MODEL
from medguard.security.guardrails import before_model_guardrail, before_tool_guardrail
from medguard.sub_agents.interaction_agent import interaction_agent
from medguard.sub_agents.schedule_agent import schedule_agent

root_agent = LlmAgent(
    name="medguard_coordinator",
    model=MODEL,
    description="Personal medication-safety concierge that coordinates interaction and scheduling specialists.",
    instruction=prompts.COORDINATOR_INSTRUCTION,
    sub_agents=[interaction_agent, schedule_agent],
    # Input screening (emergency / medical-advice / prompt-injection) runs before
    # the model ever sees a user turn; the tool allowlist guards any tool call.
    before_model_callback=before_model_guardrail,
    before_tool_callback=before_tool_guardrail,
)
