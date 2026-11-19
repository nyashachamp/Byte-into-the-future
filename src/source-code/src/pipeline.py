"""Deterministic synthetic-dataset pipeline with an in-memory action simulator.

The analyze() function delegates each stage of its logic to the four specialist
agent modules in src/agents/:

    investigator   – Security Investigator   (input validation, baseline comparison)
    analyst        – Risk & Dependency Analyst (service mapping, score, notify_first)
    response_agent – Response Agent           (authorization gate, sandbox action, retry)
    verifier       – Verification & Handoff   (independent state check, outcome, handoff)

The CaseResult dataclass and the public analyze() signature are unchanged so that
the Streamlit dashboard, CLI entry-point, and all existing tests continue to work
without modification.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable

from .agents import investigator as _investigator
from .agents import analyst as _analyst
from .agents import response_agent as _response_agent
from .agents import verifier as _verifier


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

        # ------------------------------------------------------------------
        # Stage 1 – Security Investigator
        # ------------------------------------------------------------------
        inv = _investigator.investigate(
            case=case,
            asset=asset,
            baseline=baseline,
            exceptions=dataset["exceptions"],
            clock=clock,
        )

        # ------------------------------------------------------------------
        # Short-circuit: invalid input
        # ------------------------------------------------------------------
        if inv["assessment"] == "invalid_input":
            service_ids = list(asset.get("service_ids", []))
            linked_services = [services[sid] for sid in service_ids]
            service_name = (
                ", ".join(item["name"] for item in linked_services) or "Unknown service impact"
            )
            human_work = [
                "Provide a corrected snapshot with strict boolean fields.",
                "Review evidence and approve final case closure.",
            ]
            results.append(CaseResult(
                case_id=case["id"], title=case["title"],
                asset_id=case["asset_id"], asset_name=asset["type"],
                affected_public_service=service_name, service_ids=service_ids,
                assessment="invalid_input",
                finding="Invalid input",
                finding_rule_ids=[],
                severity="unknown", score=None, confidence=0.0,
                evidence=inv["errors"],
                baseline_evidence=[
                    f"{key} required {value}"
                    for key, value in baseline["required_fields"].items()
                ],
                action_taken="none", action_attempts=0, action_result="not_run",
                verification_result="not_run",
                outcome="request_data",
                escalation_required=False,
                handoff_required=False,
                human_intervention=human_work,
                completed_ai_work=[
                    "Loaded one isolated case from public-service-risk-v1",
                    "Validated the snapshot without coercing types",
                    "Compared observed settings with the approved baseline",
                    "Mapped the asset to its simulated public service",
                ],
                outstanding_human_work=human_work,
                decision_points=["Human approval is required before closure or any unapproved correction."],
                events=[],
                lifecycle_status="awaiting_corrected_data",
            ))
            continue

        # ------------------------------------------------------------------
        # Short-circuit: compliant
        # ------------------------------------------------------------------
        if inv["assessment"] == "compliant":
            service_ids = list(asset.get("service_ids", []))
            linked_services = [services[sid] for sid in service_ids]
            service_name = (
                ", ".join(item["name"] for item in linked_services) or "Unknown service impact"
            )
            human_work = ["Review evidence and approve final case closure."]
            results.append(CaseResult(
                case_id=case["id"], title=case["title"],
                asset_id=case["asset_id"], asset_name=asset["type"],
                affected_public_service=service_name, service_ids=service_ids,
                assessment="compliant",
                finding="No baseline deviation",
                finding_rule_ids=[],
                severity="none", score=0, confidence=1.0,
                evidence=[],
                baseline_evidence=[
                    f"{key} required {value}"
                    for key, value in baseline["required_fields"].items()
                ],
                action_taken="none", action_attempts=0, action_result="not_run",
                verification_result="not_run",
                outcome="no_action",
                escalation_required=False,
                handoff_required=False,
                human_intervention=human_work,
                completed_ai_work=[
                    "Loaded one isolated case from public-service-risk-v1",
                    "Validated the snapshot without coercing types",
                    "Compared observed settings with the approved baseline",
                    "Mapped the asset to its simulated public service",
                ],
                outstanding_human_work=human_work,
                decision_points=["Human approval is required before closure or any unapproved correction."],
                events=[],
                lifecycle_status="awaiting_human_review",
            ))
            continue

        # ------------------------------------------------------------------
        # Stage 2 – Risk & Dependency Analyst
        # ------------------------------------------------------------------
        an = _analyst.analyse_impact(
            inv=inv,
            services=services,
            asset=asset,
            policy=policy,
        )

        # ------------------------------------------------------------------
        # Stage 3 – Response Agent
        # ------------------------------------------------------------------
        resp = _response_agent.execute_response(
            inv=inv,
            an=an,
            case=case,
            policy=policy,
            clock=clock,
        )

        # ------------------------------------------------------------------
        # Stage 4 – Verification & Handoff
        # ------------------------------------------------------------------
        vr = _verifier.verify_and_prepare_handoff(
            inv=inv,
            an=an,
            resp=resp,
            case=case,
        )

        # ------------------------------------------------------------------
        # Assemble CaseResult (identical fields to the original pipeline)
        # ------------------------------------------------------------------
        rules_violated = inv["rules_violated"]
        finding = ", ".join(rule["field"] for rule in rules_violated)
        finding_rule_ids = [rule["id"] for rule in rules_violated]
        score = an["score"]
        handoff_required = vr["handoff_required"]

        results.append(CaseResult(
            case_id=case["id"], title=case["title"],
            asset_id=case["asset_id"], asset_name=asset["type"],
            affected_public_service=an["affected_public_service"],
            service_ids=an["service_ids"],
            assessment=inv["assessment"],
            finding=finding,
            finding_rule_ids=finding_rule_ids,
            severity=an["severity"],
            score=score,
            confidence=inv["confidence"],
            evidence=inv["evidence"],
            baseline_evidence=[
                f"{key} required {value}"
                for key, value in baseline["required_fields"].items()
            ],
            action_taken=resp["action_taken"],
            action_attempts=resp["action_attempts"],
            action_result=resp["action_result"],
            verification_result=vr["verification_result"],
            outcome=vr["outcome"],
            escalation_required=handoff_required or (score is not None and score >= 60),
            handoff_required=handoff_required,
            human_intervention=vr["human_intervention"],
            completed_ai_work=vr["completed_ai_work"],
            outstanding_human_work=vr["human_intervention"],
            decision_points=["Human approval is required before closure or any unapproved correction."],
            events=vr["events"],
            lifecycle_status=vr["lifecycle_status"],
        ))

    return results
