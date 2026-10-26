"""Safe, deterministic analysis pipeline for the synthetic proof of concept."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json


CRITICALITY_SCORE = {"low": 1, "medium": 2, "high": 3}


@dataclass
class Finding:
    case_id: str
    asset_id: str
    asset_name: str
    finding: str
    severity: str
    score: int
    confidence: float
    affected_public_service: str
    evidence: list[str]
    escalation_required: bool
    completed_ai_work: list[str]
    outstanding_human_work: list[str]
    decision_points: list[str]
    lifecycle_status: str = "awaiting_human_review"

    def to_dict(self) -> dict:
        return asdict(self)


def load_json(data_dir: Path, filename: str):
    return json.loads((data_dir / filename).read_text(encoding="utf-8"))


def analyze(data_dir: str | Path) -> list[Finding]:
    data_dir = Path(data_dir)
    assets = {item["asset_id"]: item for item in load_json(data_dir, "assets.json")}
    baselines = {item["asset_id"]: item for item in load_json(data_dir, "baselines.json")}
    configurations = load_json(data_dir, "configurations.json")
    dependencies = load_json(data_dir, "dependencies.json")

    service_by_asset = {asset_id: asset["public_service"] for asset_id, asset in assets.items()}
    # Keep an asset's declared service as the primary label. Dependencies are
    # retained as context rather than replacing the dependent asset's service.
    dependency_context = {
        item["depends_on"]: item["relationship"] for item in dependencies
    }

    findings: list[Finding] = []
    for index, configuration in enumerate(configurations, start=1):
        asset_id = configuration["asset_id"]
        asset = assets[asset_id]
        baseline = baselines.get(asset_id, {"required_settings": {}})["required_settings"]
        observed = configuration["observed_settings"]
        differences = [
            f"{key}: expected {expected}, observed {observed.get(key)}"
            for key, expected in baseline.items()
            if observed.get(key) != expected
        ]
        if not differences:
            continue

        public_exposure = (
            observed.get("public_read_access") is True
            or observed.get("admin_api_public") is True
        )
        privileged_mfa_disabled = observed.get("mfa_required_for_privileged_accounts") is False
        exposure_score = 3 if public_exposure else 2
        service_score = 3 if asset["criticality"] == "high" else 2
        confidence_score = 3
        score = exposure_score + CRITICALITY_SCORE[asset["criticality"]] + service_score + confidence_score
        severity = "critical" if public_exposure else ("high" if privileged_mfa_disabled else "medium")
        escalation = public_exposure or severity == "critical"
        service = service_by_asset.get(asset_id, "Unknown simulated service")

        findings.append(Finding(
            case_id=f"CASE-{index:03d}",
            asset_id=asset_id,
            asset_name=asset["name"],
            finding="Configuration deviation",
            severity=severity,
            score=score,
            confidence=0.94 if public_exposure else 0.90,
            affected_public_service=service,
            evidence=differences + ([
                f"dependency_context: {dependency_context[asset_id]}"
            ] if asset_id in dependency_context else []),
            escalation_required=escalation,
            completed_ai_work=[
                "Read synthetic configuration",
                "Compared observed settings with approved baseline",
                "Linked the asset to a simulated public service",
                "Calculated a preliminary risk score",
            ],
            outstanding_human_work=(
                [
                    "Verify whether sensitive data is present",
                    "Review access history",
                    "Determine incident status",
                    "Approve any access change",
                ] if public_exposure else [
                    "Confirm owner and remediation window",
                    "Approve the configuration change",
                ]
            ),
            decision_points=(
                ["Human approval required before changing access or closing the case"]
                if escalation else ["Human owner should approve remediation plan"]
            ),
        ))
    return findings
