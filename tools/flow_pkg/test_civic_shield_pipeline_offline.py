"""Offline validation tests for the civic_shield_pipeline @flow definition.

Test organisation
-----------------
CLASS 1 — TestSchemas (ALWAYS OFFLINE)
    Imports only the Pydantic schema classes. These never touch the WXO runtime
    and run without any authentication token.

CLASS 2 — TestFlowStructure  (REQUIRES ACTIVE WXO TOKEN)
CLASS 3 — TestFlowCompile    (REQUIRES ACTIVE WXO TOKEN)
    The @flow decorator in ibm-watsonx-orchestrate v2.20.0 calls
    FlowFactory.create_flow() at decoration time, which calls
    instantiate_client(ToolClient) — this checks for a valid MCSP token and
    exits with code 1 when none is found. As a result, the entire
    civic_shield_pipeline module cannot be imported without an active token.
    These tests are therefore marked with @pytest.mark.requires_wxo_auth
    and skipped automatically when the WXO token is absent.

CLASS 4 — TestC05RegressionExpectations (ALWAYS OFFLINE)
    Documents the expected C05 and C03 output values as pure Python dicts.
    These are reference constants validated as importable documentation.

Run all offline tests (no auth needed):
    python -m pytest tools/flow_pkg/test_civic_shield_pipeline_offline.py -v \
        -k "not requires_wxo_auth"

Run all tests (auth required for structure/compile tests):
    orchestrate env activate eu-gb-22d6bac0 --api-key <KEY>   # restore token first
    python -m pytest tools/flow_pkg/test_civic_shield_pipeline_offline.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest

# ---------------------------------------------------------------------------
# Helper: detect whether a valid WXO token is present by running
# `orchestrate env list` and checking for a non-error exit code.
# ---------------------------------------------------------------------------

def _wxo_token_present() -> bool:
    """Return True when the CLI has a valid, non-expired MCSP token.

    We use `orchestrate agents list` as the probe because it exercises the
    actual token validation path (instantiate_client) — the same path the
    @flow decorator uses. `orchestrate env list` only reads the config file
    and does NOT validate the token, so it cannot be used as a proxy.
    """
    try:
        repo_root = Path(__file__).resolve().parents[2]
        orchestrate_exe = repo_root / "venv" / "Scripts" / "orchestrate.exe"
        result = subprocess.run(
            [str(orchestrate_exe), "agents", "list"],
            capture_output=True, text=True, timeout=15,
        )
        # expired/missing token → [ERROR] on stdout + exit code 1
        return "ERROR" not in result.stdout and result.returncode == 0
    except Exception:
        return False


_HAS_WXO_AUTH = _wxo_token_present()

requires_wxo_auth = pytest.mark.skipif(
    not _HAS_WXO_AUTH,
    reason=(
        "WXO auth token is absent or expired. "
        "Run: orchestrate env activate eu-gb-22d6bac0 --api-key <KEY>, "
        "then re-run this test suite."
    ),
)

# ---------------------------------------------------------------------------
# Lazy import of flow module (only when auth is present)
# ---------------------------------------------------------------------------

_flow_module = None

def _get_flow_module():
    """Import the flow module on first call; return cached module thereafter."""
    global _flow_module
    if _flow_module is None:
        repo_root = str(Path(__file__).resolve().parents[2])
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        import importlib
        _flow_module = importlib.import_module("tools.flow_pkg.civic_shield_pipeline")
    return _flow_module


# ---------------------------------------------------------------------------
# Always-importable: schema classes only (no @flow decorator involved)
# ---------------------------------------------------------------------------

# Import schema classes directly — these are plain Pydantic models and
# do not trigger the @flow decorator.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# We import just the schema models from the source text to avoid triggering
# the @flow decorator. We do this by importing the module only if auth is
# present; otherwise we define a minimal shadow just for schema tests.

if _HAS_WXO_AUTH:
    from tools.flow_pkg.civic_shield_pipeline import (
        PipelineInput,
        PipelineOutput,
        InvestigatorOutput,
        AnalystOutput,
        NotificationOutput,
        ResponseOutput,
        VerifierOutput,
        build_civic_shield_pipeline,
    )
else:
    # Auth absent: import only the schema classes by executing the file up to
    # the @flow decorator. We use a source-code parse trick: read the module
    # source, strip the @flow block, and exec just the schema definitions.
    _src = Path(__file__).with_name("civic_shield_pipeline.py").read_text(encoding="utf-8")
    # Truncate at the @flow decorator line so the decorator never executes.
    _cutoff = _src.find("\n@flow(")
    if _cutoff == -1:
        _cutoff = len(_src)
    _schema_only_src = _src[:_cutoff]

    # Pre-populate the exec namespace with stub objects for the IBM WXO
    # symbols imported at the top of the pipeline module. Without these stubs
    # the `from ibm_watsonx_orchestrate...` import line inside the exec'd
    # source would still attempt to contact the runtime (and may raise or
    # pull in token-validation side-effects). The stubs are only needed to
    # satisfy the import statement; none of the schema classes use them.
    class _FlowStub:
        pass
    def _flow_decorator(*a, **kw):
        def _inner(fn):
            return fn
        return _inner

    _ns: dict = {
        "END":   object(),
        "Flow":  _FlowStub,
        "START": object(),
        "flow":  _flow_decorator,
    }
    exec(compile(_schema_only_src, "civic_shield_pipeline_schemas", "exec"), _ns)

    # Pydantic v2 defers model construction; models that contain List[str]
    # fields defined with default_factory are not "fully defined" until
    # model_rebuild() is called explicitly when the class was created via
    # exec() rather than a normal module import.
    #
    # We must pass _types_namespace so Pydantic can resolve forward-reference
    # strings like 'List' and 'Optional' that were in scope when the model
    # was defined inside exec() but are absent from Pydantic's default
    # rebuild globalns.
    import typing as _typing
    _rebuild_ns = {
        "List":     _typing.List,
        "Optional": _typing.Optional,
        "Any":      _typing.Any,
    }
    # Also include every model defined in _ns so cross-model references resolve.
    _rebuild_ns.update({k: v for k, v in _ns.items() if isinstance(v, type)})

    for _model_name in (
        "RuleViolated",          # rebuild leaf models first (no deps)
        "PipelineInput",
        "InvestigatorOutput",
        "AnalystOutput",
        "NotificationOutput",
        "ResponseOutput",
        "VerifierOutput",
        "PipelineOutput",        # rebuild last (references other models)
    ):
        _m = _ns.get(_model_name)
        if _m is not None and hasattr(_m, "model_rebuild"):
            _m.model_rebuild(_types_namespace=_rebuild_ns)

    PipelineInput        = _ns["PipelineInput"]
    PipelineOutput       = _ns["PipelineOutput"]
    InvestigatorOutput   = _ns["InvestigatorOutput"]
    AnalystOutput        = _ns["AnalystOutput"]
    NotificationOutput   = _ns["NotificationOutput"]
    ResponseOutput       = _ns["ResponseOutput"]
    VerifierOutput       = _ns["VerifierOutput"]
    build_civic_shield_pipeline = None  # unavailable without auth


# ===========================================================================
# CLASS 1 — Schema tests (ALWAYS OFFLINE, no WXO auth needed)
# ===========================================================================

class TestSchemas:

    def test_pipeline_input_has_case_id(self):
        m = PipelineInput(case_id="C05")
        assert m.case_id == "C05"

    def test_pipeline_output_defaults_fail_closed(self):
        """all_stages_complete must default to False — fail-closed sentinel."""
        m = PipelineOutput(case_id="C05", assessment="confirmed")
        assert m.all_stages_complete is False

    def test_pipeline_output_has_all_required_fields(self):
        required = {
            "case_id", "assessment", "evidence", "confidence",
            "score", "severity", "notify_first", "public_restricted",
            "service_ids", "affected_public_service",
            "action_taken", "action_attempts", "action_result",
            "verification_result", "lifecycle_status", "handoff_required",
            "human_intervention", "completed_ai_work",
            "notification_required", "notification_message",
            "investigator_result_json", "analyst_result_json", "response_result_json",
            "all_stages_complete", "errors",
        }
        actual = set(PipelineOutput.model_fields.keys())  # class-level access is correct
        missing = required - actual
        assert not missing, f"PipelineOutput is missing fields: {missing}"

    def test_investigator_output_has_json_field(self):
        assert "investigator_result_json" in InvestigatorOutput.model_fields  # class-level

    def test_analyst_output_has_json_field(self):
        assert "analyst_result_json" in AnalystOutput.model_fields  # class-level

    def test_response_output_has_json_field(self):
        assert "response_result_json" in ResponseOutput.model_fields  # class-level

    def test_notification_output_fields(self):
        m = NotificationOutput(notification_required=True, notification_message="test")
        assert m.notification_required is True
        assert m.notification_message == "test"

    def test_notification_output_default_not_required(self):
        m = NotificationOutput(notification_required=False)
        assert m.notification_message == ""

    def test_pipeline_output_c05_values_round_trip(self):
        """PipelineOutput can hold all expected C05 field values."""
        m = PipelineOutput(
            case_id="C05",
            assessment="confirmed",
            public_restricted=True,
            notify_first=True,
            action_taken="none",
            action_attempts=0,
            action_result="not_run",
            verification_result="not_run",
            lifecycle_status="human_handoff_required",
            handoff_required=True,
            notification_required=True,
            notification_message="Immediate human notification required before any automated action is taken for case C05.",
            all_stages_complete=True,
        )
        assert m.action_taken == "none"
        assert m.verification_result == "not_run"
        assert m.all_stages_complete is True

    def test_pipeline_output_c03_values_round_trip(self):
        """PipelineOutput can hold all expected C03 field values."""
        m = PipelineOutput(
            case_id="C03",
            assessment="confirmed",
            public_restricted=False,
            notify_first=False,
            action_taken="enable_audit_logging",
            action_attempts=1,
            action_result="success",
            verification_result="passed",
            lifecycle_status="awaiting_human_closure",
            handoff_required=False,
            notification_required=False,
            all_stages_complete=True,
        )
        assert m.verification_result == "passed"
        assert m.lifecycle_status == "awaiting_human_closure"
        assert m.all_stages_complete is True


# ===========================================================================
# CLASS 2 — Flow structure tests (REQUIRES ACTIVE WXO TOKEN)
# ===========================================================================

class TestFlowStructure:
    """Structure tests that query the compiled JSON representation.

    The ADK FlowSpec object (flow_obj.spec) stores metadata fields only
    (name, description, schemas, initiators, etc.). Node definitions are NOT
    stored on spec.nodes — they live in the compiled JSON produced by
    flow_obj.to_json(), under the top-level 'nodes' dict keyed by node name.
    Each entry has the shape: { "spec": { "kind", "name", "agent", ... }, "input_map": ... }

    All node-level assertions therefore go through _compiled_nodes(), which
    calls to_json() once and returns that dict.  The to_json() call also
    serves as a full compile-and-serialise pass against the real ADK.
    """

    @staticmethod
    def _compiled_nodes() -> dict:
        """Return the nodes dict from flow_obj.to_json() — keyed by node name."""
        compiled = build_civic_shield_pipeline().to_json()
        if isinstance(compiled, str):
            compiled = json.loads(compiled)
        return compiled["nodes"]

    @requires_wxo_auth
    def test_flow_object_is_returned(self):
        """build_civic_shield_pipeline() must return a Flow instance."""
        from ibm_watsonx_orchestrate.flow_builder.flows import Flow
        flow_obj = build_civic_shield_pipeline()
        assert isinstance(flow_obj, Flow)

    @requires_wxo_auth
    def test_flow_name(self):
        flow_obj = build_civic_shield_pipeline()
        assert flow_obj.spec.name == "civic_shield_pipeline"

    @requires_wxo_auth
    def test_flow_has_input_schema(self):
        flow_obj = build_civic_shield_pipeline()
        assert flow_obj.spec.input_schema is not None

    @requires_wxo_auth
    def test_flow_has_output_schema(self):
        flow_obj = build_civic_shield_pipeline()
        assert flow_obj.spec.output_schema is not None

    @requires_wxo_auth
    def test_all_six_nodes_present(self):
        nodes = self._compiled_nodes()
        # Exclude the implicit __start__ and __end__ sentinel nodes added by the ADK.
        user_nodes = {k for k in nodes if not k.startswith("__")}
        expected = {
            "stage1_security_investigator",
            "stage2_risk_analyst",
            "notification_gate",
            "stage3_response_agent",
            "stage4_verification_handoff",
            "aggregate_results",
        }
        missing = expected - user_nodes
        assert not missing, f"Flow is missing nodes: {missing}"

    @requires_wxo_auth
    def test_all_four_agent_node_names_present(self):
        nodes = self._compiled_nodes()
        agent_nodes = {
            "stage1_security_investigator",
            "stage2_risk_analyst",
            "stage3_response_agent",
            "stage4_verification_handoff",
        }
        missing = agent_nodes - set(nodes.keys())
        assert not missing, f"Missing agent nodes: {missing}"

    @requires_wxo_auth
    def test_notification_script_node_present(self):
        nodes = self._compiled_nodes()
        assert "notification_gate" in nodes

    @requires_wxo_auth
    def test_aggregation_script_node_present(self):
        nodes = self._compiled_nodes()
        assert "aggregate_results" in nodes

    @requires_wxo_auth
    def test_agent_nodes_reference_correct_agents(self):
        nodes = self._compiled_nodes()
        expected_agents = {
            "stage1_security_investigator": "security_investigator",
            "stage2_risk_analyst":          "risk_analyst",
            "stage3_response_agent":        "response_agent",
            "stage4_verification_handoff":  "verification_handoff_agent",
        }
        for node_name, expected_agent in expected_agents.items():
            assert node_name in nodes, f"Node '{node_name}' not found in compiled flow"
            node_spec = nodes[node_name]["spec"]
            actual_agent = node_spec.get("agent")
            assert actual_agent == expected_agent, (
                f"Node '{node_name}' references '{actual_agent}', expected '{expected_agent}'"
            )

    @requires_wxo_auth
    def test_all_agent_nodes_use_create_always_thread_policy(self):
        nodes = self._compiled_nodes()
        agent_node_names = {
            "stage1_security_investigator",
            "stage2_risk_analyst",
            "stage3_response_agent",
            "stage4_verification_handoff",
        }
        for name in agent_node_names:
            assert name in nodes, f"Agent node '{name}' missing from compiled flow"
            node_spec = nodes[name]["spec"]
            policy = node_spec.get("thread_control_policy")
            assert policy == "CREATE_ALWAYS", (
                f"Node '{name}' must use CREATE_ALWAYS, got '{policy}'"
            )

    @requires_wxo_auth
    def test_initiators_includes_orchestrator(self):
        flow_obj = build_civic_shield_pipeline()
        initiators = getattr(flow_obj.spec, 'initiators', []) or []
        assert "orchestrator_agent" in initiators


# ===========================================================================
# CLASS 3 — Flow compile test (REQUIRES ACTIVE WXO TOKEN)
# ===========================================================================

class TestFlowCompile:

    @requires_wxo_auth
    def test_flow_serialises_to_json_without_error(self):
        """to_json() must produce a JSON-serialisable dict containing all node names."""
        flow_obj = build_civic_shield_pipeline()
        try:
            compiled_json = flow_obj.to_json()
            assert compiled_json is not None
            json_str = compiled_json if isinstance(compiled_json, str) else json.dumps(compiled_json)
            for name in [
                "stage1_security_investigator",
                "stage2_risk_analyst",
                "notification_gate",
                "stage3_response_agent",
                "stage4_verification_handoff",
                "aggregate_results",
            ]:
                assert name in json_str, f"Node '{name}' not found in serialised flow JSON"
        except Exception as exc:
            pytest.fail(f"flow.to_json() raised: {exc}")


# ===========================================================================
# CLASS 4 — Regression expectation constants (ALWAYS OFFLINE)
# ===========================================================================

class TestC05RegressionExpectations:
    """Reference constants for C05 and C03 regression tests.
    These are verified as internally consistent; they serve as the acceptance
    criteria for live integration testing once the flow is deployed."""

    C05_EXPECTED = {
        "assessment":            "confirmed",
        "public_restricted":     True,
        "notify_first":          True,
        "action_taken":          "none",
        "action_attempts":       0,
        "action_result":         "not_run",
        "verification_result":   "not_run",
        "lifecycle_status":      "human_handoff_required",
        "handoff_required":      True,
        "notification_required": True,
        "all_stages_complete":   True,
    }

    C03_EXPECTED = {
        "assessment":            "confirmed",
        "public_restricted":     False,
        "notify_first":          False,
        "action_taken":          "enable_audit_logging",
        "action_result":         "success",
        "verification_result":   "passed",
        "lifecycle_status":      "awaiting_human_closure",
        "handoff_required":      False,
        "notification_required": False,
        "all_stages_complete":   True,
    }

    def test_c05_expected_dict_is_coherent(self):
        exp = self.C05_EXPECTED
        assert exp["action_taken"] == "none"
        assert exp["action_result"] == "not_run"
        assert exp["verification_result"] == "not_run"
        assert exp["lifecycle_status"] == "human_handoff_required"
        assert exp["public_restricted"] is True
        assert exp["notification_required"] is True
        # all_stages_complete must still be True — the pipeline ran, it just took no action
        assert exp["all_stages_complete"] is True

    def test_c03_expected_dict_is_coherent(self):
        exp = self.C03_EXPECTED
        assert exp["action_taken"] == "enable_audit_logging"
        assert exp["action_result"] == "success"
        assert exp["verification_result"] == "passed"
        assert exp["lifecycle_status"] == "awaiting_human_closure"
        assert exp["public_restricted"] is False
        assert exp["all_stages_complete"] is True

    def test_c05_and_c03_differ_on_key_fields(self):
        """C05 and C03 must produce structurally different results on the key safety fields."""
        c05 = self.C05_EXPECTED
        c03 = self.C03_EXPECTED
        assert c05["public_restricted"] != c03["public_restricted"]
        assert c05["action_taken"]       != c03["action_taken"]
        assert c05["verification_result"] != c03["verification_result"]
        assert c05["lifecycle_status"]   != c03["lifecycle_status"]


# ===========================================================================
# CLASS 5 — C09 / C10 Regression Expectations (ALWAYS OFFLINE)
# ===========================================================================

class TestC09C10RegressionExpectations:
    """Reference constants and tool-layer regression tests for C09 and C10.

    C09 — "Missing required logging field": snapshot omits audit_logging_enabled.
    C10 — "Wrong type for public access": public_read is the string "false" not bool.

    Both cases produce assessment="invalid_input" at the investigator stage.
    The pipeline runs all four specialist stages unconditionally; the flow's
    aggregate_results script propagates the validation errors and sets
    handoff_required=True (via the inv.assessment guard on line 512 of the
    aggregate script).

    KNOWN LIMITATION — lifecycle_status discrepancy:
        The reference pipeline (pipeline.analyze()) returns
        lifecycle_status="awaiting_corrected_data" for invalid_input cases,
        because the pipeline sets outcome="request_data" before calling the
        verifier.  The flow's verifier agent receives resp["outcome"]="no_action"
        (the response agent returns "no_action" for non-confirmed assessments)
        and therefore falls through to lifecycle="human_handoff_required".
        This discrepancy is documented here and must be verified against the
        live flow trace — the flow output will show "human_handoff_required".

    SAFETY INVARIANTS (must hold for both C09 and C10):
        - assessment == "invalid_input"
        - action_taken == "none"      (no remediation on invalid input)
        - action_result == "not_run"
        - verification_result == "not_run"
        - handoff_required == True    (forced True by aggregate script)
        - all_stages_complete == True (all 4 agent nodes executed)
        - errors list is non-empty and contains the validation error text
        - No autonomous correction or closure
    """

    # Ground truth from tools/investigator_pkg/pipeline.py (reference pipeline).
    # These are the values produced by the tool layer before the flow aggregation.
    C09_TOOL_EXPECTED = {
        "assessment":          "invalid_input",
        "action_taken":        "none",
        "action_result":       "not_run",
        "verification_result": "not_run",
        "lifecycle_status":    "awaiting_corrected_data",   # pipeline reference
        "handoff_required":    False,                       # pipeline reference (flow overrides to True)
        "score":               None,
        "severity":            "unknown",
        "error_contains":      "missing required field: audit_logging_enabled",
    }

    C10_TOOL_EXPECTED = {
        "assessment":          "invalid_input",
        "action_taken":        "none",
        "action_result":       "not_run",
        "verification_result": "not_run",
        "lifecycle_status":    "awaiting_corrected_data",   # pipeline reference
        "handoff_required":    False,                       # pipeline reference (flow overrides to True)
        "score":               None,
        "severity":            "unknown",
        "error_contains":      "field must be a JSON boolean: public_read",
    }

    # Expected PipelineOutput values after the flow's aggregate_results script.
    # lifecycle_status is "human_handoff_required" here (see KNOWN LIMITATION above).
    C09_FLOW_EXPECTED = {
        "assessment":          "invalid_input",
        "action_taken":        "none",
        "action_result":       "not_run",
        "verification_result": "not_run",
        "lifecycle_status":    "human_handoff_required",    # flow-layer value
        "handoff_required":    True,                        # forced by aggregate script
        "all_stages_complete": True,
        "notification_required": False,
    }

    C10_FLOW_EXPECTED = {
        "assessment":          "invalid_input",
        "action_taken":        "none",
        "action_result":       "not_run",
        "verification_result": "not_run",
        "lifecycle_status":    "human_handoff_required",    # flow-layer value
        "handoff_required":    True,                        # forced by aggregate script
        "all_stages_complete": True,
        "notification_required": False,
    }

    # ── Tool-layer tests (use pipeline.analyze() as the reference implementation) ──

    def test_c09_tool_produces_invalid_input(self):
        """pipeline.analyze() must return assessment=invalid_input for C09."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from tools.investigator_pkg.pipeline import analyze
        results = analyze("data/samples/public-service-risk-v1.json", ["C09"])
        assert len(results) == 1
        d = results[0].to_dict()
        assert d["assessment"] == "invalid_input", (
            f"C09 expected assessment=invalid_input, got {d['assessment']}"
        )

    def test_c09_tool_reports_missing_field_error(self):
        """C09 evidence must contain the missing-field error string."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from tools.investigator_pkg.pipeline import analyze
        results = analyze("data/samples/public-service-risk-v1.json", ["C09"])
        d = results[0].to_dict()
        evidence_str = " ".join(d.get("evidence", []))
        assert "missing required field" in evidence_str, (
            f"C09 evidence must mention 'missing required field'; got: {d.get('evidence')}"
        )
        assert "audit_logging_enabled" in evidence_str, (
            f"C09 evidence must name the missing field audit_logging_enabled; got: {d.get('evidence')}"
        )

    def test_c09_tool_no_action_taken(self):
        """C09 must never trigger a remediation action."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from tools.investigator_pkg.pipeline import analyze
        results = analyze("data/samples/public-service-risk-v1.json", ["C09"])
        d = results[0].to_dict()
        assert d["action_taken"] == "none", (
            f"C09 must not trigger any action; got action_taken={d['action_taken']}"
        )
        assert d["action_result"] == "not_run", (
            f"C09 action_result must be not_run; got {d['action_result']}"
        )

    def test_c10_tool_produces_invalid_input(self):
        """pipeline.analyze() must return assessment=invalid_input for C10."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from tools.investigator_pkg.pipeline import analyze
        results = analyze("data/samples/public-service-risk-v1.json", ["C10"])
        assert len(results) == 1
        d = results[0].to_dict()
        assert d["assessment"] == "invalid_input", (
            f"C10 expected assessment=invalid_input, got {d['assessment']}"
        )

    def test_c10_tool_reports_type_error(self):
        """C10 evidence must contain the wrong-type error string for public_read."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from tools.investigator_pkg.pipeline import analyze
        results = analyze("data/samples/public-service-risk-v1.json", ["C10"])
        d = results[0].to_dict()
        evidence_str = " ".join(d.get("evidence", []))
        assert "JSON boolean" in evidence_str, (
            f"C10 evidence must mention 'JSON boolean'; got: {d.get('evidence')}"
        )
        assert "public_read" in evidence_str, (
            f"C10 evidence must name the field public_read; got: {d.get('evidence')}"
        )

    def test_c10_tool_no_action_taken(self):
        """C10 must never trigger a remediation action."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from tools.investigator_pkg.pipeline import analyze
        results = analyze("data/samples/public-service-risk-v1.json", ["C10"])
        d = results[0].to_dict()
        assert d["action_taken"] == "none", (
            f"C10 must not trigger any action; got action_taken={d['action_taken']}"
        )
        assert d["action_result"] == "not_run", (
            f"C10 action_result must be not_run; got {d['action_result']}"
        )

    # ── Schema round-trip tests: PipelineOutput can hold C09/C10 flow values ──

    def test_c09_flow_values_round_trip(self):
        """PipelineOutput can hold all expected C09 flow-layer field values."""
        m = PipelineOutput(
            case_id="C09",
            assessment="invalid_input",
            action_taken="none",
            action_attempts=0,
            action_result="not_run",
            verification_result="not_run",
            lifecycle_status="human_handoff_required",
            handoff_required=True,
            notification_required=False,
            notification_message="",
            all_stages_complete=True,
            errors=["missing required field: audit_logging_enabled"],
            severity="unknown",
            score=None,
        )
        assert m.assessment == "invalid_input"
        assert m.action_taken == "none"
        assert m.handoff_required is True
        assert m.all_stages_complete is True
        assert len(m.errors) == 1
        assert "audit_logging_enabled" in m.errors[0]

    def test_c10_flow_values_round_trip(self):
        """PipelineOutput can hold all expected C10 flow-layer field values."""
        m = PipelineOutput(
            case_id="C10",
            assessment="invalid_input",
            action_taken="none",
            action_attempts=0,
            action_result="not_run",
            verification_result="not_run",
            lifecycle_status="human_handoff_required",
            handoff_required=True,
            notification_required=False,
            notification_message="",
            all_stages_complete=True,
            errors=["field must be a JSON boolean: public_read"],
            severity="unknown",
            score=None,
        )
        assert m.assessment == "invalid_input"
        assert m.action_taken == "none"
        assert m.handoff_required is True
        assert m.all_stages_complete is True
        assert len(m.errors) == 1
        assert "public_read" in m.errors[0]

    # ── Coherence tests: constants are internally consistent ──

    def test_c09_flow_expected_is_coherent(self):
        exp = self.C09_FLOW_EXPECTED
        assert exp["assessment"] == "invalid_input"
        assert exp["action_taken"] == "none"
        assert exp["action_result"] == "not_run"
        assert exp["verification_result"] == "not_run"
        assert exp["handoff_required"] is True,  "invalid_input cases must require human handoff"
        assert exp["all_stages_complete"] is True, "all 4 stages ran — pipeline did complete"
        assert exp["notification_required"] is False, "invalid_input does not trigger notification"

    def test_c10_flow_expected_is_coherent(self):
        exp = self.C10_FLOW_EXPECTED
        assert exp["assessment"] == "invalid_input"
        assert exp["action_taken"] == "none"
        assert exp["action_result"] == "not_run"
        assert exp["verification_result"] == "not_run"
        assert exp["handoff_required"] is True,  "invalid_input cases must require human handoff"
        assert exp["all_stages_complete"] is True, "all 4 stages ran — pipeline did complete"
        assert exp["notification_required"] is False, "invalid_input does not trigger notification"

    def test_c09_and_c10_share_invalid_input_structure(self):
        """Both C09 and C10 are invalid-input cases with identical structural outcomes."""
        c09 = self.C09_FLOW_EXPECTED
        c10 = self.C10_FLOW_EXPECTED
        # Both must have same structural outcomes even though errors differ
        for field in ("assessment", "action_taken", "action_result",
                      "verification_result", "handoff_required",
                      "all_stages_complete", "notification_required"):
            assert c09[field] == c10[field], (
                f"C09 and C10 should have identical {field}: "
                f"C09={c09[field]}, C10={c10[field]}"
            )

    def test_tool_expected_error_text_is_distinct(self):
        """C09 and C10 produce different validation error messages."""
        assert self.C09_TOOL_EXPECTED["error_contains"] != self.C10_TOOL_EXPECTED["error_contains"], (
            "C09 and C10 must produce distinct error messages"
        )
        # C09 is a missing field; C10 is a type error
        assert "missing" in self.C09_TOOL_EXPECTED["error_contains"]
        assert "boolean" in self.C10_TOOL_EXPECTED["error_contains"]
