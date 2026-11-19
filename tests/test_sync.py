"""Sync guard: asserts that the tool package copies remain valid and consistent.

M0 note
-------
In M0, src/source-code/src/pipeline.py was refactored to delegate to the four
agent modules in src/source-code/src/agents/.  The copy at
tools/risk_tool_pkg/pipeline.py intentionally retains the original monolithic
implementation: the existing risk_analysis_agent WXO tool has no access to the
src/agents/ sub-package, so the copy must remain self-contained.

The sync guard is therefore updated to:
  - Verify the risk_tool_pkg copy is a valid standalone pipeline (contains the
    public analyze() function and CaseResult class).
  - Continue verifying the dataset copy is byte-for-byte identical to the original.
  - In M1, four new specialist packages will be added and their pipeline copies
    will each be synced to the monolithic source (tools/risk_tool_pkg/pipeline.py),
    not to the delegating pipeline.

Run:
    python -m pytest tests/test_sync.py -v
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_PIPELINE_MONOLITHIC = ROOT / "tools" / "risk_tool_pkg" / "pipeline.py"
_PIPELINE_DELEGATING = ROOT / "src" / "source-code" / "src" / "pipeline.py"

_DATASET_ORIGINAL = ROOT / "data" / "samples" / "public-service-risk-v1.json"
_DATASET_COPY     = ROOT / "tools" / "risk_tool_pkg" / "data" / "public-service-risk-v1.json"


def test_risk_tool_pkg_pipeline_is_self_contained_monolith():
    """tools/risk_tool_pkg/pipeline.py must remain a self-contained monolithic pipeline.

    From M0 onward, src/source-code/src/pipeline.py delegates to the four agent
    modules in src/agents/.  The risk_tool_pkg copy intentionally stays as the
    original standalone version so the existing WXO tool continues to work without
    requiring the src/agents/ sub-package.

    This test verifies the copy still exports the required public symbols.
    """
    assert _PIPELINE_MONOLITHIC.exists(), f"Not found: {_PIPELINE_MONOLITHIC}"
    source = _PIPELINE_MONOLITHIC.read_text(encoding="utf-8")
    assert "def analyze(" in source, (
        "tools/risk_tool_pkg/pipeline.py must contain the public analyze() function."
    )
    assert "class CaseResult" in source, (
        "tools/risk_tool_pkg/pipeline.py must contain the CaseResult dataclass."
    )
    # The monolithic copy must NOT import from the src.agents subpackage,
    # because the tool package has no access to it.
    assert "from .agents" not in source, (
        "tools/risk_tool_pkg/pipeline.py must not import from .agents — "
        "it must remain a self-contained monolith."
    )


def test_delegating_pipeline_imports_all_four_agent_modules():
    """src/source-code/src/pipeline.py must import all four agent modules.

    Verifies that the M0 refactor correctly delegates to each specialist module.
    """
    assert _PIPELINE_DELEGATING.exists(), f"Not found: {_PIPELINE_DELEGATING}"
    source = _PIPELINE_DELEGATING.read_text(encoding="utf-8")
    for module in ("investigator", "analyst", "response_agent", "verifier"):
        assert f"import {module}" in source or f"agents import {module}" in source, (
            f"src/source-code/src/pipeline.py must import the {module} agent module."
        )


def test_dataset_copy_is_in_sync():
    """tools/risk_tool_pkg/data/public-service-risk-v1.json must be identical to the original."""
    assert _DATASET_ORIGINAL.exists(), f"Original not found: {_DATASET_ORIGINAL}"
    assert _DATASET_COPY.exists(),     f"Copy not found: {_DATASET_COPY}"
    assert _DATASET_ORIGINAL.read_bytes() == _DATASET_COPY.read_bytes(), (
        "tools/risk_tool_pkg/data/public-service-risk-v1.json is out of sync with "
        "data/samples/public-service-risk-v1.json — re-copy it before importing the tool."
    )
