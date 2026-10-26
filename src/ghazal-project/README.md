# Public Service Risk Dashboard

Synthetic proof of concept for detecting security configuration deviations, assessing public-service impact, and preparing human escalation handoffs.

## Safety boundaries

- Synthetic data only.
- No real government systems, credentials, citizen data, or production changes.
- Human approval is required for critical findings, possible data exposure, recovery, and case closure.

## Scenarios included

The simulated county dataset includes benefits, identity, emergency services, public works, records, library, transit, and development assets. The main demonstration scenario is a benefits application whose cloud storage is unexpectedly publicly readable. The system compares observed configurations with approved baselines, calculates risk, and creates a human handoff instead of changing access automatically.

## Run locally

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
python -m pytest
python -m src.main
python -m streamlit run src/dashboard.py
```

The first command prints the generated findings and handoff decisions. The Streamlit command opens the visual dashboard in your browser.

## Project structure

```text
data/       Synthetic assets, baselines, configurations, and dependencies
agents/     YAML definitions for the proposed agents and safety gate
src/        Deterministic Python implementation
tests/      Automated tests
reports/    Generated handoff reports
```
