from pathlib import Path

from src.pipeline import analyze
import json

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATASET = REPOSITORY_ROOT / "data" / "samples" / "public-service-risk-v1.json"


def result(case_id: str):
    return next(item for item in analyze(DATASET, [case_id]) if item.case_id == case_id)


def test_c03_corrects_logging_and_verifies_independently():
    item = result("C03")
    assert item.score == 30
    assert item.action_taken == "enable_audit_logging"
    assert item.action_attempts == 1
    assert item.verification_result == "passed"
    assert item.outcome == "verified_awaiting_human_closure"


def test_c05_escalates_without_automatic_change():
    item = result("C05")
    assert item.score == 100
    assert item.severity == "critical"
    assert item.action_attempts == 0
    assert item.action_taken == "none"
    assert item.handoff_required is True
    assert item.verification_result == "not_run"


def test_c07_detects_success_without_state_change_and_does_not_retry():
    item = result("C07")
    assert item.action_taken == "enable_audit_logging"
    assert item.action_attempts == 1
    assert item.action_result == "success"
    assert item.verification_result == "failed"
    assert item.outcome == "handoff"
    assert item.handoff_required is True


def test_all_cases_are_isolated_and_have_expected_core_outcomes():
    results = {item.case_id: item for item in analyze(DATASET)}
    assert len(results) == 12
    assert results["C01"].outcome == "no_action"
    assert results["C02"].outcome == "no_action"
    assert results["C09"].assessment == "invalid_input"
    assert results["C10"].assessment == "invalid_input"
    assert results["C11"].score is None
    assert results["C11"].action_taken == "none"
    assert results["C11"].action_attempts == 0
    assert results["C11"].handoff_required is True
    assert results["C12"].score == 50

def test_mismatched_exception_does_not_suppress_finding(tmp_path):
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))

    # C02 normally has approved_value=True and observed public_read=True.
    # Make the exception intentionally invalid.
    dataset["exceptions"][0]["approved_value"] = False

    modified_dataset = tmp_path / "mismatched-exception.json"
    modified_dataset.write_text(
        json.dumps(dataset),
        encoding="utf-8",
    )

    item = next(
        result
        for result in analyze(modified_dataset, ["C02"])
        if result.case_id == "C02"
    )

    assert item.assessment == "confirmed"
    assert item.finding_rule_ids == ["CFG-PUBLIC"]
    assert item.action_attempts == 0


def test_valid_c02_exception_still_suppresses_finding():
    item = result("C02")

    assert item.assessment == "compliant"
    assert item.finding_rule_ids == []
    assert item.score == 0


def test_unknown_service_has_unknown_severity_and_no_action():
    item = result("C11")

    assert item.score is None
    assert item.severity == "unknown"
    assert item.action_taken == "none"
    assert item.action_attempts == 0
    assert item.handoff_required is True


def test_zero_score_compliant_case_has_none_severity():
    item = result("C01")

    assert item.score == 0
    assert item.severity == "none"