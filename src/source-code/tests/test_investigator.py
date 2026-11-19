"""Unit tests for the Security Investigator agent module.

Tests cover: compliant input, missing required field, wrong-type boolean,
valid exception suppression, expired exception, wrong-asset exception.

Run from src/source-code/:
    python -m pytest tests/test_investigator.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

from src.agents.investigator import investigate

# ---------------------------------------------------------------------------
# Fixtures: load the shared dataset once per session
# ---------------------------------------------------------------------------

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = REPOSITORY_ROOT / "data" / "samples" / "public-service-risk-v1.json"


def _load() -> dict:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def _context(ds: dict) -> tuple:
    """Return (assets, baselines, exceptions, clock) indexed dicts."""
    assets = {item["id"]: item for item in ds["assets"]}
    baselines = {item["id"]: item for item in ds["baselines"]}
    return assets, baselines, ds["exceptions"], ds["simulation_clock"]


def _case(ds: dict, case_id: str) -> dict:
    return next(c for c in ds["cases"] if c["id"] == case_id)


# ---------------------------------------------------------------------------
# Test 1 — compliant case returns "compliant"
# ---------------------------------------------------------------------------

def test_valid_compliant_case_returns_compliant():
    ds = _load()
    assets, baselines, exceptions, clock = _context(ds)
    case = _case(ds, "C01")          # All fields correct, no deviations
    asset = assets[case["asset_id"]]
    baseline = baselines[case["baseline_id"]]

    result = investigate(case, asset, baseline, exceptions, clock)

    assert result["assessment"] == "compliant"
    assert result["rules_violated"] == []
    assert result["errors"] == []
    assert result["evidence"] == []
    assert result["confidence"] == 1.0


# ---------------------------------------------------------------------------
# Test 2 — missing required field returns "invalid_input"
# ---------------------------------------------------------------------------

def test_missing_field_returns_invalid_input():
    ds = _load()
    assets, baselines, exceptions, clock = _context(ds)
    case = _case(ds, "C09")          # audit_logging_enabled field is absent
    asset = assets[case["asset_id"]]
    baseline = baselines[case["baseline_id"]]

    result = investigate(case, asset, baseline, exceptions, clock)

    assert result["assessment"] == "invalid_input"
    assert result["confidence"] == 0.0
    assert any("missing required field" in e for e in result["errors"])
    assert result["rules_violated"] == []


# ---------------------------------------------------------------------------
# Test 3 — string instead of boolean returns "invalid_input"
# ---------------------------------------------------------------------------

def test_string_boolean_returns_invalid_input():
    ds = _load()
    assets, baselines, exceptions, clock = _context(ds)
    case = _case(ds, "C10")          # public_read is "false" (string), not False
    asset = assets[case["asset_id"]]
    baseline = baselines[case["baseline_id"]]

    result = investigate(case, asset, baseline, exceptions, clock)

    assert result["assessment"] == "invalid_input"
    assert result["confidence"] == 0.0
    assert any("field must be a JSON boolean" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# Test 4 — matching valid exception suppresses the finding
# ---------------------------------------------------------------------------

def test_matching_exception_suppresses_rule():
    ds = _load()
    assets, baselines, exceptions, clock = _context(ds)
    case = _case(ds, "C02")          # public_read=True, but EX-PUBLIC exception applies
    asset = assets[case["asset_id"]]
    baseline = baselines[case["baseline_id"]]

    result = investigate(case, asset, baseline, exceptions, clock)

    assert result["assessment"] == "compliant"
    assert result["rules_violated"] == []
    # The finding that *would* have fired is CFG-PUBLIC (public_read=True)
    # but the valid exception suppresses it.
    assert all("CFG-PUBLIC" not in e for e in result["evidence"])


# ---------------------------------------------------------------------------
# Test 5 — expired exception does NOT suppress the finding
# ---------------------------------------------------------------------------

def test_expired_exception_does_not_suppress():
    ds = _load()
    assets, baselines, exceptions, clock = _context(ds)
    # Mutate the clock to be after the exception expiry (2026-12-31T23:59:59Z)
    # by advancing it to 2027-01-01.
    mutated_clock = "2027-01-01T00:00:00Z"

    case = _case(ds, "C02")
    asset = assets[case["asset_id"]]
    baseline = baselines[case["baseline_id"]]

    result = investigate(case, asset, baseline, exceptions, mutated_clock)

    # Exception is expired → CFG-PUBLIC deviation should be flagged.
    assert result["assessment"] == "confirmed"
    assert any(r["id"] == "CFG-PUBLIC" for r in result["rules_violated"])


# ---------------------------------------------------------------------------
# Test 6 — wrong-asset exception does NOT suppress the finding
# ---------------------------------------------------------------------------

def test_wrong_asset_exception_does_not_suppress():
    """An exception that references a different asset must not be applied."""
    ds = _load()
    assets, baselines, exceptions, clock = _context(ds)

    # C02 uses AST-PUBLIC. Mutate the exception to reference AST-PERMIT instead.
    mutated_exceptions = json.loads(json.dumps(exceptions))  # deep copy
    for exc in mutated_exceptions:
        if exc["id"] == "EX-PUBLIC":
            exc["asset_id"] = "AST-PERMIT"   # wrong asset

    case = _case(ds, "C02")
    asset = assets[case["asset_id"]]
    baseline = baselines[case["baseline_id"]]

    result = investigate(case, asset, baseline, mutated_exceptions, clock)

    # Exception asset_id doesn't match case asset_id → finding fires.
    assert result["assessment"] == "confirmed"
    assert any(r["id"] == "CFG-PUBLIC" for r in result["rules_violated"])
