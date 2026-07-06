"""End-to-end tests for the prep-sheet skill and MCP server tool surface."""

from mcp_server import interactions_db as db
from medguard.tools.prep_sheet_tool import generate_prep_sheet


def _sample_schedule():
    from medguard.tools.schedule_tools import build_daily_schedule

    return build_daily_schedule(
        [
            {"name": "warfarin", "frequency": "once daily", "notes": "same time daily"},
            {"name": "aspirin", "frequency": "once daily"},
        ]
    )


def test_prep_sheet_skill_renders_markdown():
    interactions = db.check_medication_list(["warfarin", "aspirin"])
    out = generate_prep_sheet("Mum", _sample_schedule(), interactions)
    assert out["status"] == "ok"
    md = out["markdown"]
    assert "Medication Prep Sheet — Mum" in md
    assert "MAJOR" in md  # highest-severity finding surfaced and upper-cased
    assert "pharmacist" in md.lower()  # disclaimer present


def test_prep_sheet_handles_no_interactions():
    interactions = db.check_medication_list(["metformin", "amlodipine"])
    out = generate_prep_sheet("My meds", _sample_schedule(), interactions)
    assert "No interactions were found" in out["markdown"]


def test_mcp_server_exposes_expected_tools():
    from mcp_server import server

    names = {t.name for t in server.mcp._tool_manager.list_tools()}
    assert {"check_drug_pair", "check_medication_list", "lookup_drug", "list_known_drugs"} <= names


def test_mcp_tool_functions_work_directly():
    # The MCP tools are thin wrappers over db.*; verify wiring.
    assert db.check_pair("simvastatin", "clarithromycin")["severity"] == "major"
