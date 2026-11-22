"""Watsonx Orchestrate @tool — Verification & Handoff Agent specialist.

Independently verifies the post-action state (without trusting the tool's own
success/failure report), determines the final outcome and lifecycle status, and
assembles the human handoff packet.

Entry point for:
    orchestrate tools import -k python -f tools/verifier_pkg/verify_and_handoff.py \\
        --package-root tools/verifier_pkg
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


_pipeline_mod   = _load_bundled("_ver_pipeline",  "pipeline.py")
_verifier_mod   = _load_bundled("_ver_verifier",   "agents/verifier.py")

load_dataset              = _pipeline_mod.load_dataset
_verify_and_handoff_fn    = _verifier_mod.verify_and_prepare_handoff

_DATASET_PATH = _PKG_ROOT / "data" / "public-service-risk-v1.json"


@tool(permission=ToolPermission.READ_ONLY)
def verify_and_handoff(
    case_id: str,
    investigator_result: str,
    analyst_result: str,
    response_result: str,
) -> dict[str, Any]:
    """Verify post-action state and assemble the final human handoff packet.

    Accepts the JSON-serialised results from all three prior specialists, re-loads
    the case from the bundled dataset for case isolation, and independently verifies
    whether the post-action state matches the expected outcome before determining
    the final lifecycle status and human work items.

    Key invariant: a tool success message alone does NOT establish resolution.
    verification="passed" only when post_state["audit_logging_enabled"] is exactly True.

    All actions are in-memory simulations only. No real infrastructure is modified.

    Args:
        case_id (str): The case identifier, e.g. "C03".
        investigator_result (str): JSON string returned by the investigate_case tool.
        analyst_result (str): JSON string returned by the analyse_impact tool.
        response_result (str): JSON string returned by the execute_response tool.
    Returns:
        dict: verification result with keys verification_result, outcome,
              handoff_required, human_intervention, completed_ai_work,
              lifecycle_status, and events.
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
        resp: dict[str, Any] = json.loads(response_result)
    except (json.JSONDecodeError, TypeError) as exc:
        return {"assessment": "error", "error": f"response_result is not valid JSON: {exc}"}

    try:
        dataset = load_dataset(_DATASET_PATH)

        cases = {c["id"]: c for c in dataset["cases"]}
        if case_id not in cases:
            return {"assessment": "error", "error": f"case_id '{case_id}' not found in dataset"}

        case = cases[case_id]

        return _verify_and_handoff_fn(
            inv=inv,
            an=an,
            resp=resp,
            case=case,
        )
    except Exception as exc:  # noqa: BLE001
        return {"assessment": "error", "error": str(exc)}
