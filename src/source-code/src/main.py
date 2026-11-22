"""Run the synthetic risk-analysis pipeline."""

from pathlib import Path
import json

from .pipeline import analyze


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATASET = REPOSITORY_ROOT / "data" / "samples" / "public-service-risk-v1.json"


def main() -> None:
    results = analyze(DATASET)
    print(json.dumps([result.to_dict() for result in results], indent=2))


if __name__ == "__main__":
    main()
