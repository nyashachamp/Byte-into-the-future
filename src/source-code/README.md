# Deterministic Public Service Risk Dashboard

This directory holds the local Python/Streamlit synthetic proof of concept. It analyses configuration deviations, public-service dependency impact, policy-authorized simulated actions, independent post-action checking, and human handoff.

**Scope:** local deterministic application, distinct from the newer five-native-agent watsonx Orchestrate configuration in the repository root [`agents/`](../../agents/).

## Architecture

| File or directory | Responsibility |
|---|---|
| `src/pipeline.py` | Deterministic case lifecycle / risk-analysis entry point |
| `src/agents/` | Python investigator, analyst, response and verifier modules |
| `src/main.py` | CLI entry point |
| `src/dashboard.py` | Streamlit dashboard |
| `agents/` | Original prototype role/policy YAML (not native-agent deployment evidence) |
| `tests/` | Automated local tests |
| `../../data/samples/public-service-risk-v1.json` | Shared synthetic dataset |

The root [`tools/`](../../tools/) contains native-agent tool packaging and synchronized copies of code/data. Do not assume these copies update automatically when the canonical source changes.

## Run locally

From the **repository root**, create and activate a virtual environment, then run:

```bash
python -m pip install -r src/source-code/requirements.txt
python -m pip install pytest
python tests/validate_synthetic_dataset.py
cd src/source-code
python -m pytest -q
python -m src.main
python -m streamlit run src/dashboard.py
```

Install Python 3.10+ and use the appropriate virtual environment activation command for Windows, macOS, or Linux. These are the deterministic local commands, **not** watsonx authentication/deployment steps. Run them again on the exact final accepted commit before claiming a new passing result.

For the prior observed Ubuntu testing process, see [Ubuntu local installation log](../../docs/ubuntu-local-installation-log-2026-10-27.md) and [Oct 29 functional report](../../docs/cybersecurity-functional-test-report-2026-10-29.md).

## Safety boundaries

- Synthetic scenario fixtures only; no live government systems or real citizen data.
- Simulated responses modify in-memory data; do not interpret a displayed success as a real infrastructure change.
- Critical or uncertain findings remain subject to human escalation; human approval is required for final closure.
- A local 12-case result does **not** establish a passed native-agent formal evaluation or published Live version.

For later IBM Bob/watsonx testing, see the [current system status](../../docs/current-system-status-2026-11-20.md) and [validation log](../../docs/validation-progress-2026-11-20.md).
