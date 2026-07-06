"""
config.py
=========
Central, environment-driven configuration. No secrets are hard-coded here; the
Gemini API key is read by ADK from the environment (see .env.example).
"""

from __future__ import annotations

import os
from pathlib import Path

# Repository root (…/medguard). Used to launch the MCP server subprocess with the
# correct working directory regardless of where `adk` is invoked from.
REPO_ROOT = Path(__file__).resolve().parents[1]

# Model is overridable so judges can swap in whatever Gemini flash tier they have.
MODEL = os.environ.get("MEDGUARD_MODEL", "gemini-2.0-flash")

APP_NAME = "medguard"
