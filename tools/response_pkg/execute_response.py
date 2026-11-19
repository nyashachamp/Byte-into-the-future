"""Watsonx Orchestrate @tool — Response Agent specialist.

Receives the investigation and analyst results, checks every authorization guard,
and executes the allowlisted simulated action if — and only if — all guards pass.

Authorization safeguards live exclusively in this tool package (agents/response_agent.py)
and cannot be bypassed by any other agent or the Orchestrator.

Entry point for:
    orchestrate tools import -k python -f tools/response_pkg/execute_response.py \\
        --package-root tools/response_pkg
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

# ---------------------------------------------------------------------------
# Bundle-relative imports (resolved against __file__ so this works both
# offline in tests and inside the WXO package bundle at deploy time).
# ---------------------------------------------------------------------------

_PKG_ROOT = Path(__file__).parent


def _load_bundled(module_name: str, rel_path: str):
    """Load a module from a path relative to this file's directory."""
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, _PKG_ROOT / rel_path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


_pipeline_mod       = _load_bundled("_resp_pipeline",      "pipeline.py")
_response_agent_mod = _load_bundled("_resp_response_agent", "agents/response_agent.py")

load_dataset        = _pipeline_mod.load_dataset
_execute_response_fn = _response_agent_mod.execute_response  # all 6 auth guards

_DATASET_PATH = _PKG_ROOT / "data" / "public-service-risk-v1.json"


@tool(permission=ToolPermission.READ_ONLY)
def execute_response(
    case_id: str,
    investigator_result: str,
    analyst_result: str,
) -> dict[str, Any]:
    """Check authorization and execute the allowlisted simulated action for one case.

    Accepts the JSON-serialised results from the Security Investigator and the
    Risk & Dependency Analyst, re-loads the case from the bundled dataset for case
    isolation, and applies all six authorization invariants before any action.

    Authorization safeguards (all must hold for an action to be taken):
      1. Exactly one rule is violated, and it is CFG-LOGGING.
      2. "enable_audit_logging" is in the policy allowlisted_simulated_actions.
      3. "enable_audit_logging" is in the case authorization allowed_actions.
      4. case authorization sandbox_only is exactly True (strict bool).
      5. The authorization has not expired relative to the simulation clock.
      6. public_restricted is False (restricted data exposure is never auto-corrected).

    All actions are in-memory simulations only. No real infrastructure is modified.

    Args:
        case_id (str): The case identifier, e.g. "C03".
        investigator_result (str): JSON string returned by the investigate_case tool.
        analyst_result (str): JSON string returned by the analyse_impact tool.
    Returns:
        dict: response result with keys action_taken, action_attempts, action_result,
              post_state, events, handoff, and outcome.
              On input/dataset error, returns a dict with assessment="error".
    """
    # --- Deserialise prior-stage results ---
    try:
        inv: dict[str, Any] = json.loads(investigator_result)
    except (json.JSONDecodeError, TypeError) as exc:
        return {"assessment": "error", "error": f"investigator_result is not valid JSON: {exc}"}

    try:
        an: dict[str, Any] = json.loads(analyst_result)
    except (json.JSONDecodeError, TypeError) as exc:
        return {"assessment": "error", "error": f"analyst_result is not valid JSON: {exc}"}

    try:
        dataset = load_dataset(_DATASET_PATH)
        policy = dataset["policy"]
        clock  = dataset["simulation_clock"]

        cases = {c["id"]: c for c in dataset["cases"]}
        if case_id not in cases:
            return {"assessment": "error", "error": f"case_id '{case_id}' not found in dataset"}

        case = cases[case_id]

        return _execute_response_fn(
            inv=inv,
            an=an,
            case=case,
            policy=policy,
            clock=clock,
        )
    except Exception as exc:  # noqa: BLE001
        return {"assessment": "error", "error": str(exc)}
