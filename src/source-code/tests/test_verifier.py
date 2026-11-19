"""Unit tests for the Verification & Handoff agent module.

Tests cover:
  1. C03 — verification passed after authorized action succeeds
  2. C07 — tool reports success but state unchanged → verification failed, handoff
  3. C05 — no action taken → verification not_run
  4. Handoff packet contains all eight required fields (§8 of the project concept)
  5. Lifecycle status mapping for all outcome values

Run from src/source-code/:
    python -m pytest tests/test_verifier.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

from src.agents.investigator import investigate
from src.agents.analyst import analyse_impact
from src.agents.response_agent import execute_response
from src.agents.verifier import verify_and_prepare_handoff

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = REPOSITORY_ROOT / "data" / "samples" / "public-service-risk-v1.json"

# Required handoff packet fields from §8 of the project concept document.
_REQUIRED_HANDOFF_FIELDS = {
    "verification_result",
    "outcome",
    "handoff_required",
    "lifecycle_status",
    "human_intervention",
    "completed_ai_work",
    "events",
}


def _load() -> dict:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def _run(ds: dict, case_id: str) -> tuple:
    """Return (inv, an, resp, vr) for the given case."""
    assets = {item["id"]: item for item in ds["assets"]}
    baselines = {item["id"]: item for item in ds["baselines"]}
    services = {item["id"]: item for item in ds["services"]}
    clock = ds["simulation_clock"]

    case = next(c for c in ds["cases"] if c["id"] == case_id)
    asset = assets[case["asset_id"]]
    baseline = baselines[case["baseline_id"]]

    inv = investigate(case, asset, baseline, ds["exceptions"], clock)
    an = analyse_impact(inv, services, asset, ds["policy"])
    resp = execute_response(inv, an, case, ds["policy"], clock)
    vr = verify_and_prepare_handoff(inv, an, resp, case)
    return inv, an, resp, vr


# ---------------------------------------------------------------------------
# Test 1 — C03: authorized action succeeds → verification passed
# ---------------------------------------------------------------------------

def test_c03_verification_passed():
    ds = _load()
    _inv, _an, _resp, vr = _run(ds, "C03")

    assert vr["verification_result"] == "passed"
    assert vr["outcome"] == "verified_awaiting_human_closure"
    assert vr["handoff_required"] is False
    assert vr["lifecycle_status"] == "awaiting_human_closure"
    # Verification event must be present in the event list
    event_names = [e["event"] for e in vr["events"]]
    assert "verification" in event_names


# ---------------------------------------------------------------------------
# Test 2 — C07: tool reports success but state unchanged → verification failed
# ---------------------------------------------------------------------------

def test_c07_tool_success_but_state_unchanged_verification_failed():
    ds = _load()
    _inv, _an, _resp, vr = _run(ds, "C07")

    assert vr["verification_result"] == "failed"
    assert vr["outcome"] == "handoff"
    assert vr["handoff_required"] is True
    assert vr["lifecycle_status"] == "human_handoff_required"
    # Human intervention message must mention "do not retry"
    combined = " ".join(vr["human_intervention"]).lower()
    assert "do not retry" in combined


# ---------------------------------------------------------------------------
# Test 3 — C05: no action taken → verification not_run
# ---------------------------------------------------------------------------

def test_c05_verification_not_run_when_no_action():
    ds = _load()
    _inv, _an, _resp, vr = _run(ds, "C05")

    assert vr["verification_result"] == "not_run"
    assert vr["handoff_required"] is True
    # Notification event must precede the (empty) action sequence
    event_names = [e["event"] for e in vr["events"]]
    assert "notification" in event_names
    assert "verification" not in event_names


# ---------------------------------------------------------------------------
# Test 4 — Handoff packet contains all required fields
# ---------------------------------------------------------------------------

def test_handoff_packet_contains_all_required_fields():
    ds = _load()
    # Use C05 (handoff case) to exercise a fully populated handoff packet.
    _inv, _an, _resp, vr = _run(ds, "C05")

    missing = _REQUIRED_HANDOFF_FIELDS - set(vr.keys())
    assert not missing, f"Missing required handoff fields: {missing}"

    # human_intervention and completed_ai_work must be non-empty lists
    assert isinstance(vr["human_intervention"], list) and len(vr["human_intervention"]) >= 1
    assert isinstance(vr["completed_ai_work"], list) and len(vr["completed_ai_work"]) >= 1


# ---------------------------------------------------------------------------
# Test 5 — Lifecycle status mapping across all outcome values
# ---------------------------------------------------------------------------

def test_lifecycle_status_mapping_all_outcomes():
    """Verify lifecycle_status is set correctly for each of the four paths."""
    ds = _load()
    expected = {
        "C01": "awaiting_human_review",        # compliant → no_action
        "C03": "awaiting_human_closure",        # verified_awaiting_human_closure
        "C06": "awaiting_human_approval",       # awaiting_approval
        "C07": "human_handoff_required",        # handoff (verification failed)
        "C11": "human_handoff_required",        # handoff (no service mapping)
    }
    for case_id, expected_lifecycle in expected.items():
        _inv, _an, _resp, vr = _run(ds, case_id)
        assert vr["lifecycle_status"] == expected_lifecycle, (
            f"C{case_id}: expected lifecycle_status={expected_lifecycle!r}, "
            f"got {vr['lifecycle_status']!r}"
        )
