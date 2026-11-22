"""Deterministic synthetic-dataset pipeline with an in-memory action simulator."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Iterable


@dataclass
class CaseResult:
    case_id: str
    title: str
    asset_id: str
    asset_name: str
    affected_public_service: str
    service_ids: list[str]
    assessment: str
    finding: str
    finding_rule_ids: list[str]
    severity: str
    score: int | None
    confidence: float
    evidence: list[str]
    baseline_evidence: list[str]
    action_taken: str
    action_attempts: int
    action_result: str
    verification_result: str
    outcome: str
    escalation_required: bool
    handoff_required: bool
    human_intervention: list[str]
    completed_ai_work: list[str]
    outstanding_human_work: list[str]
    decision_points: list[str]
    events: list[dict[str, Any]]
    lifecycle_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_dataset(dataset_path: str | Path) -> dict[str, Any]:
    return json.loads(Path(dataset_path).read_text(encoding="utf-8"))


def _expired(value: str, clock: str) -> bool:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) < datetime.fromisoformat(clock.replace("Z", "+00:00"))


def _snapshot_errors(snapshot: dict[str, Any], required: Iterable[str]) -> list[str]:
    errors: list[str] = []
    for field in required:
        if field not in snapshot:
            errors.append(f"missing required field: {field}")
        elif type(snapshot[field]) is not bool:
            errors.append(f"field must be a JSON boolean: {field}")
    return errors


def _add_event(events: list[dict[str, Any]], name: str, detail: str) -> None:
    events.append({"sequence": len(events) + 1, "event": name, "detail": detail})


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


def analyze(dataset_path: str | Path, case_ids: Iterable[str] | None = None) -> list[CaseResult]:
    """Run selected cases independently; no state is carried between cases."""
    dataset = load_dataset(dataset_path)
    selected = set(case_ids) if case_ids is not None else None
    services = {item["id"]: item for item in dataset["services"]}
    assets = {item["id"]: item for item in dataset["assets"]}
    baselines = {item["id"]: item for item in dataset["baselines"]}
    policy = dataset["policy"]
    clock = dataset["simulation_clock"]
    results: list[CaseResult] = []

    for case in dataset["cases"]:
        if selected is not None and case["id"] not in selected:
            continue
        asset = assets[case["asset_id"]]
        baseline = baselines[case["baseline_id"]]
        service_ids = list(asset.get("service_ids", []))
        linked_services = [services[item] for item in service_ids]
        service_name = ", ".join(item["name"] for item in linked_services) or "Unknown service impact"
        errors = _snapshot_errors(case["snapshot"], baseline["required_fields"])
        rules: list[dict[str, Any]] = []
        evidence: list[str] = []
        events: list[dict[str, Any]] = []
        action = "none"
        attempts = 0
        action_result = "not_run"
        verification = "not_run"
        handoff = False
        human_work = ["Review evidence and approve final case closure."]

        if errors:
            assessment, score, outcome = "invalid_input", None, "request_data"
            evidence = errors
            human_work.insert(0, "Provide a corrected snapshot with strict boolean fields.")
        else:
            
            active_exceptions = set()

            for exception in dataset["exceptions"]:
                if (
                    exception["id"] not in set(case.get("exception_ids", []))
                    or exception["asset_id"] != case["asset_id"]
                    or _expired(exception["expires_at"], clock)
                ):
                    continue

                matching_rule = next(
                    (
                        rule
                        for rule in baseline["rules"]
                        if rule["id"] == exception["rule_id"]
                    ),
                    None,
                )

                if matching_rule is not None:
                    observed_value = case["snapshot"].get(matching_rule["field"])

                    if observed_value == exception["approved_value"]:
                        active_exceptions.add(exception["rule_id"])
                        
                        
            
            for rule in baseline["rules"]:
                if case["snapshot"][rule["field"]] != rule["expected"] and rule["id"] not in active_exceptions:
                    rules.append(rule)
                    evidence.append(f"{rule['id']}: {rule['field']} expected {rule['expected']}, observed {case['snapshot'][rule['field']]}")

            if not rules:
                assessment, score, outcome = "compliant", 0, "no_action"
            else:
                assessment = "confirmed"
                score = None if not linked_services else min(100, max(rule["weight"] for rule in rules) + 10 * max(item["criticality"] for item in linked_services))
                public_restricted = asset["classification"] == "restricted_synthetic" and any(rule["id"] == "CFG-PUBLIC" for rule in rules)
                notify_first = public_restricted or (score is not None and score >= 60)
                authorized = (
                    "enable_audit_logging" in case["authorization"].get("allowed_actions", [])
                    and case["authorization"].get("sandbox_only") is True
                    and not _expired(case["authorization"]["expires_at"], clock)
                )
                # A high-priority logging correction may proceed after the
                # notification event. Restricted public exposure never does.
                can_action = len(rules) == 1 and rules[0]["id"] == "CFG-LOGGING" and "enable_audit_logging" in policy["allowlisted_simulated_actions"] and authorized and not public_restricted
                if notify_first:
                    _add_event(events, "notification", "Immediate human notification required before action.")
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
                    verification = "passed" if state.get("audit_logging_enabled") is True else "failed"
                    _add_event(events, "verification", f"Independent verification {verification}.")
                    if verification == "passed":
                        outcome = "verified_awaiting_human_closure"
                    else:
                        outcome, handoff = "handoff", True
                        human_work.insert(0, "Investigate the unchanged state; do not retry automatically.")
                else:
                    if public_restricted or not authorized or not linked_services:
                        handoff = True
                        outcome = "handoff" if public_restricted or not linked_services else "awaiting_approval"
                    else:
                        outcome = "awaiting_approval"
                    human_work.insert(0, "Approve or reject the proposed correction before any action.")
                    if public_restricted:
                        human_work[0] = "Incident response must review the public exposure; no automatic correction is permitted."

        if assessment == "compliant":
            lifecycle = "awaiting_human_review"
        elif outcome == "verified_awaiting_human_closure":
            lifecycle = "awaiting_human_closure"
        elif outcome == "request_data":
            lifecycle = "awaiting_corrected_data"
        elif outcome == "awaiting_approval":
            lifecycle = "awaiting_human_approval"
        else:
            lifecycle = "human_handoff_required"
        finding = ", ".join(rule["field"] for rule in rules) if rules else ("No baseline deviation" if assessment == "compliant" else "Invalid input")
        completed = ["Loaded one isolated case from public-service-risk-v1", "Validated the snapshot without coercing types", "Compared observed settings with the approved baseline", "Mapped the asset to its simulated public service"]
        if action != "none":
            completed += ["Applied the policy gate", "Read post-action state independently"]
        results.append(CaseResult(
            case_id=case["id"], title=case["title"], asset_id=case["asset_id"], asset_name=asset["type"],
            affected_public_service=service_name, service_ids=service_ids, assessment=assessment, finding=finding,
            finding_rule_ids=[rule["id"] for rule in rules] if not errors else [], severity=_severity(score, assessment),
            score=score, confidence=1.0 if not errors else 0.0, evidence=evidence,
            baseline_evidence=[f"{key} required {value}" for key, value in baseline["required_fields"].items()],
            action_taken=action, action_attempts=attempts, action_result=action_result,
            verification_result=verification, outcome=outcome, escalation_required=handoff or (score is not None and score >= 60),
            handoff_required=handoff, human_intervention=human_work, completed_ai_work=completed,
            outstanding_human_work=human_work, decision_points=["Human approval is required before closure or any unapproved correction."],
            events=events, lifecycle_status=lifecycle,
        ))
    return results
