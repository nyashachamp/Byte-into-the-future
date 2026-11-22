"""Differential regression harness — M0 pipeline comparison.

Runs all 12 synthetic cases through both pipeline implementations and
compares every serialised CaseResult field.

Implementations under test
--------------------------
MONOLITH  : tools/risk_tool_pkg/pipeline.py
            Original single-file monolithic pipeline (unchanged from before M0).

REFACTORED: src/source-code/src/pipeline.py
            Delegating pipeline introduced in M0 (calls the four agent modules
            in src/source-code/src/agents/).

Usage
-----
Run from the repository root:

    python tests/test_differential_m0.py

Exit code 0 = all 12 cases match exactly.
Exit code 1 = at least one difference found (details printed to stdout).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "samples" / "public-service-risk-v1.json"

# Add both package roots to sys.path so both pipelines can be imported.

# 1. The monolithic pipeline lives at tools/risk_tool_pkg/pipeline.py and is
#    imported as a bare module (no package prefix).
_MONOLITH_PKG = ROOT / "tools" / "risk_tool_pkg"
if str(_MONOLITH_PKG) not in sys.path:
    sys.path.insert(0, str(_MONOLITH_PKG))

# 2. The refactored pipeline is part of the src package at
#    src/source-code/src/pipeline.py, imported as src.pipeline.
_SRC_PKG = ROOT / "src" / "source-code"
if str(_SRC_PKG) not in sys.path:
    sys.path.append(str(_SRC_PKG))

# ---------------------------------------------------------------------------
# Import both pipeline implementations under distinct aliases
# ---------------------------------------------------------------------------

import pipeline as _monolith_pipeline                    # noqa: E402  tools/risk_tool_pkg/pipeline.py
import importlib
_refactored_module = importlib.import_module("src.pipeline")  # src/source-code/src/pipeline.py

# ---------------------------------------------------------------------------
# Run all 12 cases through both implementations
# ---------------------------------------------------------------------------

monolith_results = {
    r.case_id: r.to_dict()
    for r in _monolith_pipeline.analyze(DATASET)
}

refactored_results = {
    r.case_id: r.to_dict()
    for r in _refactored_module.analyze(DATASET)
}

# ---------------------------------------------------------------------------
# Field-by-field comparison
# ---------------------------------------------------------------------------

ALL_CASE_IDS = [f"C{i:02d}" for i in range(1, 13)]

# Fields checked in every case
SCALAR_FIELDS = [
    "case_id", "title", "asset_id", "asset_name",
    "affected_public_service",
    "assessment", "finding", "severity", "score", "confidence",
    "action_taken", "action_attempts", "action_result",
    "verification_result", "outcome",
    "escalation_required", "handoff_required",
    "lifecycle_status",
]

LIST_FIELDS = [
    "service_ids", "finding_rule_ids", "evidence",
    "baseline_evidence",
    "human_intervention", "completed_ai_work", "outstanding_human_work",
    "decision_points",
    "events",
]

ALL_FIELDS = SCALAR_FIELDS + LIST_FIELDS

# ---------------------------------------------------------------------------
# Collect differences
# ---------------------------------------------------------------------------

differences: dict[str, list[str]] = {}  # case_id → list of diff descriptions

for case_id in ALL_CASE_IDS:
    mono = monolith_results.get(case_id)
    refact = refactored_results.get(case_id)

    case_diffs: list[str] = []

    if mono is None:
        case_diffs.append("MISSING from monolith results")
    if refact is None:
        case_diffs.append("MISSING from refactored results")

    if case_diffs:
        differences[case_id] = case_diffs
        continue

    for field in ALL_FIELDS:
        mono_val = mono.get(field)
        refact_val = refact.get(field)

        if mono_val != refact_val:
            case_diffs.append(
                f"  FIELD '{field}':\n"
                f"    MONOLITH  : {json.dumps(mono_val,  indent=None)}\n"
                f"    REFACTORED: {json.dumps(refact_val, indent=None)}"
            )

    # Check for unexpected extra or missing fields in refactored output
    extra = set(refact.keys()) - set(mono.keys())
    missing = set(mono.keys()) - set(refact.keys())
    if extra:
        case_diffs.append(f"  EXTRA fields in refactored: {sorted(extra)}")
    if missing:
        case_diffs.append(f"  MISSING fields in refactored: {sorted(missing)}")

    if case_diffs:
        differences[case_id] = case_diffs

# ---------------------------------------------------------------------------
# Report  (runs only when executed as a script, not when imported by pytest)
# ---------------------------------------------------------------------------

SEPARATOR = "=" * 72


def _report_and_exit() -> None:
    print(SEPARATOR)
    print("DIFFERENTIAL REGRESSION — M0 Pipeline Comparison")
    print("  MONOLITH  : tools/risk_tool_pkg/pipeline.py")
    print("  REFACTORED: src/source-code/src/pipeline.py")
    print(f"  DATASET   : {DATASET.relative_to(ROOT)}")
    print(SEPARATOR)
    print()

    if not differences:
        print(f"RESULT: PASS — all {len(ALL_CASE_IDS)} cases match exactly across all fields.")
        print()
        print("Case-by-case summary:")
        for case_id in ALL_CASE_IDS:
            mono   = monolith_results[case_id]
            refact = refactored_results[case_id]
            mono_json   = json.dumps(mono,   sort_keys=True)
            refact_json = json.dumps(refact, sort_keys=True)
            status = "MATCH" if mono_json == refact_json else "DIFFER"
            print(
                f"  {case_id}  {status}"
                f"  assessment={mono['assessment']!r:<14}"
                f"  outcome={mono['outcome']!r:<35}"
                f"  events={len(mono['events'])}"
            )
        print()
        print("Fields verified per case:")
        for f in ALL_FIELDS:
            print(f"  {f}")
        sys.exit(0)

    else:
        print(f"RESULT: FAIL — differences found in {len(differences)} / {len(ALL_CASE_IDS)} cases.")
        print()
        for case_id, diffs in differences.items():
            print(f"--- {case_id} ---")
            for d in diffs:
                print(d)
            print()
        print(SEPARATOR)
        print("Full serialised output for differing cases:")
        for case_id in differences:
            print(f"\n--- {case_id} MONOLITH ---")
            print(json.dumps(monolith_results.get(case_id), indent=2))
            print(f"\n--- {case_id} REFACTORED ---")
            print(json.dumps(refactored_results.get(case_id), indent=2))
        sys.exit(1)


# ---------------------------------------------------------------------------
# pytest-compatible test: wraps the same diff data as a single test function
# ---------------------------------------------------------------------------

def test_differential_m0_all_cases_match():
    """All 12 cases must produce byte-identical output from both pipeline implementations."""
    if differences:
        lines = []
        for case_id, diffs in differences.items():
            lines.append(f"--- {case_id} ---")
            lines.extend(diffs)
        raise AssertionError(
            f"Differential regression FAILED — {len(differences)} case(s) differ:\n"
            + "\n".join(lines)
        )


if __name__ == "__main__":
    _report_and_exit()
