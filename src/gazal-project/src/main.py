"""Run the synthetic risk-analysis pipeline."""

from pathlib import Path
import json

from .pipeline import analyze


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    findings = analyze(ROOT / "data")
    print(json.dumps([finding.to_dict() for finding in findings], indent=2))


if __name__ == "__main__":
    main()
