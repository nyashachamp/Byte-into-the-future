"""Offline unit tests for the four specialist @tool entry points.

These tests import the tool functions directly and call them without a running
WXO runtime.  The @tool decorator makes the function callable in-process;
result.content holds the actual return value.

Each test re-loads the bundled dataset from within the tool package so there
is no dependency on a running server or the top-level data/samples/ path.

Run:
    python -m pytest tests/test_wxo_specialist_tools.py -v
        (from the repo root, using the venv that has ibm-watsonx-orchestrate)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path surgery: add each tool package root to sys.path so that the bare
# "from pipeline import ..." and "from agents.xxx import ..." imports inside
# the entry-point files and agent modules resolve correctly when running
# from the repo root.
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

INVESTIGATOR_PKG = ROOT / "tools" / "investigator_pkg"
ANALYST_PKG      = ROOT / "tools" / "analyst_pkg"
RESPONSE_PKG     = ROOT / "tools" / "response_pkg"
VERIFIER_PKG     = ROOT / "tools" / "verifier_pkg"


def _add_pkg(pkg_path: Path) -> None:
    """Prepend pkg_path to sys.path if not already present."""
    s = str(pkg_path)
    if s not in sys.path:
        sys.path.insert(0, s)


# Each entry-point uses importlib.util with package-unique module names
# (e.g. "_inv_pipeline", "_an_analyst") so the four packages do NOT collide
# in sys.modules even when their pkg roots are all on sys.path at once.
# We add all four roots now and leave them there for the duration of the test
# session.

for _pkg in (INVESTIGATOR_PKG, ANALYST_PKG, RESPONSE_PKG, VERIFIER_PKG):
    _add_pkg(_pkg)

from investigate_case   import investigate_case    # noqa: E402
from analyse_impact     import analyse_impact      # noqa: E402
from execute_response   import execute_response    # noqa: E402
from verify_and_handoff import verify_and_handoff  # noqa: E402


# ---------------------------------------------------------------------------
# Shared helper: unwrap the @tool return value
# ---------------------------------------------------------------------------

def _call(fn, *args, **kwargs):
    """Call a @tool-decorated function and return its content."""
    result = fn(*args, **kwargs)
    # ibm-watsonx-orchestrate @tool returns a ToolResult with .content
    # In offline (non-server) invocation the decorator is transparent and
    # the function returns its value directly.
    if hasattr(result, "content"):
        return result.content
    return result


# ===========================================================================
# Security Investigator tests
# ===========================================================================

class TestInvestigateCase:

    def test_investigate_c03_returns_confirmed(self):
        """C03: audit_logging_enabled=False, no exceptions → assessment='confirmed'."""
        result = _call(investigate_case, "C03")
        assert result["assessment"] == "confirmed"
        assert len(result["rules_violated"]) == 1
        assert result["rules_violated"][0]["id"] == "CFG-LOGGING"
        assert result["confidence"] == 1.0
        assert result["errors"] == []

    def test_investigate_c09_returns_invalid_input(self):
        """C09: missing 'audit_logging_enabled' field → assessment='invalid_input'."""
        result = _call(investigate_case, "C09")
        assert result["assessment"] == "invalid_input"
        assert result["confidence"] == 0.0
        assert any("audit_logging_enabled" in e for e in result["errors"])

    def test_investigate_c02_exception_suppresses(self):
        """C02: public_read=True with active EX-PUBLIC exception → assessment='compliant'."""
        result = _call(investigate_case, "C02")
        assert result["assessment"] == "compliant"
        assert result["rules_violated"] == []
        assert result["errors"] == []


# ===========================================================================
# Risk & Dependency Analyst tests
# ===========================================================================

class TestAnalyseImpact:

    def test_analyse_c04_score_60_notify_true(self):
        """C04: CFG-LOGGING on AST-EMERGENCY (SVC-EMERGENCY criticality=5, weight=10).
        score = min(100, 10 + 10*5) = 60 → severity='high', notify_first=True.
        """
        inv_dict = _call(investigate_case, "C04")
        inv_json = json.dumps(inv_dict)
        result = _call(analyse_impact, "C04", inv_json)
        assert result["score"] == 60
        assert result["severity"] == "high"
        assert result["notify_first"] is True
        assert result["public_restricted"] is False

    def test_analyse_c11_null_score(self):
        """C11: CFG-LOGGING on AST-UNKNOWN (no service_ids) → score=None, severity='unknown'."""
        inv_dict = _call(investigate_case, "C11")
        inv_json = json.dumps(inv_dict)
        result = _call(analyse_impact, "C11", inv_json)
        assert result["score"] is None
        assert result["severity"] == "unknown"
        assert result["service_ids"] == []


# ===========================================================================
# Response Agent tests
# ===========================================================================

class TestExecuteResponse:

    def _pipeline_to_response(self, case_id: str):
        """Run the full investigator → analyst → response chain for a case."""
        inv_dict = _call(investigate_case, case_id)
        inv_json = json.dumps(inv_dict)
        an_dict  = _call(analyse_impact, case_id, inv_json)
        an_json  = json.dumps(an_dict)
        return _call(execute_response, case_id, inv_json, an_json)

    def test_execute_c03_success(self):
        """C03: authorized CFG-LOGGING fix, tool_behavior='success' → action_result='success'."""
        result = self._pipeline_to_response("C03")
        assert result["action_taken"] == "enable_audit_logging"
        assert result["action_result"] == "success"
        assert result["action_attempts"] == 1
        assert result["post_state"]["audit_logging_enabled"] is True

    def test_execute_c05_zero_attempts(self):
        """C05: restricted_synthetic public exposure → action never taken, action_attempts=0."""
        result = self._pipeline_to_response("C05")
        assert result["action_taken"] == "none"
        assert result["action_attempts"] == 0
        assert result["action_result"] == "not_run"

    def test_execute_c07_no_retry(self):
        """C07: success_without_change → action_result='success' but state unchanged."""
        result = self._pipeline_to_response("C07")
        assert result["action_taken"] == "enable_audit_logging"
        assert result["action_result"] == "success"
        # State must NOT be updated — the tool reported success but changed nothing.
        assert result["post_state"]["audit_logging_enabled"] is False

    def test_execute_c08_two_attempts(self):
        """C08: transient_then_success with max_attempts=2 → 2 attempts, final success."""
        result = self._pipeline_to_response("C08")
        assert result["action_taken"] == "enable_audit_logging"
        assert result["action_attempts"] == 2
        assert result["action_result"] == "success"
        assert result["post_state"]["audit_logging_enabled"] is True


# ===========================================================================
# Verification & Handoff tests
# ===========================================================================

class TestVerifyAndHandoff:

    def _full_pipeline(self, case_id: str):
        """Run the full four-stage pipeline for a case."""
        inv_dict  = _call(investigate_case, case_id)
        inv_json  = json.dumps(inv_dict)
        an_dict   = _call(analyse_impact, case_id, inv_json)
        an_json   = json.dumps(an_dict)
        resp_dict = _call(execute_response, case_id, inv_json, an_json)
        resp_json = json.dumps(resp_dict)
        return _call(verify_and_handoff, case_id, inv_json, an_json, resp_json)

    def test_verify_c03_passed(self):
        """C03: action succeeded and state changed → verification_result='passed'."""
        result = self._full_pipeline("C03")
        assert result["verification_result"] == "passed"
        assert result["handoff_required"] is False
        assert result["outcome"] == "verified_awaiting_human_closure"
        assert result["lifecycle_status"] == "awaiting_human_closure"

    def test_verify_c07_failed(self):
        """C07: tool reported success but state unchanged → verification_result='failed'."""
        result = self._full_pipeline("C07")
        assert result["verification_result"] == "failed"
        assert result["handoff_required"] is True
        assert result["outcome"] == "handoff"

    def test_verify_handoff_all_required_fields(self):
        """C03 full pipeline: all required output keys must be present."""
        result = self._full_pipeline("C03")
        required_keys = {
            "verification_result",
            "outcome",
            "handoff_required",
            "human_intervention",
            "completed_ai_work",
            "lifecycle_status",
            "events",
        }
        missing = required_keys - set(result.keys())
        assert not missing, f"Missing keys in verify_and_handoff result: {missing}"
