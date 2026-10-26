from pathlib import Path

from src.pipeline import analyze


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_public_storage_is_critical_and_escalated():
    findings = analyze(DATA_DIR)
    storage = next(item for item in findings if item.asset_id == "asset-002")

    assert storage.severity == "critical"
    assert storage.escalation_required is True
    assert storage.affected_public_service == "Online Benefits Enrollment"
    assert any("public_read_access" in item for item in storage.evidence)


def test_privileged_mfa_finding_requires_review():
    findings = analyze(DATA_DIR)
    identity = next(item for item in findings if item.asset_id == "asset-003")

    assert identity.severity == "high"
    assert identity.escalation_required is False
    assert identity.affected_public_service == "County Employee Portal"
