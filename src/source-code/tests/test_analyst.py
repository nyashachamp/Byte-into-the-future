"""Unit tests for the Risk & Dependency Analyst agent module.

Tests cover: C03 score=30, C04 score=60+notify_first, C05 score=100+public_restricted,
C11 null score (no service mapping), compliant case zero score.

Run from src/source-code/:
    python -m pytest tests/test_analyst.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

from src.agents.investigator import investigate
from src.agents.analyst import analyse_impact

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = REPOSITORY_ROOT / "data" / "samples" / "public-service-risk-v1.json"


def _load() -> dict:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def _run(ds: dict, case_id: str) -> tuple:
    """Return (inv_result, an_result) for the given case."""
    assets = {item["id"]: item for item in ds["assets"]}
    baselines = {item["id"]: item for item in ds["baselines"]}
    services = {item["id"]: item for item in ds["services"]}
    clock = ds["simulation_clock"]

    case = next(c for c in ds["cases"] if c["id"] == case_id)
    asset = assets[case["asset_id"]]
    baseline = baselines[case["baseline_id"]]

    inv = investigate(case, asset, baseline, ds["exceptions"], clock)
    an = analyse_impact(inv, services, asset, ds["policy"])
    return inv, an


# ---------------------------------------------------------------------------
# Test 1 — C03: score 30, medium severity, notify_first=False
# ---------------------------------------------------------------------------

def test_c03_score_is_30_medium_no_notify():
    ds = _load()
    _inv, an = _run(ds, "C03")
    # CFG-LOGGING weight=10, SVC-PERMIT criticality=2 → 10 + 10*2 = 30
    assert an["score"] == 30
    assert an["severity"] == "medium"
    assert an["notify_first"] is False
    assert an["public_restricted"] is False
    assert "SVC-PERMIT" in an["service_ids"]


# ---------------------------------------------------------------------------
# Test 2 — C04: score 60, high severity, notify_first=True (score >= 60)
# ---------------------------------------------------------------------------

def test_c04_score_is_60_notify_first():
    ds = _load()
    _inv, an = _run(ds, "C04")
    # CFG-LOGGING weight=10, SVC-EMERGENCY criticality=5 → 10 + 10*5 = 60
    assert an["score"] == 60
    assert an["severity"] == "high"
    assert an["notify_first"] is True
    assert an["public_restricted"] is False
    assert "SVC-EMERGENCY" in an["service_ids"]


# ---------------------------------------------------------------------------
# Test 3 — C05: score 100, critical, notify_first=True, public_restricted=True
# ---------------------------------------------------------------------------

def test_c05_score_100_critical_public_restricted():
    ds = _load()
    _inv, an = _run(ds, "C05")
    # CFG-PUBLIC weight=60, SVC-AID criticality=4 → min(100, 60+40) = 100
    assert an["score"] == 100
    assert an["severity"] == "critical"
    assert an["notify_first"] is True
    assert an["public_restricted"] is True
    assert "SVC-AID" in an["service_ids"]


# ---------------------------------------------------------------------------
# Test 4 — C11: no service mapping → score None, severity unknown
# ---------------------------------------------------------------------------

def test_c11_no_services_gives_null_score():
    ds = _load()
    _inv, an = _run(ds, "C11")
    # AST-UNKNOWN has service_ids=[] → score must be None
    assert an["score"] is None
    assert an["severity"] == "unknown"
    assert an["notify_first"] is False
    assert an["service_ids"] == []
    assert an["affected_public_service"] == "Unknown service impact"


# ---------------------------------------------------------------------------
# Test 5 — Compliant case (C01): score 0, severity none, no notification
# ---------------------------------------------------------------------------

def test_compliant_case_score_zero_severity_none():
    ds = _load()
    _inv, an = _run(ds, "C01")
    assert an["score"] == 0
    assert an["severity"] == "none"
    assert an["notify_first"] is False
    assert an["public_restricted"] is False
