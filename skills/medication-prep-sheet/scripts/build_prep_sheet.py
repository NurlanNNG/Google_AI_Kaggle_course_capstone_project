#!/usr/bin/env python3
"""
build_prep_sheet.py
-------------------
Deterministic renderer for the medication-prep-sheet skill.

Reads a JSON payload from stdin and prints finished Markdown to stdout, so it
"executes without ever polluting the token window" (Day 3, progressive
disclosure). It performs no network or LLM calls -- pure formatting of data that
already passed MedGuard's guardrails.

Payload shape:
    {
      "patient_label": "Mum",
      "schedule":    { ...output of build_daily_schedule... },
      "interactions":{ ...output of check_medication_list... }
    }
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "prep_sheet_template.md"


def _render_schedule(schedule: dict) -> str:
    slots = (schedule or {}).get("schedule", {})
    if not slots:
        return "_No schedule provided._"
    lines = []
    for time, meds in slots.items():
        names = ", ".join(
            f"{m['name']}" + (f" ({m['notes']})" if m.get("notes") else "")
            for m in meds
        )
        lines.append(f"- **{time}** — {names}")
    return "\n".join(lines)


def _render_interactions(interactions: dict) -> str:
    findings = (interactions or {}).get("interactions", [])
    if not findings:
        return (
            "No interactions were found in the demo knowledge base for this list. "
            "This is not a guarantee of safety — confirm with a pharmacist."
        )
    lines = []
    for f in findings:
        pair = " + ".join(f.get("pair", []))
        sev = str(f.get("severity", "")).upper()
        lines.append(
            f"- **{sev}: {pair}** — {f.get('mechanism', '')} "
            f"_{f.get('advice', '')}_"
        )
    return "\n".join(lines)


def build_sheet(payload: dict) -> str:
    template = TEMPLATE.read_text(encoding="utf-8")
    # Keep the label minimal and non-identifying (privacy-by-design).
    label = str(payload.get("patient_label", "My medications")).strip()[:40] or "My medications"
    return template.format(
        patient_label=label,
        schedule_block=_render_schedule(payload.get("schedule", {})),
        interaction_block=_render_interactions(payload.get("interactions", {})),
    )


def main() -> None:
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}
    sys.stdout.write(build_sheet(payload))


if __name__ == "__main__":
    main()
