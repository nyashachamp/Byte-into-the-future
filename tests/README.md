# Testing and Validation

**Checkpoint:** 20 November 2026 · **Project:** Public Service Risk Dashboard / Civic Shield

There are two distinct verification paths. **Do not combine their pass counts or use local fixture outcomes as proof of a successfully deployed five-native-agent workflow.**

## 1. Local deterministic Python / Streamlit tests

- [Synthetic dataset v1](../data/samples/README.md): 12 representative test cases; evaluator-only expected answers in [fixtures](fixtures/public-service-risk-v1.expected.json).
- [Source-specific Python tests](../src/source-code/tests/): functional unit/regression tests for the deterministic application.
- [Repository-level tests](./): fixture validation and later source/tool consistency tests.
- [October 29 functional report](../docs/cybersecurity-functional-test-report-2026-10-29.md): reports **12/12 synthetic case behaviors** observed in local testing, with F-01/F-02 findings and explicit limitations.
- [54 original local screenshots](../docs/testing-evidence/README.md): retained as historical evidence of the Ubuntu/Streamlit test scope.

Representative local validation commands from the repository root:

```bash
python tests/validate_synthetic_dataset.py
cd src/source-code
python -m pytest -q
```

Do not treat these commands as proof that tests were rerun on the current head; record the commit, date and actual output whenever they are run.

## 2. Native watsonx Orchestrate five-agent formal evaluations

The five-agent recovery branch has separate native specs under [`agents/`](../agents/) and tool packages under [`tools/`](../tools/). The team lead observed imported/configured agents. A C03 Draft Preview generated a report, **but the first formal C03 test FAILED on 2026-11-20 at 09:16 Pacific (0/1)**.

The saved `investigator_result` matcher was changed from Exact to Fuzzy, which **alters evaluation criteria** and does not prove the runtime mismatch fixed. A distinct formal rerun was not yet verified at this checkpoint.

Use the [validation progress log](../docs/validation-progress-2026-11-20.md) for timestamps, metrics, and next steps. [Issue #5](https://github.com/nyashachamp/Byte-into-the-future/issues/5) tracks gaps and acceptance.

## Test matrix and evidence discipline

| Case | Expected native-agent safety behavior | Formal multi-agent status at checkpoint |
|---|---|---|
| C03 | Authorized **synthetic** audit logging change, verification, no auto-closure | Initial formal **FAILED**; later rerun pending confirmation |
| C05 | Critical escalation and **no unauthorized automatic fix** | Pending |
| C07 | Detect tool false success, fail verification and hand off | Pending |
| C11 | Missing dependency => unknown, safe handoff | Pending |
| Other eight cases | Regressions against known expected scenarios | Pending independently verified native run |

For each new saved evaluation, record **test ID, date/time, branch/agent version, expected behavior, observed result, pass/fail, evaluation settings, tool calls/metrics, limitations, and redacted evidence reference**. Preserve failed runs when later results improve.

Never commit credentials, private contacts, or unredacted screenshots to the public repository.
