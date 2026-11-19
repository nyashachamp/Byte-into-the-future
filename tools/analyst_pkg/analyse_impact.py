"""Watsonx Orchestrate @tool — Risk & Dependency Analyst specialist.

Receives the investigation result from the Security Investigator and computes
the priority score, severity, service impact, and notification requirements.

Entry point for:
    orchestrate tools import -k python -f tools/analyst_pkg/analyse_impact.py \\
        --package-root tools/analyst_pkg
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


_pipeline_mod = _load_bundled("_an_pipeline", "pipeline.py")
_analyst_mod  = _load_bundled("_an_analyst",  "agents/analyst.py")

load_dataset        = _pipeline_mod.load_dataset
_analyse_impact_fn  = _analyst_mod.analyse_impact

_DATASET_PATH = _PKG_ROOT / "data" / "public-service-risk-v1.json"


@tool(permission=ToolPermission.READ_ONLY)
def analyse_impact(case_id: str, investigator_result: str) -> dict[str, Any]:
    """Compute risk score and service-dependency impact for a confirmed finding.

    Accepts the JSON-serialised result from the Security Investigator, re-loads
    the case from the bundled dataset for case isolation, and returns the priority
    score, severity band, notification flag, and affected public services.

    All actions are in-memory simulations only. No real infrastructure is modified.

    Args:
        case_id (str): The case identifier, e.g. "C03".
        investigator_result (str): JSON string returned by the investigate_case tool.
    Returns:
        dict: analysis result with keys score, severity, notify_first,
              public_restricted, service_ids, and affected_public_service.
              On input/dataset error, returns a dict with assessment="error".
    """
    # --- Deserialise prior-stage result ---
    try:
        inv: dict[str, Any] = json.loads(investigator_result)
    except (json.JSONDecodeError, TypeError) as exc:
        return {"assessment": "error", "error": f"investigator_result is not valid JSON: {exc}"}

    try:
        dataset = load_dataset(_DATASET_PATH)
        assets_index   = {item["id"]: item for item in dataset["assets"]}
        services_index = {item["id"]: item for item in dataset["services"]}
        policy = dataset["policy"]

        cases = {c["id"]: c for c in dataset["cases"]}
        if case_id not in cases:
            return {"assessment": "error", "error": f"case_id '{case_id}' not found in dataset"}

        case  = cases[case_id]
        asset = assets_index[case["asset_id"]]

        return _analyse_impact_fn(
            inv=inv,
            services=services_index,
            asset=asset,
            policy=policy,
        )
    except Exception as exc:  # noqa: BLE001
        return {"assessment": "error", "error": str(exc)}
