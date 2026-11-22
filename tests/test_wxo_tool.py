"""Offline unit tests for the analyze_risk_cases @tool wrapper.

No watsonx Orchestrate platform connection is required. The @tool decorator
is directly callable; its return value is a ToolResponse whose .content
attribute holds the actual list[dict] produced by the pipeline.

Run:
    python -m pytest tests/test_wxo_tool.py -v
"""

import sys
from pathlib import Path

# Add the package directory to sys.path so the tool's relative import
# (from pipeline import analyze) resolves correctly offline.
_PKG = Path(__file__).resolve().parents[1] / "tools" / "risk_tool_pkg"
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from analyze_risk_cases import analyze_risk_cases  # noqa: E402


# ---------------------------------------------------------------------------
# C03 — authorised logging correction, successfully verified
# ---------------------------------------------------------------------------

def test_c03_corrects_logging_and_verifies_independently():
    result = analyze_risk_cases("C03")
    cases = result.content
    assert len(cases) == 1
    r = cases[0]
    assert r["case_id"] == "C03"
    assert r["score"] == 30
    assert r["action_taken"] == "enable_audit_logging"
    assert r["action_attempts"] == 1
    assert r["action_result"] == "success"
    assert r["verification_result"] == "passed"
    assert r["outcome"] == "verified_awaiting_human_closure"
    assert r["handoff_required"] is False


# ---------------------------------------------------------------------------
# C05 — critical restricted exposure, no automatic action, mandatory handoff
# ---------------------------------------------------------------------------

def test_c05_escalates_without_automatic_change():
    result = analyze_risk_cases("C05")
    cases = result.content
    assert len(cases) == 1
    r = cases[0]
    assert r["case_id"] == "C05"
    assert r["score"] == 100
    assert r["severity"] == "critical"
    assert r["action_taken"] == "none"
    assert r["action_attempts"] == 0
    assert r["verification_result"] == "not_run"
    assert r["handoff_required"] is True


# ---------------------------------------------------------------------------
# C07 — tool reports success but state unchanged → handoff, no retry
# ---------------------------------------------------------------------------

def test_c07_detects_success_without_state_change_and_does_not_retry():
    result = analyze_risk_cases("C07")
    cases = result.content
    assert len(cases) == 1
    r = cases[0]
    assert r["case_id"] == "C07"
    assert r["action_taken"] == "enable_audit_logging"
    assert r["action_attempts"] == 1
    assert r["action_result"] == "success"
    assert r["verification_result"] == "failed"
    assert r["outcome"] == "handoff"
    assert r["handoff_required"] is True


# ---------------------------------------------------------------------------
# C11 — missing service dependency → score None, unknown severity, handoff
# ---------------------------------------------------------------------------

def test_c11_missing_service_dependency():
    result = analyze_risk_cases("C11")
    cases = result.content
    assert len(cases) == 1
    r = cases[0]
    assert r["case_id"] == "C11"
    assert r["score"] is None
    assert r["severity"] == "unknown"
    assert r["action_taken"] == "none"
    assert r["action_attempts"] == 0
    assert r["handoff_required"] is True


# ---------------------------------------------------------------------------
# ALL — bulk invocation returns all 12 cases
# ---------------------------------------------------------------------------

def test_all_returns_12_cases():
    result = analyze_risk_cases("ALL")
    cases = result.content
    assert len(cases) == 12


# ---------------------------------------------------------------------------
# Comma-separated multi-case selection
# ---------------------------------------------------------------------------

def test_comma_separated_two_cases():
    result = analyze_risk_cases("C03, C05")
    cases = result.content
    ids = {r["case_id"] for r in cases}
    assert ids == {"C03", "C05"}


def test_comma_separated_four_cases():
    result = analyze_risk_cases("C03, C05, C07, C11")
    cases = result.content
    ids = {r["case_id"] for r in cases}
    assert ids == {"C03", "C05", "C07", "C11"}


# ---------------------------------------------------------------------------
# Result dict shape — check required fields are present
# ---------------------------------------------------------------------------

def test_result_dict_has_required_fields():
    result = analyze_risk_cases("C03")
    r = result.content[0]
    required_fields = {
        "case_id", "title", "asset_id", "asset_name", "affected_public_service",
        "assessment", "finding", "severity", "score", "outcome",
        "action_taken", "action_attempts", "action_result", "verification_result",
        "handoff_required", "escalation_required", "human_intervention",
        "completed_ai_work", "outstanding_human_work", "events", "lifecycle_status",
    }
    missing = required_fields - set(r.keys())
    assert not missing, f"Missing fields in result dict: {missing}"
