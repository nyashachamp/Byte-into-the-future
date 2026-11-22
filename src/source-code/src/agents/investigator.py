"""Security Investigator agent logic.

Responsibility: validate the configuration snapshot, apply exception suppression,
compare observed settings with approved baseline rules, and return a structured
investigation result.

This module contains the exact logic extracted from pipeline.analyze() lines
103-150. It has no side-effects and makes no network or file-system calls
beyond what it receives as arguments.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Shared utilities (duplicated here so each agent module is self-contained)
# ---------------------------------------------------------------------------

def _expired(value: str, clock: str) -> bool:
    return (
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        < datetime.fromisoformat(clock.replace("Z", "+00:00"))
    )


def _snapshot_errors(snapshot: dict[str, Any], required: dict[str, Any]) -> list[str]:
    """Return a list of validation error strings for the snapshot.

    ``required`` is the baseline ``required_fields`` dict whose keys name the
    fields that must be present and whose values are the expected booleans
    (used only for type-checking here).
    """
    errors: list[str] = []
    for field in required:
        if field not in snapshot:
            errors.append(f"missing required field: {field}")
        elif type(snapshot[field]) is not bool:
            errors.append(f"field must be a JSON boolean: {field}")
    return errors


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def investigate(
    case: dict[str, Any],
    asset: dict[str, Any],
    baseline: dict[str, Any],
    exceptions: list[dict[str, Any]],
    clock: str,
) -> dict[str, Any]:
    """Validate a snapshot and compare it against the approved baseline.

    Parameters
    ----------
    case:       the full case record from the dataset.
    asset:      the asset record resolved from case["asset_id"].
    baseline:   the baseline record resolved from case["baseline_id"].
    exceptions: all exception records from the dataset.
    clock:      ISO-8601 simulation clock string used for expiry checks.

    Returns
    -------
    dict with keys:
        assessment        "compliant" | "confirmed" | "invalid_input"
        rules_violated    list of rule dicts that failed (empty when compliant/invalid)
        errors            list of validation error strings (empty when valid)
        evidence          human-readable finding strings
        confidence        1.0 when valid, 0.0 when invalid
    """
    snapshot = case["snapshot"]
    errors = _snapshot_errors(snapshot, baseline["required_fields"])

    if errors:
        return {
            "assessment": "invalid_input",
            "rules_violated": [],
            "errors": errors,
            "evidence": errors,
            "confidence": 0.0,
        }

    # --- Exception suppression ---
    active_exceptions: set[str] = set()
    case_exception_ids = set(case.get("exception_ids", []))

    for exception in exceptions:
        if (
            exception["id"] not in case_exception_ids
            or exception["asset_id"] != case["asset_id"]
            or _expired(exception["expires_at"], clock)
        ):
            continue

        matching_rule = next(
            (rule for rule in baseline["rules"] if rule["id"] == exception["rule_id"]),
            None,
        )
        if matching_rule is not None:
            observed_value = snapshot.get(matching_rule["field"])
            if observed_value == exception["approved_value"]:
                active_exceptions.add(exception["rule_id"])

    # --- Baseline comparison ---
    rules_violated: list[dict[str, Any]] = []
    evidence: list[str] = []

    for rule in baseline["rules"]:
        if snapshot[rule["field"]] != rule["expected"] and rule["id"] not in active_exceptions:
            rules_violated.append(rule)
            evidence.append(
                f"{rule['id']}: {rule['field']} expected {rule['expected']},"
                f" observed {snapshot[rule['field']]}"
            )

    if not rules_violated:
        return {
            "assessment": "compliant",
            "rules_violated": [],
            "errors": [],
            "evidence": [],
            "confidence": 1.0,
        }

    return {
        "assessment": "confirmed",
        "rules_violated": rules_violated,
        "errors": [],
        "evidence": evidence,
        "confidence": 1.0,
    }
