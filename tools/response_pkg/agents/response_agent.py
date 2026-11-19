"""Response Agent logic.

Responsibility: check the policy authorization gate and execute the allowlisted
simulated action if — and only if — every guard passes. Implements bounded retry
(at most min(2, max_attempts) total attempts). Never retries after a tool reports
success but state is unchanged (C07 invariant). Never acts on restricted-synthetic
public-exposure cases regardless of authorization.

This module contains the exact logic extracted from pipeline.analyze() lines
159-200 (can_action evaluation, action loop, retry bounds).

Authorization invariants (all must hold for can_action to be True):
  1. Exactly one rule is violated, and it is CFG-LOGGING.
  2. "enable_audit_logging" is in policy["allowlisted_simulated_actions"].
  3. "enable_audit_logging" is in case["authorization"]["allowed_actions"].
  4. case["authorization"]["sandbox_only"] is exactly True (strict bool).
  5. The authorization has not expired relative to the simulation clock.
  6. public_restricted is False (restricted data exposure is never auto-corrected).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Shared utility
# ---------------------------------------------------------------------------

def _expired(value: str, clock: str) -> bool:
    return (
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        < datetime.fromisoformat(clock.replace("Z", "+00:00"))
    )


def _add_event(events: list[dict[str, Any]], name: str, detail: str) -> None:
    events.append({"sequence": len(events) + 1, "event": name, "detail": detail})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def execute_response(
    inv: dict[str, Any],
    an: dict[str, Any],
    case: dict[str, Any],
    policy: dict[str, Any],
    clock: str,
) -> dict[str, Any]:
    """Check authorization and execute the allowlisted simulated action.

    Parameters
    ----------
    inv:    dict returned by investigator.investigate().
    an:     dict returned by analyst.analyse_impact().
    case:   the full case record from the dataset.
    policy: the dataset policy object.
    clock:  ISO-8601 simulation clock string.

    Returns
    -------
    dict with keys:
        action_taken    str    "enable_audit_logging" or "none"
        action_attempts int
        action_result   str    "success" | "transient_failure" | "not_run"
        post_state      dict   copy of snapshot after attempted action
        events          list   ordered event records
        handoff         bool   True when outcome requires human handoff
        outcome         str
    """
    events: list[dict[str, Any]] = []
    action = "none"
    attempts = 0
    action_result = "not_run"
    handoff = False
    outcome = "no_action"

    # Only "confirmed" findings reach the Response Agent; guard defensively.
    if inv["assessment"] != "confirmed":
        return {
            "action_taken": action,
            "action_attempts": attempts,
            "action_result": action_result,
            "post_state": dict(case["snapshot"]),
            "events": events,
            "handoff": handoff,
            "outcome": "no_action",
        }

    rules_violated = inv["rules_violated"]
    public_restricted = an["public_restricted"]
    notify_first = an["notify_first"]
    linked_services_exist = bool(an["service_ids"])

    # Emit notification event before any action when required.
    if notify_first:
        _add_event(events, "notification", "Immediate human notification required before action.")

    # --- Authorization gate ---
    authorized = (
        "enable_audit_logging" in case["authorization"].get("allowed_actions", [])
        and case["authorization"].get("sandbox_only") is True
        and not _expired(case["authorization"]["expires_at"], clock)
    )

    can_action = (
        len(rules_violated) == 1
        and rules_violated[0]["id"] == "CFG-LOGGING"
        and "enable_audit_logging" in policy["allowlisted_simulated_actions"]
        and authorized
        and not public_restricted
    )

    if can_action:
        action = "enable_audit_logging"
        behavior = case["simulation"]["tool_behavior"]
        state = dict(case["snapshot"])

        for attempt in range(1, min(2, case["simulation"].get("max_attempts", 1)) + 1):
            attempts = attempt
            _add_event(events, "action_attempt", f"Attempt {attempt}: {action}")
            if behavior == "transient_then_success" and attempt == 1:
                action_result = "transient_failure"
                _add_event(events, "tool_result", "Temporary simulated tool failure.")
                continue
            action_result = "success"
            if behavior != "success_without_change":
                state["audit_logging_enabled"] = True
            _add_event(events, "tool_result", "Tool reported success.")
            break

        return {
            "action_taken": action,
            "action_attempts": attempts,
            "action_result": action_result,
            "post_state": state,
            "events": events,
            "handoff": False,   # handoff/outcome determined by verifier after state check
            "outcome": "pending_verification",
        }

    # --- No action path: determine outcome and handoff ---
    if public_restricted or not authorized or not linked_services_exist:
        handoff = True
        outcome = (
            "handoff"
            if (public_restricted or not linked_services_exist)
            else "awaiting_approval"
        )
    else:
        outcome = "awaiting_approval"

    return {
        "action_taken": action,
        "action_attempts": attempts,
        "action_result": action_result,
        "post_state": dict(case["snapshot"]),
        "events": events,
        "handoff": handoff,
        "outcome": outcome,
    }
