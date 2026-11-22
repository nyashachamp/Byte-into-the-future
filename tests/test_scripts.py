"""Offline tests for the M3 PowerShell deployment scripts.

Tests verify structural invariants of the three scripts by static analysis
(text parsing).  No WXO runtime, no orchestrate CLI, and no PowerShell
interpreter is required.

Invariants tested:
  - Import order: tools before agents, specialists before Orchestrator
  - Dry-run mode: -DryRun switch declared; all orchestrate calls are
    wrapped inside Invoke-Step (which respects DryRun)
  - Rollback safeguards: delete-five-agents.ps1 does NOT reference the
    protected names 'risk_analysis_agent' or 'analyze_risk_cases' in any
    removal command
  - Full-cleanup order: delete-all.ps1 removes Orchestrator before
    specialist agents before original agent; tools removed after agents
  - Preflight: import-all.ps1 checks for venv and required files before
    calling orchestrate

Run:
    python -m pytest tests/test_scripts.py -v
        (from the repo root, any Python interpreter)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT    = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

IMPORT_SCRIPT        = SCRIPTS / "import-all.ps1"
DELETE_ALL_SCRIPT    = SCRIPTS / "delete-all.ps1"
DELETE_FIVE_SCRIPT   = SCRIPTS / "delete-five-agents.ps1"


# ---------------------------------------------------------------------------
# Helper: load a script and collect all non-comment, non-whitespace lines
# ---------------------------------------------------------------------------

def _lines(path: Path) -> list[str]:
    assert path.exists(), f"Script not found: {path}"
    return path.read_text(encoding="utf-8").splitlines()


def _effective_lines(path: Path) -> list[str]:
    """Strip blank and pure-comment lines; preserve inline # comments."""
    result = []
    for line in _lines(path):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            result.append(line)
    return result


def _find_positions(lines: list[str], patterns: list[str]) -> list[int]:
    """Return the first line index (0-based) for each pattern, in order found."""
    positions: list[int] = []
    for pat in patterns:
        for i, line in enumerate(lines):
            if pat in line:
                positions.append(i)
                break
        else:
            positions.append(-1)  # not found
    return positions


# ===========================================================================
# import-all.ps1 tests
# ===========================================================================

class TestImportScript:

    def test_script_exists(self):
        assert IMPORT_SCRIPT.exists(), f"Not found: {IMPORT_SCRIPT}"

    def test_dryrun_param_declared(self):
        """Script must declare a [switch]$DryRun parameter."""
        src = IMPORT_SCRIPT.read_text(encoding="utf-8")
        assert "[switch]$DryRun" in src or "[switch] $DryRun" in src, (
            "import-all.ps1 must declare a [switch]$DryRun parameter"
        )

    def test_invoke_step_function_defined(self):
        """Script must define an Invoke-Step function that respects DryRun."""
        src = IMPORT_SCRIPT.read_text(encoding="utf-8")
        assert "function Invoke-Step" in src, (
            "import-all.ps1 must define an Invoke-Step helper"
        )
        assert "$DryRun" in src, (
            "Invoke-Step must reference $DryRun"
        )

    def test_preflight_checks_venv(self):
        """Script must check that venv exists before importing."""
        src = IMPORT_SCRIPT.read_text(encoding="utf-8")
        assert "venv" in src and "Test-Path" in src, (
            "import-all.ps1 must include a preflight check for the venv"
        )

    def test_preflight_checks_agent_files(self):
        """Script must check that required agent YAML files exist."""
        src = IMPORT_SCRIPT.read_text(encoding="utf-8")
        for f in [
            "security_investigator_agent.yaml",
            "risk_analyst_agent.yaml",
            "response_agent.yaml",
            "verification_handoff_agent.yaml",
            "orchestrator_agent.yaml",
        ]:
            assert f in src, (
                f"import-all.ps1 preflight must reference agent file: {f}"
            )

    def test_preflight_checks_tool_files(self):
        """Script must check that required tool entry-point files exist."""
        src = IMPORT_SCRIPT.read_text(encoding="utf-8")
        for f in [
            "investigate_case.py",
            "analyse_impact.py",
            "execute_response.py",
            "verify_and_handoff.py",
            "analyze_risk_cases.py",
        ]:
            assert f in src, (
                f"import-all.ps1 preflight must reference tool file: {f}"
            )

    def test_all_four_specialist_tools_imported(self):
        """Script must import all four specialist tool packages."""
        src = IMPORT_SCRIPT.read_text(encoding="utf-8")
        for tool in [
            "investigate_case.py",
            "analyse_impact.py",
            "execute_response.py",
            "verify_and_handoff.py",
        ]:
            assert tool in src, (
                f"import-all.ps1 must import tool: {tool}"
            )

    def test_original_tool_imported(self):
        """Script must (re-)import the original analyze_risk_cases tool."""
        src = IMPORT_SCRIPT.read_text(encoding="utf-8")
        assert "analyze_risk_cases.py" in src, (
            "import-all.ps1 must import the original analyze_risk_cases tool"
        )

    def test_all_five_agents_imported(self):
        """Script must import all five agent YAML files."""
        src = IMPORT_SCRIPT.read_text(encoding="utf-8")
        for agent_file in [
            "security_investigator_agent.yaml",
            "risk_analyst_agent.yaml",
            "response_agent.yaml",
            "verification_handoff_agent.yaml",
            "orchestrator_agent.yaml",
            "risk_analysis_agent.yaml",
        ]:
            assert agent_file in src, (
                f"import-all.ps1 must import agent file: {agent_file}"
            )

    def test_tools_imported_before_agents(self):
        """All tool imports must appear before any agent import in the script."""
        lines = _lines(IMPORT_SCRIPT)
        # The scripts use Invoke-Step arrays; look for the token 'tools', 'import'
        # or the string 'tools import' (both forms are accepted).
        tool_lines = [
            i for i, l in enumerate(lines)
            if ("'tools', 'import'" in l or '"tools", "import"' in l
                or "tools import" in l)
        ]
        agent_lines = [
            i for i, l in enumerate(lines)
            if ("'agents', 'import'" in l or '"agents", "import"' in l
                or "agents import" in l)
        ]
        assert tool_lines, "No tool import lines found in import-all.ps1"
        assert agent_lines, "No agent import lines found in import-all.ps1"
        assert max(tool_lines) < min(agent_lines), (
            "All tool imports must come before any agent imports.\n"
            f"  Last tool import at line {max(tool_lines)+1}, "
            f"first agent import at line {min(agent_lines)+1}"
        )

    def test_orchestrator_imported_last_among_agents(self):
        """orchestrator_agent.yaml must be imported after all four specialist agents.
        Only consider lines that are actual import calls (contain 'agents', 'import'
        or 'agents import'), not lines in comments or the YAML file list."""
        lines = _lines(IMPORT_SCRIPT)

        # Lines that perform an agent import (Invoke-Step or direct)
        import_lines = [
            (i, l) for i, l in enumerate(lines)
            if ("'agents', 'import'" in l or '"agents", "import"' in l
                or "agents import" in l)
        ]
        assert import_lines, "No agent import calls found in import-all.ps1"

        # Find positions of each import call that mentions each file
        def _import_pos(yaml_name: str) -> int:
            for i, l in import_lines:
                if yaml_name in l:
                    return i
            # Check surrounding lines (the yaml filename may be on the next line)
            for idx, (i, _) in enumerate(import_lines):
                # look at context: scan ±3 lines around each import call
                for offset in range(0, 4):
                    j = i + offset
                    if j < len(lines) and yaml_name in lines[j]:
                        return j
            return -1

        specialist_yaml_patterns = [
            "security_investigator_agent.yaml",
            "risk_analyst_agent.yaml",
            "response_agent.yaml",
            "verification_handoff_agent.yaml",
        ]
        orchestrator_pattern = "orchestrator_agent.yaml"

        orch_pos = _import_pos(orchestrator_pattern)
        assert orch_pos != -1, "orchestrator_agent.yaml import not found in import-all.ps1"

        for pat in specialist_yaml_patterns:
            pos = _import_pos(pat)
            assert pos != -1, f"'{pat}' import not found in import-all.ps1"
            assert pos < orch_pos, (
                f"'{pat}' (line {pos+1}) must appear before orchestrator_agent.yaml "
                f"(line {orch_pos+1})"
            )

    def test_all_orchestrate_calls_wrapped_in_invoke_step(self):
        """Every 'orchestrate' CLI call in the import script must be inside
        an Invoke-Step array — not called directly — so DryRun works."""
        src = IMPORT_SCRIPT.read_text(encoding="utf-8")
        # Look for lines that call 'orchestrate' directly (not via Invoke-Step)
        # Pattern: line containing bare 'orchestrate tools' or 'orchestrate agents'
        # but NOT inside an Invoke-Step call.
        bare_calls = []
        for i, line in enumerate(src.splitlines(), 1):
            stripped = line.strip()
            # Skip comment lines
            if stripped.startswith("#"):
                continue
            # A bare call looks like: orchestrate tools ... or orchestrate agents ...
            # An Invoke-Step call looks like: 'orchestrate', 'tools', ...
            if re.search(r"^\s*orchestrate\s+(tools|agents)\b", line):
                bare_calls.append((i, line.rstrip()))
        assert not bare_calls, (
            "The following lines call orchestrate directly instead of via Invoke-Step "
            "(DryRun would not suppress them):\n"
            + "\n".join(f"  line {n}: {l}" for n, l in bare_calls)
        )

    def test_offline_tests_invoked_in_step2(self):
        """Step 2 must invoke pytest against test_sync.py and test_agent_yaml.py."""
        src = IMPORT_SCRIPT.read_text(encoding="utf-8")
        assert "test_sync.py" in src, (
            "import-all.ps1 must run tests/test_sync.py as part of offline checks"
        )
        assert "test_agent_yaml.py" in src, (
            "import-all.ps1 must run tests/test_agent_yaml.py as part of offline checks"
        )


# ===========================================================================
# delete-five-agents.ps1 (rollback) tests
# ===========================================================================

class TestRollbackScript:

    def test_script_exists(self):
        assert DELETE_FIVE_SCRIPT.exists(), f"Not found: {DELETE_FIVE_SCRIPT}"

    def test_dryrun_param_declared(self):
        src = DELETE_FIVE_SCRIPT.read_text(encoding="utf-8")
        assert "[switch]$DryRun" in src or "[switch] $DryRun" in src, (
            "delete-five-agents.ps1 must declare a [switch]$DryRun parameter"
        )

    def test_does_not_remove_original_agent(self):
        """Rollback script must NOT contain a remove command for risk_analysis_agent."""
        src = DELETE_FIVE_SCRIPT.read_text(encoding="utf-8")
        # Look for lines that could remove risk_analysis_agent (not in comments)
        for i, line in enumerate(src.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "risk_analysis_agent" in line and "remove" in line.lower():
                pytest.fail(
                    f"delete-five-agents.ps1 line {i} removes risk_analysis_agent "
                    f"(must NOT be removed by rollback script):\n  {line.rstrip()}"
                )

    def test_does_not_remove_original_tool(self):
        """Rollback script must NOT contain a remove command for analyze_risk_cases."""
        src = DELETE_FIVE_SCRIPT.read_text(encoding="utf-8")
        for i, line in enumerate(src.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "analyze_risk_cases" in line and "remove" in line.lower():
                pytest.fail(
                    f"delete-five-agents.ps1 line {i} removes analyze_risk_cases "
                    f"(must NOT be removed by rollback script):\n  {line.rstrip()}"
                )

    def test_removes_all_five_new_agents(self):
        """Rollback script must remove all five new agents by name."""
        src = DELETE_FIVE_SCRIPT.read_text(encoding="utf-8")
        for agent_name in [
            "orchestrator_agent",
            "verification_handoff_agent",
            "response_agent",
            "risk_analyst",
            "security_investigator",
        ]:
            assert agent_name in src, (
                f"delete-five-agents.ps1 must remove agent: {agent_name}"
            )

    def test_removes_all_four_specialist_tools(self):
        """Rollback script must remove all four specialist tools by name."""
        src = DELETE_FIVE_SCRIPT.read_text(encoding="utf-8")
        for tool_name in [
            "verify_and_handoff",
            "execute_response",
            "analyse_impact",
            "investigate_case",
        ]:
            assert tool_name in src, (
                f"delete-five-agents.ps1 must remove tool: {tool_name}"
            )

    def test_orchestrator_removed_before_specialist_agents(self):
        """Orchestrator must be removed before specialist agents in rollback."""
        lines = _lines(DELETE_FIVE_SCRIPT)
        orch_lines = [i for i, l in enumerate(lines) if "orchestrator_agent" in l and "remove" in l]
        spec_lines = [
            i for i, l in enumerate(lines)
            if any(n in l for n in ["security_investigator", "risk_analyst",
                                     "response_agent", "verification_handoff_agent"])
            and "remove" in l
        ]
        if orch_lines and spec_lines:
            assert min(orch_lines) < min(spec_lines), (
                "Orchestrator must be removed (line "
                f"{min(orch_lines)+1}) before specialist agents (first at line {min(spec_lines)+1})"
            )

    def test_agents_removed_before_tools(self):
        """Agent removals must precede tool removals in rollback script."""
        lines = _lines(DELETE_FIVE_SCRIPT)
        agent_remove_lines = [
            i for i, l in enumerate(lines)
            if ("'agents', 'remove'" in l or '"agents", "remove"' in l
                or "agents remove" in l)
        ]
        tool_remove_lines = [
            i for i, l in enumerate(lines)
            if ("'tools', 'remove'" in l or '"tools", "remove"' in l
                or "tools remove" in l)
        ]
        assert agent_remove_lines, "No agent remove calls in delete-five-agents.ps1"
        assert tool_remove_lines,  "No tool remove calls in delete-five-agents.ps1"
        assert max(agent_remove_lines) < min(tool_remove_lines), (
            "All agent removals must come before tool removals in rollback script"
        )

    def test_protected_names_mentioned_in_synopsis(self):
        """Rollback script must explicitly state the protected names in its header."""
        src = DELETE_FIVE_SCRIPT.read_text(encoding="utf-8")
        assert "risk_analysis_agent" in src, (
            "delete-five-agents.ps1 must mention 'risk_analysis_agent' "
            "in its documentation (even if only in comments/synopsis)"
        )
        assert "analyze_risk_cases" in src, (
            "delete-five-agents.ps1 must mention 'analyze_risk_cases' "
            "in its documentation"
        )

    def test_invoke_step_function_defined(self):
        src = DELETE_FIVE_SCRIPT.read_text(encoding="utf-8")
        assert "function Invoke-Step" in src, (
            "delete-five-agents.ps1 must define an Invoke-Step helper"
        )


# ===========================================================================
# delete-all.ps1 (full cleanup) tests
# ===========================================================================

class TestDeleteAllScript:

    def test_script_exists(self):
        assert DELETE_ALL_SCRIPT.exists(), f"Not found: {DELETE_ALL_SCRIPT}"

    def test_dryrun_param_declared(self):
        src = DELETE_ALL_SCRIPT.read_text(encoding="utf-8")
        assert "[switch]$DryRun" in src or "[switch] $DryRun" in src, (
            "delete-all.ps1 must declare a [switch]$DryRun parameter"
        )

    def _remove_line(self, lines: list[str], pattern: str) -> int:
        """Return 0-based index of the Invoke-Step call that removes 'pattern'.

        The agent/tool name may appear on a separate line from 'remove' inside
        an Invoke-Step array literal, so we scan a 3-line window around each
        'agents remove' or 'tools remove' call.
        """
        remove_call_lines = [
            i for i, l in enumerate(lines)
            if ("'agents', 'remove'" in l or "'tools', 'remove'" in l
                or "agents remove" in l or "tools remove" in l)
            and not l.strip().startswith("#")
        ]
        for i in remove_call_lines:
            # Check this line and the next 2 lines for the pattern
            for offset in range(3):
                j = i + offset
                if j < len(lines) and pattern in lines[j]:
                    return i
        return -1

    def _remove_line_for_specialist(self, lines: list[str], names: list[str]) -> int:
        """Return the first remove-call line that removes any of the given names."""
        for name in names:
            pos = self._remove_line(lines, name)
            if pos != -1:
                return pos
        return -1

    def test_removes_orchestrator_first(self):
        """Orchestrator must be removed before specialist agents."""
        lines = _lines(DELETE_ALL_SCRIPT)
        orch_pos = self._remove_line(lines, "orchestrator_agent")
        spec_pos = self._remove_line_for_specialist(lines, [
            "verification_handoff_agent", "response_agent",
            "risk_analyst", "security_investigator",
        ])
        assert orch_pos != -1, "orchestrator_agent not removed in delete-all.ps1"
        assert spec_pos != -1, "specialist agents not removed in delete-all.ps1"
        assert orch_pos < spec_pos, (
            f"Orchestrator (line {orch_pos+1}) must be removed before "
            f"specialist agents (first at line {spec_pos+1})"
        )

    def test_removes_original_agent_after_specialists(self):
        """risk_analysis_agent must be removed after all specialist agents."""
        lines = _lines(DELETE_ALL_SCRIPT)
        orig_pos = self._remove_line(lines, "risk_analysis_agent")
        spec_positions = [
            p for n in ["verification_handoff_agent", "response_agent",
                        "risk_analyst", "security_investigator"]
            for p in [self._remove_line(lines, n)] if p != -1
        ]
        assert orig_pos != -1, "risk_analysis_agent not removed in delete-all.ps1"
        assert spec_positions, "specialist agents not removed in delete-all.ps1"
        assert max(spec_positions) < orig_pos, (
            f"risk_analysis_agent (line {orig_pos+1}) must be removed AFTER "
            f"all specialist agents (last at line {max(spec_positions)+1})"
        )

    def test_agents_removed_before_tools(self):
        """Agent removals must all precede tool removals."""
        lines = _lines(DELETE_ALL_SCRIPT)
        agent_lines = [
            i for i, l in enumerate(lines)
            if ("'agents', 'remove'" in l or '"agents", "remove"' in l
                or "agents remove" in l)
        ]
        tool_lines = [
            i for i, l in enumerate(lines)
            if ("'tools', 'remove'" in l or '"tools", "remove"' in l
                or "tools remove" in l)
        ]
        assert agent_lines, "No agent remove calls in delete-all.ps1"
        assert tool_lines,  "No tool remove calls in delete-all.ps1"
        assert max(agent_lines) < min(tool_lines), (
            "All agent removals must come before tool removals in delete-all.ps1"
        )

    def test_references_rollback_only_script(self):
        """delete-all.ps1 must mention delete-five-agents.ps1 as the selective option."""
        src = DELETE_ALL_SCRIPT.read_text(encoding="utf-8")
        assert "delete-five-agents.ps1" in src, (
            "delete-all.ps1 must reference delete-five-agents.ps1 "
            "as the rollback-only alternative"
        )
