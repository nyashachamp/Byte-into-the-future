"""Watsonx Orchestrate @tool — Security Investigator specialist.

Validates the configuration snapshot for the requested case, applies exception
suppression, and compares observed settings against the approved baseline.

Entry point for:
    orchestrate tools import -k python -f tools/investigator_pkg/investigate_case.py \\
        --package-root tools/investigator_pkg
"""

from __future__ import annotations

import importlib.util
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


_pipeline_mod    = _load_bundled("_inv_pipeline",    "pipeline.py")
_investigator_mod = _load_bundled("_inv_investigator", "agents/investigator.py")

load_dataset = _pipeline_mod.load_dataset
investigate  = _investigator_mod.investigate

_DATASET_PATH = _PKG_ROOT / "data" / "public-service-risk-v1.json"


@tool(permission=ToolPermission.READ_ONLY)
def investigate_case(case_id: str) -> dict[str, Any]:
    """Validate the configuration snapshot and detect baseline violations for one case.

    Loads the case in isolation from the bundled public-service-risk-v1 dataset,
    checks the snapshot for required boolean fields, applies active exceptions, and
    compares observed settings against the approved baseline rules.

    All actions are in-memory simulations only. No real infrastructure is modified.

    Args:
        case_id (str): The case identifier to investigate, e.g. "C03".
    Returns:
        dict: investigation result with keys assessment, rules_violated, errors,
              evidence, and confidence.  On dataset/input error, returns a dict
              with assessment="error" and an "error" key describing the problem.
    """
    try:
        dataset = load_dataset(_DATASET_PATH)
        assets_index    = {item["id"]: item for item in dataset["assets"]}
        baselines_index = {item["id"]: item for item in dataset["baselines"]}
        clock = dataset["simulation_clock"]

        cases = {c["id"]: c for c in dataset["cases"]}
        if case_id not in cases:
            return {"assessment": "error", "error": f"case_id '{case_id}' not found in dataset"}

        case     = cases[case_id]
        asset    = assets_index[case["asset_id"]]
        baseline = baselines_index[case["baseline_id"]]

        return investigate(
            case=case,
            asset=asset,
            baseline=baseline,
            exceptions=dataset["exceptions"],
            clock=clock,
        )
    except Exception as exc:  # noqa: BLE001
        return {"assessment": "error", "error": str(exc)}
