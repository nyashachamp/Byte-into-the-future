"""Offline structural validation tests for the five native agent YAML specs.

These tests verify that all five agents in agents/ are:
  - Valid YAML (parseable without errors)
  - Conformant with the ADK v1 native agent schema (required fields present,
    correct types, expected values)
  - Consistent with each other (collaborator graph, tool name references,
    import-order safety requirements)

No watsonx Orchestrate runtime is required.  All assertions are pure
static analysis of the YAML files.

Run:
    python -m pytest tests/test_agent_yaml.py -v
        (from the repo root, using the venv that has PyYAML)

Corresponds to the five offline structural tests described in §4 of
docs/five-agent-recovery-plan.md, plus additional M2 schema checks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT       = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / "agents"

_SPECIALIST_FILES = {
    "security_investigator":    AGENTS_DIR / "security_investigator_agent.yaml",
    "risk_analyst":             AGENTS_DIR / "risk_analyst_agent.yaml",
    "response_agent":           AGENTS_DIR / "response_agent.yaml",
    "verification_handoff_agent": AGENTS_DIR / "verification_handoff_agent.yaml",
}
_ORCHESTRATOR_FILE = AGENTS_DIR / "orchestrator_agent.yaml"
_ORIGINAL_FILE     = AGENTS_DIR / "risk_analysis_agent.yaml"

# Expected tool assignment: agent name → tool function name
_EXPECTED_TOOLS = {
    "security_investigator":      "investigate_case",
    "risk_analyst":               "analyse_impact",
    "response_agent":             "execute_response",
    "verification_handoff_agent": "verify_and_handoff",
}

# Tool entry-point files for cross-reference
_TOOL_ENTRY_POINTS = {
    "investigate_case":  ROOT / "tools" / "investigator_pkg" / "investigate_case.py",
    "analyse_impact":    ROOT / "tools" / "analyst_pkg"      / "analyse_impact.py",
    "execute_response":  ROOT / "tools" / "response_pkg"     / "execute_response.py",
    "verify_and_handoff": ROOT / "tools" / "verifier_pkg"    / "verify_and_handoff.py",
}

_ADK_REQUIRED_FIELDS = {"spec_version", "kind", "name", "llm", "style", "description", "instructions"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(path: Path) -> dict[str, Any]:
    """Load and parse a YAML file; raise AssertionError on failure."""
    assert path.exists(), f"Agent YAML not found: {path}"
    with path.open(encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    assert isinstance(doc, dict), f"Expected a YAML mapping in {path.name}, got {type(doc).__name__}"
    return doc


def _load_all_five() -> dict[str, dict[str, Any]]:
    """Return all five agent specs keyed by agent name."""
    specs: dict[str, dict[str, Any]] = {}
    for name, path in _SPECIALIST_FILES.items():
        specs[name] = _load(path)
    specs["orchestrator_agent"] = _load(_ORCHESTRATOR_FILE)
    return specs


# ===========================================================================
# 1. YAML parseability — all five files must load without errors
# ===========================================================================

class TestYamlParseability:

    def test_security_investigator_parses(self):
        _load(_SPECIALIST_FILES["security_investigator"])

    def test_risk_analyst_parses(self):
        _load(_SPECIALIST_FILES["risk_analyst"])

    def test_response_agent_parses(self):
        _load(_SPECIALIST_FILES["response_agent"])

    def test_verification_handoff_agent_parses(self):
        _load(_SPECIALIST_FILES["verification_handoff_agent"])

    def test_orchestrator_agent_parses(self):
        _load(_ORCHESTRATOR_FILE)

    def test_original_risk_analysis_agent_still_parses(self):
        """The original preserved agent must still be valid YAML."""
        _load(_ORIGINAL_FILE)


# ===========================================================================
# 2. Required ADK fields — every native agent spec must have them
# ===========================================================================

class TestRequiredFields:

    @pytest.mark.parametrize("agent_name,path", list(_SPECIALIST_FILES.items()) + [
        ("orchestrator_agent", _ORCHESTRATOR_FILE)
    ])
    def test_all_required_fields_present(self, agent_name, path):
        """Every agent spec must contain all ADK-required top-level fields."""
        spec = _load(path)
        missing = _ADK_REQUIRED_FIELDS - set(spec.keys())
        assert not missing, (
            f"{path.name} is missing required ADK fields: {sorted(missing)}"
        )

    @pytest.mark.parametrize("agent_name,path", list(_SPECIALIST_FILES.items()) + [
        ("orchestrator_agent", _ORCHESTRATOR_FILE)
    ])
    def test_spec_version_is_v1(self, agent_name, path):
        spec = _load(path)
        assert spec["spec_version"] == "v1", (
            f"{path.name}: spec_version must be 'v1', got {spec['spec_version']!r}"
        )

    @pytest.mark.parametrize("agent_name,path", list(_SPECIALIST_FILES.items()) + [
        ("orchestrator_agent", _ORCHESTRATOR_FILE)
    ])
    def test_kind_is_native(self, agent_name, path):
        spec = _load(path)
        assert spec["kind"] == "native", (
            f"{path.name}: kind must be 'native', got {spec['kind']!r}"
        )

    @pytest.mark.parametrize("agent_name,path", list(_SPECIALIST_FILES.items()) + [
        ("orchestrator_agent", _ORCHESTRATOR_FILE)
    ])
    def test_name_field_is_non_empty_string(self, agent_name, path):
        spec = _load(path)
        assert isinstance(spec["name"], str) and spec["name"].strip(), (
            f"{path.name}: 'name' must be a non-empty string"
        )


# ===========================================================================
# 3. All five agents use react_core style
#    (from §4 of the recovery plan — test_all_five_agents_use_react_core)
# ===========================================================================

class TestReactCoreStyle:

    def test_all_five_agents_use_react_core(self):
        """All five agent specs must use style: react_core (required for
        multi-agent collaboration with the gpt-oss-120b LLM)."""
        specs = _load_all_five()
        failures = []
        for name, spec in specs.items():
            if spec.get("style") != "react_core":
                failures.append(f"{name}: style={spec.get('style')!r}")
        assert not failures, (
            "The following agents do not use style: react_core:\n"
            + "\n".join(f"  {f}" for f in failures)
        )


# ===========================================================================
# 4. Orchestrator has four collaborators and no tools
#    (from §4 — test_orchestrator_has_four_collaborators_and_no_tools)
# ===========================================================================

class TestOrchestratorStructure:

    def test_orchestrator_has_no_collaborators(self):
        """Orchestrator must have an empty collaborators list.

        The four specialist agents are invoked exclusively by the
        civic_shield_pipeline flow engine.  Listing them as collaborators
        gives the LLM a direct bypass route that overrides the flow — the
        bypass was confirmed in live C09/C10 traces and is the root cause of
        the stage-skipping defect.  Removing collaborators closes that route
        architecturally.
        """
        spec = _load(_ORCHESTRATOR_FILE)
        collaborators = spec.get("collaborators", [])
        assert collaborators == [] or collaborators is None, (
            f"Orchestrator must have no collaborators (flow engine handles "
            f"all inter-agent calls); found: {collaborators}"
        )

    def test_orchestrator_has_pipeline_tools(self):
        """Orchestrator must declare civic_shield_pipeline and its status tool.

        The orchestrator invokes specialists via the flow rather than by
        direct collaborator delegation, requiring both the pipeline tool and
        the flow-status polling tool to be present.
        """
        spec = _load(_ORCHESTRATOR_FILE)
        tools = spec.get("tools") or []
        assert "civic_shield_pipeline" in tools, (
            f"Orchestrator must list civic_shield_pipeline in tools; found: {tools}"
        )
        assert "i__get_flow_status_intrinsic_tool__" in tools, (
            f"Orchestrator must list i__get_flow_status_intrinsic_tool__ in tools; found: {tools}"
        )


# ===========================================================================
# 5. Specialist agents have no collaborators
#    (from §4 — test_specialist_agents_have_no_collaborators)
# ===========================================================================

class TestSpecialistStructure:

    @pytest.mark.parametrize("agent_name,path", list(_SPECIALIST_FILES.items()))
    def test_specialist_has_no_collaborators(self, agent_name, path):
        """Each specialist agent must have collaborators: [] (no sub-delegation)."""
        spec = _load(path)
        collaborators = spec.get("collaborators", [])
        assert collaborators == [] or collaborators is None, (
            f"{path.name} must have no collaborators; found: {collaborators}"
        )

    @pytest.mark.parametrize("agent_name,path", list(_SPECIALIST_FILES.items()))
    def test_specialist_has_exactly_one_tool(self, agent_name, path):
        """Each specialist must have exactly one tool."""
        spec = _load(path)
        tools = spec.get("tools", [])
        assert len(tools) == 1, (
            f"{path.name} must have exactly 1 tool, found {len(tools)}: {tools}"
        )


# ===========================================================================
# 6. Collaborator names match specialist agent name fields
#    (from §4 — test_orchestrator_collaborator_names_match_agent_names)
# ===========================================================================

class TestCollaboratorGraphConsistency:

    def test_orchestrator_has_empty_collaborator_list(self):
        """orchestrator_agent.collaborators must be empty.

        Specialist agent names are intentionally NOT listed as collaborators.
        They are invoked only by the civic_shield_pipeline flow engine.
        This test guards against accidental re-introduction of the collaborator
        bypass that caused the C09/C10 stage-skipping regression.
        """
        orch_spec = _load(_ORCHESTRATOR_FILE)
        collaborators = orch_spec.get("collaborators", [])
        assert not collaborators, (
            f"orchestrator_agent must have no collaborators — found: {collaborators}. "
            f"Specialist agents must only be reachable via civic_shield_pipeline."
        )


# ===========================================================================
# 7. Specialist tool names match @tool entry-point function names
#    (from §4 — test_specialist_tools_match_entrypoint_function_names)
# ===========================================================================

class TestToolNameConsistency:

    @pytest.mark.parametrize("agent_name,expected_tool", list(_EXPECTED_TOOLS.items()))
    def test_specialist_tool_matches_expected_name(self, agent_name, expected_tool):
        """The tool listed in each specialist YAML must match the expected @tool
        function name from the M1 tool packages."""
        path = _SPECIALIST_FILES[agent_name]
        spec = _load(path)
        tools = spec.get("tools", [])
        assert expected_tool in tools, (
            f"{path.name}: expected tool '{expected_tool}' not found in tools: {tools}"
        )

    @pytest.mark.parametrize("tool_name,entry_point", list(_TOOL_ENTRY_POINTS.items()))
    def test_tool_function_exists_in_entry_point_file(self, tool_name, entry_point):
        """The @tool function named in each specialist YAML must have a matching
        'def <tool_name>(' declaration in its M1 entry-point file."""
        assert entry_point.exists(), f"Entry-point file not found: {entry_point}"
        source = entry_point.read_text(encoding="utf-8")
        assert f"def {tool_name}(" in source, (
            f"Entry-point {entry_point.name} does not define 'def {tool_name}('.\n"
            f"Tool name in YAML must match the decorated function name exactly."
        )


# ===========================================================================
# 8. Safety requirements — Orchestrator instructions contain key guardrails
# ===========================================================================

class TestOrchestratorSafetyRequirements:

    def _instructions(self) -> str:
        return _load(_ORCHESTRATOR_FILE).get("instructions", "")

    def test_orchestrator_instructions_mention_notification_gate(self):
        """Orchestrator instructions must mention emitting a notification before
        response_agent when notify_first is true."""
        instr = self._instructions()
        assert "notify_first" in instr or "notification" in instr.lower(), (
            "Orchestrator instructions must reference the notification gate "
            "(notify_first check before calling response_agent)."
        )

    def test_orchestrator_instructions_mention_human_closure(self):
        """Orchestrator instructions must remind the user that human closure is
        always required."""
        instr = self._instructions().lower()
        assert "human" in instr and ("closure" in instr or "approval" in instr), (
            "Orchestrator instructions must mention that human closure/approval "
            "is always required."
        )

    def test_orchestrator_instructions_mention_public_restricted_guard(self):
        """Orchestrator instructions must reference the public_restricted guard
        or restricted data safety."""
        instr = self._instructions().lower()
        assert "public_restricted" in instr or "restricted" in instr, (
            "Orchestrator instructions must reference the public_restricted "
            "safety constraint."
        )

    def test_response_agent_instructions_list_all_six_auth_invariants(self):
        """Response agent instructions must reference all six authorization
        invariants by their key concepts."""
        spec   = _load(_SPECIALIST_FILES["response_agent"])
        instr  = spec.get("instructions", "").lower()
        checks = {
            "CFG-LOGGING":          "cfg-logging",
            "allowlist":            "allowlist",
            "sandbox_only":         "sandbox_only",
            "expiry":               "expired",
            "public_restricted":    "public_restricted",
            "retry limit":          "retry",
        }
        missing = [label for label, keyword in checks.items() if keyword not in instr]
        assert not missing, (
            "response_agent instructions are missing references to these "
            f"authorization invariants: {missing}"
        )

    def test_verification_handoff_instructions_mention_independent_verification(self):
        """Verifier instructions must state that the tool success message alone
        does not establish resolution."""
        spec  = _load(_SPECIALIST_FILES["verification_handoff_agent"])
        instr = spec.get("instructions", "").lower()
        assert "success" in instr and ("not" in instr or "alone" in instr or "independent" in instr), (
            "verification_handoff_agent instructions must state that a tool "
            "success message alone does not establish resolution."
        )


# ===========================================================================
# 9. Original risk_analysis_agent is preserved and unchanged
# ===========================================================================

class TestOriginalAgentPreserved:

    def test_original_agent_name_unchanged(self):
        """agents/risk_analysis_agent.yaml must keep name: risk_analysis_agent."""
        spec = _load(_ORIGINAL_FILE)
        assert spec["name"] == "risk_analysis_agent", (
            f"Original agent name changed: got {spec['name']!r}"
        )

    def test_original_agent_has_analyze_risk_cases_tool(self):
        """agents/risk_analysis_agent.yaml must keep the analyze_risk_cases tool."""
        spec  = _load(_ORIGINAL_FILE)
        tools = spec.get("tools", [])
        assert "analyze_risk_cases" in tools, (
            f"Original agent must retain the analyze_risk_cases tool; found: {tools}"
        )

    def test_original_agent_has_no_collaborators(self):
        """The original single agent must not reference the five-agent collaborators."""
        spec         = _load(_ORIGINAL_FILE)
        collaborators = spec.get("collaborators", [])
        assert not collaborators, (
            f"Original risk_analysis_agent must have no collaborators; found: {collaborators}"
        )
