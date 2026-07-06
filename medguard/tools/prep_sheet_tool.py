"""
tools/prep_sheet_tool.py
========================
Bridges the `medication-prep-sheet` Agent Skill into the ADK agent as a tool.

This is the "composition" story from Day 3: a skill's deterministic script is
executed out-of-band (its output never bloats the model's context) and the agent
simply receives the finished Markdown. The agent decides *when* a document is
wanted; the skill guarantees *how* it is formatted.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Repo root -> skills/medication-prep-sheet/scripts/build_prep_sheet.py
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SKILL_SCRIPT = _REPO_ROOT / "skills" / "medication-prep-sheet" / "scripts" / "build_prep_sheet.py"


def generate_prep_sheet(patient_label: str, schedule: dict, interactions: dict) -> dict:
    """Generate a printable medication prep sheet (Markdown) via the skill.

    Args:
        patient_label: A short, non-identifying label (e.g. "Mum", "My meds").
        schedule: The output of build_daily_schedule.
        interactions: The output of check_medication_list.

    Returns:
        {"status": "ok", "markdown": <sheet>} on success, or an error status.
    """
    payload = json.dumps(
        {
            "patient_label": patient_label,
            "schedule": schedule,
            "interactions": interactions,
        }
    )
    try:
        # The skill script runs as a subprocess: deterministic, sandboxable, and
        # its (potentially long) output stays out of the model's token window
        # until we hand back exactly the finished document.
        result = subprocess.run(
            [sys.executable, str(_SKILL_SCRIPT)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - defensive
        return {"status": "error", "reason": exc.stderr.strip() or "skill script failed"}
    except subprocess.TimeoutExpired:  # pragma: no cover - defensive
        return {"status": "error", "reason": "prep-sheet generation timed out"}

    return {"status": "ok", "markdown": result.stdout}
