# Public Service Risk Dashboard — Technical Development Report

## Project overview

This project is a synthetic cybersecurity risk dashboard for identifying configuration problems that could affect public services. My main contribution was preparing the Python application to use the team’s 12-case synthetic dataset, making the workflow reproducible on Ubuntu, and adding tests for the required safety behaviors.

The application is currently located in `src/source-code/`.

The local version has been tested successfully. The dataset validator passed, and the automated test suite passed with eight tests. IBM Cloud deployment and testing are the next phase.

## 1. System architecture

The project has four main parts:

1. The synthetic dataset in `data/samples/public-service-risk-v1.json`.
2. The Python pipeline in `src/source-code/src/pipeline.py`.
3. The command-line entry point in `src/source-code/src/main.py`.
4. The Streamlit dashboard in `src/source-code/src/dashboard.py`.

The dataset provides the simulated services, assets, approved baselines, exceptions, policy rules, authorizations, and test cases. The pipeline processes each case independently and sends the result to the command-line output or dashboard.

The system does not connect to real government systems, storage accounts, citizen records, or production infrastructure. Any correction is performed only on an in-memory copy of the synthetic case state.

## 2. Agent functionality

The project includes five agent-role YAML files:

| Agent | Function |
|---|---|
| Configuration Agent | Compares the observed configuration with the approved baseline. |
| Impact Agent | Connects an asset to its public service and identifies unknown impact. |
| Prioritization Agent | Calculates the synthetic priority score. |
| Policy Gate | Checks exceptions, authorization, expiration, and permitted actions. |
| Handoff Agent | Prepares the human-review information and outstanding decisions. |

The current prototype uses deterministic Python orchestration to perform these tasks. The YAML files describe the agent roles and safety boundaries, but the application does not yet use an external language model or IBM watsonx API. I am documenting this distinction so we do not claim an IBM integration before it has been tested.

The workflow is:

```text
Load case → Validate input → Compare baseline → Check exceptions
→ Determine service impact → Calculate priority → Apply policy gate
→ Simulate permitted action → Verify the resulting state → Report or hand off
```

## 3. Code implementation

The application uses:

- Python 3.10 or newer
- Streamlit for the dashboard
- PyYAML for the YAML agent definitions
- pytest for automated testing
- JSON for the dataset and expected test fixtures

Important files include:

- `src/source-code/src/pipeline.py` — main analysis and safety logic
- `src/source-code/src/main.py` — command-line runner
- `src/source-code/src/dashboard.py` — Streamlit interface
- `src/source-code/agents/` — agent-role YAML files
- `src/source-code/tests/test_pipeline.py` — automated tests
- `tests/validate_synthetic_dataset.py` — dataset consistency check

No external API is required for the current local workflow.

## 4. Dataset integration

The pipeline reads `data/samples/public-service-risk-v1.json` and processes every case with a fresh state. A correction made in one case cannot affect another case.

Before analyzing a case, the pipeline checks that required fields exist and that Boolean values are actual JSON Booleans. It does not convert invalid strings such as `"false"` into Boolean values.

The pipeline also checks that an exception has the correct ID, asset, rule, expiration, and `approved_value`. An exception is only allowed to suppress a finding when the observed configuration matches the approved value.

When an asset has no known public-service mapping, the system does not invent a service or treat the risk as zero. It reports the priority as unknown, prevents automatic action, and requires human handoff.

## 5. Testing and debugging

The original 12-case dataset validator passed:

```text
PASS: 12 fixture cases; references, strict input types, baseline labels,
scores, notification rules, and action authorization expectations are consistent.
```

The automated test suite passed:

```text
8 passed
```

The tests cover the main workflow cases, including C03, C05, C07, compliant cases, invalid input, unknown service impact, and encryption findings.

### F-01: Security exception validation

The first review found that the pipeline checked an exception’s ID, asset, rule, and expiration, but did not check whether the observed value matched `approved_value`.

I corrected the pipeline so a mismatched exception cannot hide a security finding. I also added a negative regression test using a temporary modified copy of the dataset. The test confirms that an invalid C02 exception produces a finding instead of being accepted.

The legitimate C02 exception still works correctly.

### F-02: Unknown severity display

The pipeline originally treated both a score of `0` and a missing score as `none`. This was misleading for C11 because C11 has an unknown priority, not confirmed zero risk.

I changed the classification so:

- A confirmed score of `0` is displayed as `NONE`.
- A missing or null score is displayed as `UNKNOWN`.

C11 now displays `UNKNOWN`, while compliant case C01 continues to display `NONE`.

## 6. IBM Cloud integration

This section is pending because the application has not yet been deployed and tested in IBM Cloud.

During the next phase, I will document:

- The IBM Cloud service used to host the application.
- The deployment method.
- The Python runtime and dependency installation process.
- Required environment variables and secret handling.
- The dataset path in the cloud environment.
- The dashboard startup command and access method.
- Whether the 12 scenarios produce the same results as the local version.
- Any changes needed for paths, permissions, networking, or dependencies.

No credentials or secret values should be committed to GitHub.

## 7. Current limitations

- The dataset and policy are synthetic demonstration fixtures, not production security standards.
- Simulated actions only modify in-memory state.
- IBM Cloud and watsonx integration have not yet been verified.
- The current implementation uses deterministic Python orchestration rather than independently deployed AI agents.
- Dashboard behavior should be tested again after deployment to IBM Cloud.
- Future improvements could include persistent execution logs, stronger schema validation, authentication, cloud monitoring, and a formal deployment configuration.
- Cases are never closed automatically; human review remains required.

## 8. Reproducibility commands

From the repository root on Ubuntu:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r src/source-code/requirements.txt
python tests/validate_synthetic_dataset.py
cd src/source-code
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python -m src.main
python -m streamlit run src/dashboard.py
```

This report will be updated after the independent Ubuntu rerun and IBM Cloud testing.
