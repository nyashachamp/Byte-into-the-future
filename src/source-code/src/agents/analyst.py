"""Risk & Dependency Analyst agent logic.

Responsibility: map the confirmed finding's asset to its linked public services,
compute the priority score using the dataset policy formula, determine whether an
immediate human notification is required before any action, and flag
restricted-synthetic public exposure.

This module contains the exact logic extracted from pipeline.analyze() lines
155-158 (score/notify/public_restricted), plus the service-name assembly and
severity derivation that feed into the final CaseResult.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Severity helper (shared with the pipeline; duplicated here for
# module independence)
# ---------------------------------------------------------------------------

def _severity(score: int | None, assessment: str) -> str:
    if assessment == "invalid_input":
        return "unknown"
    if score is None:
        return "unknown"
    if score == 0:
        return "none"
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyse_impact(
    inv: dict[str, Any],
    services: dict[str, dict[str, Any]],
    asset: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    """Compute risk score and service impact for a confirmed finding.

    Parameters
    ----------
    inv:      the dict returned by investigator.investigate().
    services: service records indexed by service ID.
    asset:    the asset record resolved from the case's asset_id.
    policy:   the dataset policy object (used for allowlist; not for scoring here,
              scoring uses the formula directly).

    Returns
    -------
    dict with keys:
        score                 int | None   (None when no service mapping)
        severity              str
        notify_first          bool
        public_restricted     bool
        service_ids           list[str]
        affected_public_service str
    """
    # Assessment must be "confirmed" for meaningful impact analysis.
    # Compliant and invalid_input cases short-circuit in the pipeline before
    # this function is called; we handle them defensively here too.
    if inv["assessment"] != "confirmed":
        service_ids = list(asset.get("service_ids", []))
        linked_services = [services[sid] for sid in service_ids if sid in services]
        service_name = (
            ", ".join(item["name"] for item in linked_services) or "Unknown service impact"
        )
        return {
            "score": 0 if inv["assessment"] == "compliant" else None,
            "severity": _severity(0 if inv["assessment"] == "compliant" else None, inv["assessment"]),
            "notify_first": False,
            "public_restricted": False,
            "service_ids": service_ids,
            "affected_public_service": service_name,
        }

    rules_violated = inv["rules_violated"]
    service_ids = list(asset.get("service_ids", []))
    linked_services = [services[sid] for sid in service_ids if sid in services]
    service_name = (
        ", ".join(item["name"] for item in linked_services) or "Unknown service impact"
    )

    # Score formula: min(100, max(violated rule weights) + 10 * max(linked service criticality))
    # None when there is no service mapping.
    if not linked_services:
        score = None
    else:
        score = min(
            100,
            max(rule["weight"] for rule in rules_violated)
            + 10 * max(item["criticality"] for item in linked_services),
        )

    public_restricted = asset["classification"] == "restricted_synthetic" and any(
        rule["id"] == "CFG-PUBLIC" for rule in rules_violated
    )
    notify_first = public_restricted or (score is not None and score >= 60)

    return {
        "score": score,
        "severity": _severity(score, inv["assessment"]),
        "notify_first": notify_first,
        "public_restricted": public_restricted,
        "service_ids": service_ids,
        "affected_public_service": service_name,
    }
