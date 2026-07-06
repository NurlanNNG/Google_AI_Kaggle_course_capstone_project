"""Unit tests for the deterministic schedule builder."""

from medguard.tools.schedule_tools import build_daily_schedule


def test_twice_daily_creates_two_slots():
    out = build_daily_schedule([{"name": "metformin", "frequency": "twice daily"}])
    assert list(out["schedule"].keys()) == ["08:00", "20:00"]
    assert out["total_doses_per_day"] == 2


def test_frequency_alias_bid():
    out = build_daily_schedule([{"name": "x", "frequency": "bid"}])
    assert out["summary"][0]["frequency"] == "twice daily"


def test_notes_carry_through():
    out = build_daily_schedule(
        [{"name": "levothyroxine", "frequency": "once daily", "notes": "empty stomach"}]
    )
    assert out["schedule"]["08:00"][0]["notes"] == "empty stomach"


def test_unknown_frequency_defaults_once_daily():
    out = build_daily_schedule([{"name": "y", "frequency": "whenever"}])
    assert out["summary"][0]["frequency"] == "once daily"


def test_empty_and_nameless_entries_skipped():
    out = build_daily_schedule([{"name": ""}, {"frequency": "bid"}])
    assert out["total_doses_per_day"] == 0
