"""Unit tests for the deterministic interaction knowledge base (no API key needed)."""

from mcp_server import interactions_db as db


def test_alias_resolves_brand_to_generic():
    assert db.normalize_drug("Coumadin") == "warfarin"
    assert db.normalize_drug("ADVIL") == "ibuprofen"
    assert db.normalize_drug("  zoloft ") == "sertraline"


def test_unknown_drug_returns_none():
    assert db.normalize_drug("unicorn dust") is None


def test_input_is_sanitised():
    # Markup characters are stripped out entirely.
    cleaned = db._clean("warfarin<script>alert()</script>")
    assert "<" not in cleaned and ">" not in cleaned and "(" not in cleaned
    # And a name carrying injected markup fails CLOSED (does not resolve to a
    # real drug), rather than being silently "recovered" to warfarin.
    assert db.normalize_drug("warfarin<script>alert()</script>") is None
    # Ordinary whitespace/case handling still works.
    assert db.normalize_drug("aspirin\n\n") == "aspirin"


def test_major_pair_detected_both_orders():
    r1 = db.check_pair("warfarin", "aspirin")
    r2 = db.check_pair("aspirin", "warfarin")
    assert r1["status"] == "interaction_found"
    assert r1["severity"] == "major"
    assert r2["severity"] == "major"  # order-independent


def test_unknown_pair_flagged_not_silently_safe():
    r = db.check_pair("warfarin", "unicorn")
    assert r["status"] == "unknown_drug"
    assert "unicorn" in r["unknown"]


def test_no_known_interaction_status():
    r = db.check_pair("metformin", "amlodipine")
    assert r["status"] == "no_known_interaction"


def test_medication_list_orders_by_severity():
    result = db.check_medication_list(
        ["metformin", "amlodipine", "simvastatin", "warfarin", "aspirin"]
    )
    assert result["highest_severity"] == "major"
    severities = [i["severity"] for i in result["interactions"]]
    ranks = [db.SEVERITY_RANK[s] for s in severities]
    assert ranks == sorted(ranks, reverse=True)  # sorted worst-first


def test_disclaimer_always_present():
    assert "pharmacist" in db.check_pair("warfarin", "aspirin")["disclaimer"].lower()
