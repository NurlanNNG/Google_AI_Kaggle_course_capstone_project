"""
security/guardrails.py
======================
Zero-trust guardrails for MedGuard, implemented as ADK lifecycle callbacks
(Day 4: "Guardrails or Hooks: deterministic code that runs at specific lifecycle
points: before a model call, before a tool call").

Three layers, all deterministic (no LLM in the loop of a safety decision):

  1. before_model_callback  -> screens the USER input before it reaches the model
        * emergency / self-harm detection   -> hand off to human help immediately
        * medical-advice guardrail           -> refuse dosing/diagnosis, defer to pros
        * prompt-injection detection         -> neutralise "ignore previous..." attacks

  2. before_tool_callback   -> screens every TOOL call
        * least-privilege allowlist          -> only approved tools may run
        * argument validation / sanitisation -> reject oversized or malformed args
        * injection scan on tool arguments

The heavy lifting is in small pure functions (screen_user_text, is_tool_allowed,
validate_tool_args) so they can be unit-tested with no API key or ADK runtime
(see tests/test_guardrails.py).
"""

from __future__ import annotations

import re
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import BaseTool, ToolContext
from google.genai import types

# --------------------------------------------------------------------------- #
# Tunable policy
# --------------------------------------------------------------------------- #

# Least-privilege: MedGuard agents may ONLY call tools on this allowlist.
# Anything not listed here is denied by default (default-deny, Day 4).
ALLOWED_TOOLS: frozenset[str] = frozenset(
    {
        "check_drug_pair",
        "check_medication_list",
        "lookup_drug",
        "list_known_drugs",
        "build_daily_schedule",
        "generate_prep_sheet",
        # ADK control tool used for coordinator -> sub-agent hand-off:
        "transfer_to_agent",
    }
)

MAX_ARG_CHARS = 2000  # reject absurdly large tool arguments

# Phrases that indicate a possible emergency. We never diagnose; we route to help.
_EMERGENCY_PATTERNS = [
    r"\bchest pain\b",
    r"\bcan'?t breathe\b",
    r"\btrouble breathing\b",
    r"\boverdose\b",
    r"\btook too many\b",
    r"\bunconscious\b",
    r"\bsuicid",
    r"\bkill myself\b",
    r"\bend my life\b",
]

# Requests MedGuard must NOT answer (it is not a prescriber and not a diagnostician).
_MEDICAL_ADVICE_PATTERNS = [
    (r"\b(should i|can i|do i)\s+(stop|quit|double|increase|decrease|skip)\b", "dosing_change"),
    (r"\b(how much|what dose|how many mg|correct dose)\b", "dosing"),
    (r"\b(do i have|am i having|is this)\b.*\b(cancer|infection|disease|diagnos)", "diagnosis"),
    (r"\bprescrib(e|ed|ing)\b", "prescribing"),
]

# Classic prompt-injection markers (Day 4: "indirect prompt injections").
_INJECTION_PATTERNS = [
    r"ignore (all|any|previous|prior) (instructions|rules)",
    r"disregard (the|your|all) (system|previous|above)",
    r"you are now",
    r"reveal your (system prompt|instructions)",
    r"pretend to be",
    r"</?(system|assistant|user)>",
]


# --------------------------------------------------------------------------- #
# Pure, testable screening functions
# --------------------------------------------------------------------------- #

def _match_any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def screen_user_text(text: str) -> Optional[dict]:
    """
    Inspect a user message and decide whether to block it.

    Returns None when the message is allowed to proceed, or a dict describing the
    block: {"action": "block", "category": ..., "reply": ...}.
    Order matters: emergencies are checked first.
    """
    if not text:
        return None
    lowered = text.lower()

    if _match_any(_EMERGENCY_PATTERNS, lowered):
        return {
            "action": "block",
            "category": "emergency",
            "reply": (
                "This may be an emergency, and MedGuard is not able to help with "
                "urgent medical situations. Please contact your local emergency "
                "number or a poison-control / crisis line right now. If you are in "
                "immediate danger, seek emergency care."
            ),
        }

    for pattern, category in _MEDICAL_ADVICE_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            return {
                "action": "block",
                "category": category,
                "reply": (
                    "MedGuard can flag *known* interactions and help you organise a "
                    "schedule, but it can't tell you whether to change, start, or stop "
                    "a medication, or diagnose a condition. Please bring this question "
                    "to your pharmacist or doctor. I'm happy to prepare a summary of "
                    "your medications for that conversation."
                ),
            }

    if _match_any(_INJECTION_PATTERNS, lowered):
        return {
            "action": "block",
            "category": "prompt_injection",
            "reply": (
                "That request looks like an attempt to change my safety rules, so I "
                "can't follow it. I can still check medication interactions or build a "
                "schedule if you'd like."
            ),
        }

    return None


def is_tool_allowed(tool_name: str) -> bool:
    """Least-privilege check: only allowlisted tools may execute."""
    return tool_name in ALLOWED_TOOLS


def validate_tool_args(args: dict) -> Optional[str]:
    """
    Validate tool arguments. Returns an error string if invalid, else None.

    Guards against oversized payloads and injection markers hidden inside args
    (e.g. a malicious "drug name" carrying instructions).
    """
    for key, value in (args or {}).items():
        flat = value if isinstance(value, str) else str(value)
        if len(flat) > MAX_ARG_CHARS:
            return f"Argument '{key}' is too large."
        if _match_any(_INJECTION_PATTERNS, flat.lower()):
            return f"Argument '{key}' contains a disallowed instruction pattern."
    return None


# --------------------------------------------------------------------------- #
# ADK callback adapters (thin wrappers around the pure functions above)
# --------------------------------------------------------------------------- #

def _text_response(message: str) -> LlmResponse:
    """Build an ADK LlmResponse that short-circuits the model with a safe reply."""
    return LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text=message)])
    )


def before_model_guardrail(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    """
    ADK before_model_callback.

    Reads the latest user turn from the outgoing request and, if a guardrail
    fires, returns a canned LlmResponse -- which makes ADK skip the model call
    entirely (the deterministic guardrail wins over the model).
    """
    last_user_text = ""
    for content in reversed(llm_request.contents or []):
        if content.role == "user" and content.parts:
            last_user_text = " ".join(p.text or "" for p in content.parts)
            break

    verdict = screen_user_text(last_user_text)
    if verdict is not None:
        # Record why we blocked (useful for eval / audit logs).
        callback_context.state["last_guardrail"] = verdict["category"]
        return _text_response(verdict["reply"])
    return None


def before_tool_guardrail(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
) -> Optional[dict]:
    """
    ADK before_tool_callback.

    Enforces the tool allowlist and validates arguments. Returning a dict makes
    ADK use that dict as the tool result WITHOUT executing the real tool.
    """
    if not is_tool_allowed(tool.name):
        return {
            "status": "blocked",
            "reason": f"Tool '{tool.name}' is not on the MedGuard allowlist.",
        }

    error = validate_tool_args(args)
    if error is not None:
        return {"status": "blocked", "reason": error}

    return None  # allow the tool to run
