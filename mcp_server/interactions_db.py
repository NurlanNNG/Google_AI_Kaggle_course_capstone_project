"""
interactions_db.py
------------------
Pure, dependency-free logic for the MedGuard drug-interaction knowledge base.

DESIGN NOTE (Day 4 - "agentic engineering"):
    Everything safety-critical lives here as deterministic Python, NOT inside an
    LLM prompt. The MCP server (server.py) and the ADK agents are thin wrappers
    around this module. Because this file has no MCP/LLM/network dependencies, it
    can be unit-tested in full without any API key (see tests/test_interactions_db.py).

This is illustrative demo data, not a medical device. See data/*.json disclaimers.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent / "data"

# Severity ordering used to rank the "worst" interaction in a list.
SEVERITY_RANK = {"minor": 1, "moderate": 2, "major": 3}

DISCLAIMER = (
    "This is an educational demo dataset, not medical advice. "
    "Always confirm with a licensed pharmacist or physician."
)


@dataclass(frozen=True)
class DrugInfo:
    canonical: str
    drug_class: str
    common_uses: list[str]
    aliases: list[str]


@dataclass(frozen=True)
class Interaction:
    drug_a: str
    drug_b: str
    severity: str
    mechanism: str
    advice: str


@lru_cache(maxsize=1)
def _load_raw() -> tuple[dict, dict]:
    """Load and cache the JSON knowledge base (parsed once per process)."""
    drugs = json.loads((DATA_DIR / "drugs.json").read_text(encoding="utf-8"))
    interactions = json.loads((DATA_DIR / "interactions.json").read_text(encoding="utf-8"))
    return drugs, interactions


@lru_cache(maxsize=1)
def _alias_index() -> dict[str, str]:
    """Build a lowercase {alias -> canonical} lookup, including brand names."""
    drugs, _ = _load_raw()
    index: dict[str, str] = {}
    for canonical, info in drugs["drugs"].items():
        index[canonical.lower()] = canonical
        for alias in info.get("aliases", []):
            index[alias.lower()] = canonical
    return index


def _clean(name: str) -> str:
    """
    Normalise a free-text drug name.

    SECURITY (Day 4): agent-facing inputs are untrusted. We strip everything
    except letters/spaces/hyphens so a crafted "drug name" cannot smuggle control
    characters or markup into downstream context. Length is capped to avoid abuse.
    """
    if not isinstance(name, str):
        return ""
    name = name.strip().lower()[:80]
    name = re.sub(r"[^a-z0-9 \-]", "", name)
    return re.sub(r"\s+", " ", name).strip()


def normalize_drug(name: str) -> Optional[str]:
    """Resolve a brand/alias/typo-free name to its canonical form, or None."""
    cleaned = _clean(name)
    if not cleaned:
        return None
    return _alias_index().get(cleaned)


def get_drug_info(name: str) -> Optional[DrugInfo]:
    """Return structured info for a single drug, or None if unknown."""
    canonical = normalize_drug(name)
    if canonical is None:
        return None
    drugs, _ = _load_raw()
    info = drugs["drugs"][canonical]
    return DrugInfo(
        canonical=canonical,
        drug_class=info.get("class", "unknown"),
        common_uses=list(info.get("common_uses", [])),
        aliases=list(info.get("aliases", [])),
    )


def _pair_key(a: str, b: str) -> frozenset[str]:
    return frozenset({a, b})


@lru_cache(maxsize=1)
def _interaction_index() -> dict[frozenset[str], Interaction]:
    """Index interactions by unordered drug pair for O(1) lookup."""
    _, raw = _load_raw()
    index: dict[frozenset[str], Interaction] = {}
    for item in raw["interactions"]:
        inter = Interaction(
            drug_a=item["a"],
            drug_b=item["b"],
            severity=item["severity"],
            mechanism=item["mechanism"],
            advice=item["advice"],
        )
        index[_pair_key(item["a"], item["b"])] = inter
    return index


def check_pair(drug_a: str, drug_b: str) -> dict:
    """
    Check a single pair of drugs for a known interaction.

    Returns a structured result. Unknown drugs are reported explicitly rather
    than silently ignored, so the agent never implies "no interaction" when it
    actually means "not in the demo database".
    """
    canon_a = normalize_drug(drug_a)
    canon_b = normalize_drug(drug_b)

    unknown = [orig for orig, canon in ((drug_a, canon_a), (drug_b, canon_b)) if canon is None]
    if unknown:
        return {
            "status": "unknown_drug",
            "unknown": unknown,
            "message": f"Not found in the demo knowledge base: {', '.join(unknown)}.",
            "disclaimer": DISCLAIMER,
        }

    if canon_a == canon_b:
        return {
            "status": "same_drug",
            "message": f"'{canon_a}' compared with itself; no pair to evaluate.",
            "disclaimer": DISCLAIMER,
        }

    inter = _interaction_index().get(_pair_key(canon_a, canon_b))
    if inter is None:
        return {
            "status": "no_known_interaction",
            "pair": [canon_a, canon_b],
            "message": "No interaction recorded in the demo knowledge base for this pair.",
            "disclaimer": DISCLAIMER,
        }

    return {
        "status": "interaction_found",
        "pair": [canon_a, canon_b],
        "severity": inter.severity,
        "mechanism": inter.mechanism,
        "advice": inter.advice,
        "disclaimer": DISCLAIMER,
    }


def check_medication_list(drugs: list[str]) -> dict:
    """
    Check every unordered pair in a medication list.

    Returns all found interactions plus the single highest-severity finding, so
    the agent can lead with the most important risk instead of burying it.
    """
    canon: list[str] = []
    unknown: list[str] = []
    for d in drugs:
        c = normalize_drug(d)
        (canon if c else unknown).append(c or d)

    # De-duplicate while preserving order.
    seen: set[str] = set()
    unique = [c for c in canon if not (c in seen or seen.add(c))]

    findings: list[dict] = []
    for i in range(len(unique)):
        for j in range(i + 1, len(unique)):
            result = check_pair(unique[i], unique[j])
            if result["status"] == "interaction_found":
                findings.append(result)

    findings.sort(key=lambda r: SEVERITY_RANK.get(r["severity"], 0), reverse=True)

    return {
        "checked": unique,
        "unknown": unknown,
        "interaction_count": len(findings),
        "highest_severity": findings[0]["severity"] if findings else "none",
        "interactions": findings,
        "disclaimer": DISCLAIMER,
    }


def list_known_drugs() -> list[dict]:
    """Return every drug in the demo knowledge base (for discovery/UX)."""
    drugs, _ = _load_raw()
    return [asdict(get_drug_info(name)) for name in drugs["drugs"]]  # type: ignore[arg-type]
