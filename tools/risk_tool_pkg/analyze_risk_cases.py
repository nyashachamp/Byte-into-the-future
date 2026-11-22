"""Watsonx Orchestrate @tool — public-service risk analysis.

Wraps the deterministic synthetic pipeline without duplicating logic.
All actions are in-memory simulations only. No real infrastructure is modified.
Results always require human review before closure.

This file is the entry point for:
    orchestrate tools import -k python -f tools/risk_tool_pkg/analyze_risk_cases.py \\
        --package-root tools/risk_tool_pkg
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

from pipeline import analyze  # resolved within the uploaded package bundle

_DATASET_PATH = Path(__file__).parent / "data" / "public-service-risk-v1.json"


@tool(permission=ToolPermission.READ_ONLY)
def analyze_risk_cases(case_ids: str) -> list[dict[str, Any]]:
    """Run synthetic risk-analysis cases from the public-service-risk-v1 dataset.

    All actions are in-memory simulations only. No real infrastructure is modified.
    Results always require human review before closure.

    Args:
        case_ids (str): Comma-separated case IDs to analyse, e.g. "C03,C05".
                        Pass "ALL" to run all 12 cases.
    Returns:
        list[dict[str, Any]]: One result dict per case containing assessment,
                              severity, score, outcome, action_taken,
                              verification_result, handoff_required, and
                              human_intervention fields.
    """
    ids = None if case_ids.strip().upper() == "ALL" else [c.strip() for c in case_ids.split(",")]
    results = analyze(_DATASET_PATH, ids)
    return [r.to_dict() for r in results]
