"""
tools/schedule_tools.py
=======================
A deterministic function tool that turns a medication list into a daily schedule.

Like the interaction DB, this is plain Python (no LLM). The agent decides *when*
to call it; the tool guarantees the arithmetic and grouping are always correct.
Exposed to the ADK agent as a FunctionTool simply by passing the function in
`tools=[build_daily_schedule]`.
"""

from __future__ import annotations

# Human-friendly clock times for common daily frequencies.
_FREQUENCY_SLOTS: dict[str, list[str]] = {
    "once daily": ["08:00"],
    "twice daily": ["08:00", "20:00"],
    "three times daily": ["08:00", "14:00", "20:00"],
    "four times daily": ["08:00", "12:00", "16:00", "20:00"],
    "at bedtime": ["22:00"],
    "with breakfast": ["08:00"],
}

_ALIAS = {
    "qd": "once daily",
    "od": "once daily",
    "bid": "twice daily",
    "tid": "three times daily",
    "qid": "four times daily",
    "nightly": "at bedtime",
    "hs": "at bedtime",
}


def _normalise_frequency(freq: str) -> str:
    key = (freq or "").strip().lower()
    key = _ALIAS.get(key, key)
    return key if key in _FREQUENCY_SLOTS else "once daily"


def build_daily_schedule(medications: list[dict]) -> dict:
    """Build a time-of-day medication schedule from a structured list.

    Args:
        medications: A list where each item is a dict with:
            - "name" (str): the medication name
            - "frequency" (str): e.g. "twice daily", "at bedtime", "bid"
            - "notes" (str, optional): e.g. "with food"

    Returns:
        A dict mapping each clock time to the medications due then, plus a flat
        per-medication summary. Times use 24h "HH:MM" format.
    """
    timeline: dict[str, list[dict]] = {}
    summary: list[dict] = []

    for med in medications or []:
        name = str(med.get("name", "")).strip()
        if not name:
            continue
        freq = _normalise_frequency(str(med.get("frequency", "once daily")))
        notes = str(med.get("notes", "")).strip()
        slots = _FREQUENCY_SLOTS[freq]

        summary.append({"name": name, "frequency": freq, "times": slots, "notes": notes})
        for slot in slots:
            timeline.setdefault(slot, []).append({"name": name, "notes": notes})

    ordered = {slot: timeline[slot] for slot in sorted(timeline)}
    return {
        "schedule": ordered,
        "summary": summary,
        "total_doses_per_day": sum(len(v) for v in ordered.values()),
        "disclaimer": (
            "Default times are suggestions for organisation only. Confirm exact "
            "timing (and any 'with food' / spacing rules) with your pharmacist."
        ),
    }
