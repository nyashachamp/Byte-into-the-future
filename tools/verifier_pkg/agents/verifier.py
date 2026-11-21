"""Verification & Handoff agent logic.

Responsibility: independently verify the post-action state (without trusting the
tool's own success/failure report), determine the final outcome and lifecycle
status, and assemble the human handoff packet.

This module contains the exact logic extracted from pipeline.analyze() lines
185-215 (verification check, outcome/lifecycle/finding/completed_ai_work
derivation, and human_work assembly).

Key invariant: a tool success message alone does NOT establish resolution.
verification = "passed" only when post_state["audit_logging_enabled"] is
exactly True.  If the tool reported "success" but the flag is still False,
verification = "failed" and the case is handed off (C07 scenario).
"""

from __future__ import annotations

from typing import Any


def _add_event(events: list[dict[str, Any]], name: str, detail: str) -> None:
    events.append({"sequence": len(events) + 1, "event": name, "detail": detail})


def verify_and_prepare_handoff(
    inv: dict[str, Any],
    an: dict[str, Any],
    resp: dict[str, Any],
    case: dict[str, Any],
) -> dict[str, Any]:
    """Verify post-action state and assemble the human handoff packet.

    Parameters
    ----------
    inv:  dict from investigator.investigate().
    an:   dict from analyst.analyse_impact().
    resp: dict from response_agent.execute_response().
    case: the full case record from the dataset.

    Returns
    -------
    dict with keys:
        verification_result  "passed" | "failed" | "not_run"
        outcome              final outcome string
        handoff_required     bool
        human_intervention   list[str]
        completed_ai_work    list[str]
        lifecycle_status     str
        events               list (resp events + verification event appended)
    """
    events: list[dict[str, Any]] = list(resp["events"])  # copy; do not mutate resp
    verification = "not_run"
    handoff: Any | bool = resp["handoff"] or inv["assessment"] in ("invalid_input", "error")
    outcome = resp["outcome"]
    human_work = ["Review evidence and approve final case closure."]

    # --- Verification path: only when an action was actually attempted ---
    if resp["action_taken"] != "none" and resp["outcome"] == "pending_verification":
        verification = (
            "passed" if resp["post_state"].get("audit_logging_enabled") is True else "failed"
        )
        _add_event(events, "verification", f"Independent verification {verification}.")

        if verification == "passed":
            outcome = "verified_awaiting_human_closure"
            handoff = False
        else:
            outcome = "handoff"
            handoff = True
            human_work.insert(0, "Investigate the unchanged state; do not retry automatically.")

    # --- No-action path: set human_work message based on the reason ---
    elif resp["action_taken"] == "none" and inv["assessment"] == "confirmed":
        public_restricted = an["public_restricted"]
        if public_restricted:
            human_work.insert(
                0,
                "Incident response must review the public exposure;"
                " no automatic correction is permitted.",
            )
        else:
            human_work.insert(0, "Approve or reject the proposed correction before any action.")

    # --- Invalid input: data quality message ---
    elif inv["assessment"] == "invalid_input":
        human_work.insert(0, "Provide a corrected snapshot with strict boolean fields.")

    # --- Lifecycle status ---
    if inv["assessment"] == "compliant":
        lifecycle = "awaiting_human_review"
    elif outcome == "verified_awaiting_human_closure":
        lifecycle = "awaiting_human_closure"
    elif outcome == "request_data":
        lifecycle = "awaiting_corrected_data"
    elif outcome == "awaiting_approval":
        lifecycle = "awaiting_human_approval"
    else:
        lifecycle = "human_handoff_required"

    # --- Completed AI work ---
    completed = [
        "Loaded one isolated case from public-service-risk-v1",
        "Validated the snapshot without coercing types",
        "Compared observed settings with the approved baseline",
        "Mapped the asset to its simulated public service",
    ]
    if resp["action_taken"] != "none":
        completed += ["Applied the policy gate", "Read post-action state independently"]

    return {
        "verification_result": verification,
        "outcome": outcome,
        "handoff_required": handoff,
        "human_intervention": human_work,
        "completed_ai_work": completed,
        "lifecycle_status": lifecycle,
        "events": events,
    }
