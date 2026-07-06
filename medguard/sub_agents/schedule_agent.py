"""
sub_agents/schedule_agent.py
============================
The scheduling specialist. Uses two deterministic tools:
  * build_daily_schedule  -> a pure function tool (tools/schedule_tools.py)
  * generate_prep_sheet   -> bridges the medication-prep-sheet Agent Skill

Passing plain Python functions in `tools=[...]` is all ADK needs to turn them
into callable FunctionTools.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent

from medguard import prompts
from medguard.config import MODEL
from medguard.security.guardrails import before_model_guardrail, before_tool_guardrail
from medguard.tools.prep_sheet_tool import generate_prep_sheet
from medguard.tools.schedule_tools import build_daily_schedule

schedule_agent = LlmAgent(
    name="schedule_agent",
    model=MODEL,
    description="Builds daily medication schedules and printable prep sheets.",
    instruction=prompts.SCHEDULE_INSTRUCTION,
    tools=[build_daily_schedule, generate_prep_sheet],
    before_model_callback=before_model_guardrail,
    before_tool_callback=before_tool_guardrail,
)
