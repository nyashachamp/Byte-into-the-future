"""Unit tests for the Response Agent module.

Tests cover all authorization invariants:
  1. C03 — authorized action executes successfully (1 attempt)
  2. C05 — public_restricted blocks action (0 attempts)
  3. C06 — missing authorization blocks action (0 attempts)
  4. C07 — success_without_change: tool reports success but state unchanged (1 attempt, no retry)
  5. C08 — transient_then_success: first attempt fails, second succeeds (2 attempts)
  6. Expired authorization — action blocked even when otherwise permitted
  7. sandbox_only=False — action blocked even when action is in allowed_actions

Run from src/source-code/:
    python -m pytest tests/test_response_agent.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

from src.agents.investigator import investigate
from src.agents.analyst import analyse_impact
from src.agents.response_agent import execute_response

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = REPOSITORY_ROOT / "data" / "samples" / "public-service-risk-v1.json"


def _load() -> dict:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def _run(ds: dict, case_id: str, *, override_case: dict | None = None) -> dict:
    """Return the ResponseResult for the given case (or an override case dict)."""
    assets = {item["id"]: item for item in ds["assets"]}
    baselines = {item["id"]: item for item in ds["baselines"]}
    services = {item["id"]: item for item in ds["services"]}
    clock = ds["simulation_clock"]

    case = override_case or next(c for c in ds["cases"] if c["id"] == case_id)
    asset = assets[case["asset_id"]]
    baseline = baselines[case["baseline_id"]]

    inv = investigate(case, asset, baseline, ds["exceptions"], clock)
    an = analyse_impact(inv, services, asset, ds["policy"])
    return execute_response(inv, an, case, ds["policy"], clock)


# ---------------------------------------------------------------------------
# Test 1 — C03: authorized, one attempt, success
# ---------------------------------------------------------------------------

def test_c03_executes_and_returns_success():
    ds = _load()
    resp = _run(ds, "C03")

    assert resp["action_taken"] == "enable_audit_logging"
    assert resp["action_attempts"] == 1
    assert resp["action_result"] == "success"
    assert resp["post_state"].get("audit_logging_enabled") is True
    # Notification event must NOT precede action on C03 (score=30 < 60)
    event_names = [e["event"] for e in resp["events"]]
    assert "notification" not in event_names


# ---------------------------------------------------------------------------
# Test 2 — C05: public_restricted — zero attempts regardless of authorization
# ---------------------------------------------------------------------------

def test_c05_public_restricted_zero_attempts():
    ds = _load()
    resp = _run(ds, "C05")

    assert resp["action_taken"] == "none"
    assert resp["action_attempts"] == 0
    assert resp["action_result"] == "not_run"
    # Notification event must still be emitted before the (non-)action
    event_names = [e["event"] for e in resp["events"]]
    assert "notification" in event_names


# ---------------------------------------------------------------------------
# Test 3 — C06: not in allowed_actions — zero attempts
# ---------------------------------------------------------------------------

def test_c06_no_auth_zero_attempts():
    ds = _load()
    resp = _run(ds, "C06")
    # C06 snapshot has audit_logging_enabled=False but allowed_actions=[]
    assert resp["action_taken"] == "none"
    assert resp["action_attempts"] == 0
    assert resp["action_result"] == "not_run"


# ---------------------------------------------------------------------------
# Test 4 — C07: success_without_change — tool reports success, state unchanged, no retry
# ---------------------------------------------------------------------------

def test_c07_success_without_change_one_attempt_no_retry():
    ds = _load()
    resp = _run(ds, "C07")

    assert resp["action_taken"] == "enable_audit_logging"
    assert resp["action_attempts"] == 1
    assert resp["action_result"] == "success"
    # State must still show audit_logging_enabled=False
    assert resp["post_state"].get("audit_logging_enabled") is False


# ---------------------------------------------------------------------------
# Test 5 — C08: transient_then_success — two attempts, second succeeds
# ---------------------------------------------------------------------------

def test_c08_transient_first_then_success_two_attempts():
    ds = _load()
    resp = _run(ds, "C08")

    assert resp["action_taken"] == "enable_audit_logging"
    assert resp["action_attempts"] == 2
    assert resp["action_result"] == "success"
    assert resp["post_state"].get("audit_logging_enabled") is True
    # Verify event sequence: attempt 1 → transient, attempt 2 → success
    events = resp["events"]
    assert events[0]["event"] == "action_attempt"
    assert events[1]["event"] == "tool_result"
    assert "Temporary" in events[1]["detail"]
    assert events[2]["event"] == "action_attempt"
    assert events[3]["event"] == "tool_result"
    assert "success" in events[3]["detail"].lower()


# ---------------------------------------------------------------------------
# Test 6 — Expired authorization — action blocked even when otherwise permitted
# ---------------------------------------------------------------------------

def test_expired_auth_zero_attempts():
    ds = _load()
    # Mutate C03's authorization to be expired (before the simulation clock)
    case = json.loads(json.dumps(next(c for c in ds["cases"] if c["id"] == "C03")))
    case["authorization"]["expires_at"] = "2026-10-19T00:00:00Z"  # before clock

    resp = _run(ds, "C03", override_case=case)

    assert resp["action_taken"] == "none"
    assert resp["action_attempts"] == 0
    assert resp["action_result"] == "not_run"


# ---------------------------------------------------------------------------
# Test 7 — sandbox_only=False — action blocked even with correct allowed_actions
# ---------------------------------------------------------------------------

def test_non_sandbox_zero_attempts():
    ds = _load()
    # Mutate C03's authorization so sandbox_only is False
    case = json.loads(json.dumps(next(c for c in ds["cases"] if c["id"] == "C03")))
    case["authorization"]["sandbox_only"] = False

    resp = _run(ds, "C03", override_case=case)

    assert resp["action_taken"] == "none"
    assert resp["action_attempts"] == 0
    assert resp["action_result"] == "not_run"
