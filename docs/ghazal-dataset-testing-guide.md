# Ghazal: connect the dataset and run the tests

This guide is a team review checklist for connecting the 12-case synthetic dataset. The original prototype is preserved on the `ghazal-initial-code` branch, not yet merged into `main`. The 12-case integration and final setup remain unverified; the examples below are not completed implementation.

## 1. Get the latest files

In VS Code, open the Byte-into-the-future repository and use Source Control → Pull. Make changes on a new working branch based on `ghazal-initial-code`, leaving the baseline untouched. If the repository is not yet local, clone it with:

```text
https://github.com/nyashachamp/Byte-into-the-future.git
```

Keep your existing work and credentials safe when copying your project into `src/`. Follow [CONTRIBUTING.md](../CONTRIBUTING.md).

Open the terminal at the repository root: the folder containing `README.md`, `src/`, `data/`, and `tests/`.

## 2. Check the dataset first

With Python 3.9 or newer, run:

```powershell
python tests/validate_synthetic_dataset.py
```

On Windows, if your Python installation uses the launcher, try:

```powershell
py -3 tests/validate_synthetic_dataset.py
```

You should see `PASS: 12 fixture cases...`. This checks the dataset and answer labels. It does **not** run your agents or test the dashboard.

## 3. Load one case into your existing workflow

The input file is `data/samples/public-service-risk-v1.json`. This Python example loads C03, the simplest successful correction:

```python
import json
from copy import deepcopy
from pathlib import Path

# Run from the repository root.
dataset = json.loads(
    Path("data/samples/public-service-risk-v1.json").read_text(encoding="utf-8")
)
case = deepcopy(next(c for c in dataset["cases"] if c["id"] == "C03"))
asset = next(a for a in dataset["assets"] if a["id"] == case["asset_id"])
baseline = next(b for b in dataset["baselines"] if b["id"] == case["baseline_id"])

agent_input = {
    "case": case,
    "asset": deepcopy(asset),
    "services": deepcopy([
        s for s in dataset["services"] if s["id"] in asset["service_ids"]
    ]),
    "baseline": deepcopy(baseline),
    "exceptions": deepcopy([
        e for e in dataset["exceptions"] if e["id"] in case["exception_ids"]
    ]),
    "policy": deepcopy(dataset["policy"]),
    "simulation_clock": dataset["simulation_clock"],
}
# NEXT: pass agent_input to your existing Orchestrator entry point.
# Example only: result = your_orchestrator.run(agent_input)
```

If your agents expect different field names, add a small adapter that maps these fields to your existing input format. Preserve the case ID.

Keep `tests/fixtures/public-service-risk-v1.expected.json` out of agent prompts, memory, and retrieval. It is the answer key for the test harness.

## 4. Give each module the information it needs

| Module | Input and job |
|---|---|
| Orchestrator | Accept the case; track state, tool calls, notifications, and results |
| Security Investigator | Compare snapshot booleans against baseline rules; check exact asset/rule exceptions |
| Risk & Dependency Analyst | Use the asset's service IDs and linked criticality to calculate and explain priority |
| Response Agent | Check mock authorization and policy; call only the simulated action tool |
| Verification & Handoff | Read the simulated state independently; verify corrections or prepare the handoff |

Validate all three snapshot fields as actual JSON booleans before assessment. C09 has a missing field; C10 has a string instead of a boolean. Request corrected data and make no action calls for either case.

Use `simulation_clock`, not today's date, when checking expiry. Each case has its own fresh state. Clear case memory, tool attempt counters, and case-store records between runs, or use a separate run ID.

## 5. Replace real action tools with a simulation

Use an in-memory copy of `case["snapshot"]`. Do not connect these fixtures to real storage, accounts, or infrastructure.

Before calling a tool, enforce the dataset policy in code: valid input, known service mapping, sandbox mode, unexpired authorization, and the action explicitly listed in both the allowlist and that case's authorization. The only allowed simulated correction is `enable_audit_logging`.

Your test harness reads `case["simulation"]["tool_behavior"]` and configures a mock tool:

| Behavior | What the mock tool does |
|---|---|
| `success` | Set `audit_logging_enabled` to true in the copied state; return success |
| `success_without_change` | Return success but leave the state unchanged |
| `transient_then_success` | Return a temporary error on attempt 1; on attempt 2 set logging true and return success |
| `not_called` | Treat any attempted action as a failed test |

Keep the simulated behavior in the test harness/tool stub; agents should discover action results through tool responses and independent verification. The verification module must read the copied state rather than trust the tool's success message.

Allow at most two attempts for transient errors. A claimed success with unchanged state must fail verification and produce a handoff without a retry.

## 6. Show the result on the dashboard

Add a clearly labeled **Synthetic test mode** and a case selector, or feed cases through your existing data-loading route.

Display the case ID, affected asset, public service, finding and baseline evidence, priority score and explanation, actions attempted, verification result, remaining human tasks, and workflow status.

Also record ordered events with timestamps or sequence numbers: notification, action attempt, tool result, verification, and handoff. These let you check that notification happened before action.

Do not display the expected answer as the actual agent result. Show C11's missing service impact and score as **Unknown**, not zero. Do not automatically close any case; successful verification still awaits human closure approval.

## 7. Run the cases in this order

Start with C03, then C01 and C02, then C04 and C05. After those work, run C06–C12.

| Case | What must happen |
|---|---|
| C01 | No finding, score 0, no action |
| C02 | Approved public-read exception applies; no finding or action |
| C03 | Logging finding, score 30; one action; verification passes; human closure pending |
| C04 | Logging finding, score 60; notify before one action; verification passes; human closure pending |
| C05 | Public-access finding, score 100; notify immediately; zero actions; handoff |
| C06 | Logging finding, score 30; zero actions; request approval |
| C07 | Logging finding, score 30; one action; verification fails; handoff |
| C08 | Logging finding, score 30; temporary error then one retry; verification passes; human closure pending |
| C09 | Invalid input; score unknown; request data; zero actions |
| C10 | Invalid input; score unknown; request data; zero actions |
| C11 | Logging finding; service and priority unknown; zero actions; handoff |
| C12 | Encryption finding, score 50; zero actions; request approval |

The evaluator-only expected file contains the exact assessment, rule IDs, scores, action counts, verification labels, and outcomes. Normalize your output names in the adapter if needed; compare the same meaning.

A case passes only when the actual result matches these expectations **and** its evidence, notification order, and handoff details are correct. For handoffs and approval requests, include case identity, owner/timestamps, impact or unknown impact, evidence and baseline, completed work, verification, outstanding tasks, requested approvals, and next checkpoint/closure criteria.

## 8. Save actual results

Create `data/results/` and save each run's actual outputs and event log, plus a summary such as:

```text
Run ID:
Date:
Code version:
Dataset: public-service-risk-v1
Python/runtime and model version:
Command or dashboard steps used:

Case | Pass/Fail | Actual outcome | Evidence/output file | Notes
C01  |           |                |                      |
...
C12  |           |                |                      |
```

Count successful detection over the 8 positive cases. Count false positives over the 2 compliant cases. Report invalid-input rejection separately for C09/C10. Do not count the dataset validator as an end-to-end test, and do not report a case as passing without running it.

## 9. Add the missing startup instructions

Once the connection works, upload your source and add the actual commands to the root README for installing dependencies, starting the agents/dashboard, and running the 12-case harness. Record any required model settings or environment-variable names without committing secret values.

The original prototype and draft startup instructions are present on `ghazal-initial-code`; they have not been verified as a clean install or against the full 12-case dataset. On `main`, the fixture validator remains the documented executable check. Verify commands and record actual results on the new refinement branch.
