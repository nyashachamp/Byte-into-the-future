# Validation progress — 20 November 2026

Project: **Byte into the Future / Public Service Risk Dashboard (Civic Shield)**  
Workstream: **five-agent recovery**  
Submission target: **22 November 2026**  
Source: Team-lead screenshots and watsonx Orchestrate evaluations observed on 20 November.  
**Evidence standard:** Distinguish configured, observed, evaluated, and still-unverified capabilities.

## Five-agent deployment/configuration

- IBM Bob terminal reported successful Orchestrate imports of the following native agents: `orchestrator_agent`, `security_investigator`, `risk_analyst`, `response_agent`, and `verification_handoff_agent`.
- Existing `risk_analysis_agent` was preserved and reported updated.
- Team-lead inspection in watsonx Orchestrate showed `orchestrator_agent` connected to all **four specialist collaborators**, each with one associated tool.
- These findings substantiate the **configured five-agent topology**. They do **not** yet prove a published Live deployment, repeated successful delegation, or full 12-case acceptance.

## C03 — first Draft Preview (observed)

The orchestrator generated a synthetic case report:
- Finding: `CFG-LOGGING`, audit logging expected enabled but observed disabled.
- Risk: **medium**, priority **30**.
- Reported simulated response: `enable_audit_logging`.
- Reported independent verification: **PASSED**.
- Lifecycle ended as `awaiting_human_closure` rather than autonomous final closure.
- These are **simulated results**; no real infrastructure change is claimed.
- The original preview was not saved before navigating away, but report screenshots were retained. C03 was subsequently rerun and saved as an Orchestrate test.

## Saved test and formal evaluation

**Saved test:** `C03 - Five-Agent Workflow Verification` in **Evaluate > Tests**.

The Save as test dialog showed recorded test conditions for collaboration/tool invocations, including `chat_with_collaborator_security_investigator` and `investigate_case`.

**First formal evaluation (Nov 20, about 09:16 Pacific): FAILED.**
- Overall: **0/1 tests passed (0%)**.
- Tool calls recorded: **8**.
- Tool-call precision: **88%**.
- Tool-call recall: **88%**.
- Agent routing F1: **100%**.
- Journey completion: **88%**.
- Failure detail identified **parameter mismatch** for `investigator_result` passed to the risk/impact analysis tool (`analyze_impact` / `analyse_impact` spelling must be checked against deployed tool metadata).

**Code inspection:** `tools/analyst_pkg/analyze_impact.py` defines a Python string parameter `investigator_result`, documents it as JSON from `investigate_case`, and parses it via `json.loads()`. No production code change was made from this inspection.

**Test configuration adjustment:** The team lead changed the `investigator_result` comparison in the saved C03 test from **Exact** to **Fuzzy** and saved. This changes *evaluation matching*, not the agent's runtime data handling. The consequence is less strict comparison; it must not be reported as proof that the original parameter mismatch has been fixed in code.

**Rerun:** The next C03 evaluation was instructed. **Result pending confirmation** in this log; do not mark C03 fully passed on the basis of the changed matcher alone.

## Validation queue and exit criteria

| Scope | Current status | Required evidence |
|---|---|---|
| Five agent imports | Observed in IBM Bob | Import log/screenshot; confirm target workspace |
| Orchestrator collaborators | Observed in builder | Four collaborator assignments |
| C03 Draft Preview | Report generated | Screenshots retained; simulated outcomes only |
| C03 initial formal evaluation | **FAILED** | Evaluation report and parameter-failure detail |
| C03 matcher adjusted | Saved in test | Rerun outcome; ensure test remains meaningful |
| C05 critical escalation | Pending | No unauthorized automatic fix; human escalation |
| C07 false-success detection | Pending | Verification failure, escalation/handoff |
| C11 unknown dependency | Pending | Unknown handling and safe handoff |
| Full 12 synthetic cases | Pending independent multi-agent regression | Test case IDs, expected/actual, saved evaluations |
| Live publication | Not yet verified | Deployed version, accessibility, live test |
| Dashboard-to-Orchestrate connectivity | Not yet established | Do not claim live wiring without evidence |
| Final pitch/demo/submission | Pending | Working links, source branch, demo, submission receipt |

## Risk controls

- Preserve unchanged deterministic pipeline / fallback agent while evaluating the five-agent recovery.
- Do not upload raw screenshots or logs containing credentials, personal contact details, or API keys.
- Do not treat Fuzzy parameter matching as equivalent to an exact match or authorization-control proof.
- Continue recording *failures as well as passes*. Do not merge to `main` or state final acceptance until evidence supports it.

## Next record update

Record the rerun's actual outcome and metrics, then C05/C07/C11 and all twelve regressions. Record any validated change to code, agent definitions, tool metadata, and its deployment/version separately.
