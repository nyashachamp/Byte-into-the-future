# Five-Agent Recovery Plan

**Branch:** `recovery-five-agent-2026-11-19`  
**Team:** Byte into the Future | IBM SkillsBuild AI Experiential Learning Lab  
**Status: DESIGN PROPOSAL — pending implementation and team review**

> **Important:** This document describes planned work, not completed functionality.
> No application code, agent configurations, or test files have been created yet.
> The existing Python pipeline, Streamlit dashboard, and 12-case regression suite
> remain unchanged. Implementation begins only after this plan is reviewed and
> approved by the team.

---

## 1. Purpose

The repository already contains a correct, fully tested Python pipeline (`src/source-code/src/pipeline.py`) and a working single-agent watsonx Orchestrate deployment (`agents/risk_analysis_agent.yaml`). What is missing is the **five independently configured native watsonx Orchestrate agents** described in the project design documentation.

This plan describes how to close that gap — decomposing the monolithic pipeline into four specialist Python tool packages, writing five deployable native agent YAML specifications, and wiring the Orchestrator to its four collaborators using the watsonx Orchestrate `collaborators` field — without breaking any existing passing tests.

---

## 2. What must not change

The following are **preserved without modification** throughout all implementation phases:

| Artifact | Location | Reason |
|---|---|---|
| Monolithic pipeline (source of truth) | `src/source-code/src/pipeline.py` | Refactored to delegate, but output is identical |
| Streamlit dashboard | `src/source-code/src/dashboard.py` | Unchanged; calls `analyze()` directly |
| CLI entry point | `src/source-code/src/main.py` | Unchanged |
| 12-case synthetic dataset | `data/samples/public-service-risk-v1.json` | Unchanged |
| Evaluator-only expected outcomes | `tests/fixtures/public-service-risk-v1.expected.json` | Unchanged |
| Original single-agent WXO spec | `agents/risk_analysis_agent.yaml` | Preserved alongside new agents |
| Original tool package | `tools/risk_tool_pkg/` | Preserved; new packages are separate |
| All 20 existing tests | `src/source-code/tests/` and `tests/` | Must pass unchanged at every commit |

---

## 3. How watsonx Orchestrate collaboration works

The following platform constraints govern every design decision. These are grounded in the [watsonx Orchestrate ADK documentation](https://developer.watson-orchestrate.ibm.com/agents/build_agent).

**3.1 The `collaborators` field is the delegation mechanism.**  
A native agent's YAML lists other already-imported agents by name under `collaborators`. The Orchestrator's LLM — running with `style: react_core`, the documented style for multi-agent workflows — uses each collaborator's `description` field to decide which agent to route a request to. Delegation is a live LLM function-call to that collaborator; the collaborator is an independent Orchestrate entity with its own LLM, tools, and instructions.

**3.2 Import order is bottom-up.**  
A collaborator agent must be imported into the platform before any supervisor that names it. The required order is: Python tools first → specialist agents → Orchestrator last.

**3.3 Each specialist agent owns exactly one Python tool.**  
There is no shared tool. Each specialist's capability is exposed as a narrow `@tool`-decorated Python function that wraps exactly the pipeline logic belonging to that agent. The specialist agent's YAML names that tool under `tools:`.

**3.4 The Orchestrator has no tools — only collaborators.**  
It delegates all substantive work. Its `instructions` tell the LLM exactly when to call each of the four specialist agents and in what order.

**3.5 Collaborator `description` fields must be routing-precise.**  
The ADK documentation states: *"Supervisor agents use the description of collaborator agents when determining where to route a request."* Each specialist description names the tool it uses and exactly when to call it.

---

## 4. Proposed architecture

```
User / Chat UI
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│  Orchestrator Agent  (agents/orchestrator_agent.yaml)   │
│  style: react_core  │  tools: []                        │
│  collaborators:                                          │
│    - security_investigator                               │
│    - risk_analyst                                        │
│    - response_agent                                      │
│    - verification_handoff_agent                          │
└──────────┬──────────────┬────────────┬──────────────────┘
           │              │            │            │
           ▼              ▼            ▼            ▼
  Security         Risk &        Response    Verification &
  Investigator     Dependency    Agent       Handoff Agent
  Agent            Analyst Agent
  tools:           tools:        tools:      tools:
  - investigate_   - analyse_    - execute_  - verify_and_
    case             impact        response    handoff
       │               │               │           │
       ▼               ▼               ▼           ▼
  investigator_   analyst_pkg/  response_pkg/ verifier_pkg/
  pkg/            analyse_      execute_      verify_and_
  investigate_    impact.py     response.py   handoff.py
  case.py
       │               │               │           │
       └───────────────┴───────────────┴───────────┘
                               │
                     src/source-code/src/
                     agents/ (four modules)
                     ← extracted from pipeline.py
```

The four Python tool packages each contain their own copy of `pipeline.py` and the dataset, mirroring the pattern already established by `tools/risk_tool_pkg/`.

---

## 5. Inter-agent data contracts

Each specialist agent receives a JSON string input from the Orchestrator and returns a JSON string result. The Orchestrator accumulates results across the four sequential calls and assembles the final case summary for the user.

### 5.1 Input to Security Investigator

```json
{
  "case_id": "C03"
}
```

### 5.2 InvestigatorResult — returned to Orchestrator

```json
{
  "case_id": "C03",
  "assessment": "confirmed",
  "rules_violated": [
    {"id": "CFG-LOGGING", "field": "audit_logging_enabled", "weight": 10}
  ],
  "errors": [],
  "evidence": ["CFG-LOGGING: audit_logging_enabled expected True, observed False"],
  "confidence": 1.0,
  "asset_id": "AST-PERMIT",
  "asset_classification": "internal",
  "service_ids": ["SVC-PERMIT"]
}
```

### 5.3 Input to Risk & Dependency Analyst

```json
{
  "case_id": "C03",
  "investigator_result": "<InvestigatorResult JSON string>"
}
```

### 5.4 AnalystResult — returned to Orchestrator

```json
{
  "case_id": "C03",
  "score": 30,
  "severity": "medium",
  "notify_first": false,
  "public_restricted": false,
  "service_ids": ["SVC-PERMIT"],
  "affected_public_service": "Fictional county permit portal"
}
```

### 5.5 Input to Response Agent

```json
{
  "case_id": "C03",
  "investigator_result": "<InvestigatorResult JSON string>",
  "analyst_result": "<AnalystResult JSON string>"
}
```

### 5.6 ResponseResult — returned to Orchestrator

```json
{
  "case_id": "C03",
  "action_taken": "enable_audit_logging",
  "action_attempts": 1,
  "action_result": "success",
  "post_state": {
    "public_read": false,
    "encryption_enabled": true,
    "audit_logging_enabled": true
  },
  "events": [
    {"sequence": 1, "event": "action_attempt", "detail": "Attempt 1: enable_audit_logging"},
    {"sequence": 2, "event": "tool_result", "detail": "Tool reported success."}
  ]
}
```

### 5.7 Input to Verification & Handoff Agent

```json
{
  "case_id": "C03",
  "investigator_result": "<InvestigatorResult JSON string>",
  "analyst_result": "<AnalystResult JSON string>",
  "response_result": "<ResponseResult JSON string>"
}
```

### 5.8 VerifierResult — final answer returned to Orchestrator

```json
{
  "case_id": "C03",
  "verification_result": "passed",
  "outcome": "verified_awaiting_human_closure",
  "handoff_required": false,
  "lifecycle_status": "awaiting_human_closure",
  "human_intervention": ["Review evidence and approve final case closure."],
  "completed_ai_work": [
    "Loaded case from public-service-risk-v1",
    "Validated snapshot without coercing types",
    "Compared observed settings with the approved baseline",
    "Mapped the asset to its simulated public service",
    "Applied the policy gate",
    "Read post-action state independently"
  ],
  "outstanding_human_work": ["Review evidence and approve final case closure."],
  "decision_points": [
    "Human approval is required before closure or any unapproved correction."
  ],
  "events": [
    {"sequence": 1, "event": "action_attempt", "detail": "Attempt 1: enable_audit_logging"},
    {"sequence": 2, "event": "tool_result", "detail": "Tool reported success."},
    {"sequence": 3, "event": "verification", "detail": "Independent verification passed."}
  ]
}
```

---

## 6. Five agent specifications (proposed)

### 6.1 Security Investigator — `agents/security_investigator_agent.yaml`

| Field | Value |
|---|---|
| `name` | `security_investigator` |
| `style` | `react_core` |
| `tools` | `[investigate_case]` |
| `collaborators` | `[]` |
| Responsibility | Validate snapshot types, check exception suppression, compare baseline rules |
| Key decision | Is this a confirmed finding, compliant, or invalid input? |

### 6.2 Risk & Dependency Analyst — `agents/risk_analyst_agent.yaml`

| Field | Value |
|---|---|
| `name` | `risk_analyst` |
| `style` | `react_core` |
| `tools` | `[analyse_impact]` |
| `collaborators` | `[]` |
| Responsibility | Map asset to public service, compute priority score, determine notification requirement |
| Key decision | What needs attention first, and must a human be notified before action? |

### 6.3 Response Agent — `agents/response_agent.yaml`

| Field | Value |
|---|---|
| `name` | `response_agent` |
| `style` | `react_core` |
| `tools` | `[execute_response]` |
| `collaborators` | `[]` |
| Responsibility | Check policy + authorization gate, execute the allowlisted simulated action, bounded retry |
| Key decision | Is this action permitted, authorized, and safe to run? |

### 6.4 Verification & Handoff Agent — `agents/verification_handoff_agent.yaml`

| Field | Value |
|---|---|
| `name` | `verification_handoff_agent` |
| `style` | `react_core` |
| `tools` | `[verify_and_handoff]` |
| `collaborators` | `[]` |
| Responsibility | Read post-action state independently, determine outcome, build handoff packet |
| Key decision | Resolved, hand off, or escalate? |

### 6.5 Orchestrator — `agents/orchestrator_agent.yaml`

| Field | Value |
|---|---|
| `name` | `orchestrator_agent` |
| `style` | `react_core` |
| `tools` | `[]` |
| `collaborators` | `[security_investigator, risk_analyst, response_agent, verification_handoff_agent]` |
| Responsibility | Receive case requests, route to specialists in order, enforce notification-before-action, assemble final summary |
| Key decision | What should happen next? |

---

## 7. Authorization safeguards

The following invariants are enforced inside `execute_response.py` (the Response Agent's tool). They cannot be bypassed by the Orchestrator or any other agent.

| Invariant | Description |
|---|---|
| Allowlist gate | Action must appear in `policy["allowlisted_simulated_actions"]`; currently only `enable_audit_logging` |
| Sandbox-only gate | `case["authorization"]["sandbox_only"]` must be exactly `True` (strict boolean, not truthy) |
| Expiry gate | Authorization must not be expired relative to the dataset `simulation_clock` |
| Public-restricted gate | Assets with `classification == "restricted_synthetic"` and a `CFG-PUBLIC` violation never receive automatic correction, regardless of authorization |
| Retry limit | At most `min(2, case["simulation"]["max_attempts"])` attempts; never retries after `success_without_change` |
| Notification order | The Orchestrator emits the notification event *before* calling the Response Agent whenever `notify_first` is true (C04, C05) |

These match the existing invariants in `pipeline.py` and are verified by the existing `test_pipeline.py` and `test_wxo_tool.py` tests plus the new `test_response_agent.py` added in Phase 0.

---

## 8. Phased implementation

### Phase 0 — Pipeline decomposition (commit M0)

**Goal:** extract four agent logic modules from `pipeline.py`; refactor `analyze()` to delegate to them; add 23 unit tests. No WXO changes.

**Files to create:**

```
src/source-code/src/agents/__init__.py
src/source-code/src/agents/investigator.py
src/source-code/src/agents/analyst.py
src/source-code/src/agents/response_agent.py
src/source-code/src/agents/verifier.py

src/source-code/tests/test_investigator.py    (6 tests)
src/source-code/tests/test_analyst.py         (5 tests)
src/source-code/tests/test_response_agent.py  (7 tests)
src/source-code/tests/test_verifier.py        (5 tests)
```

**Files to modify:**

```
src/source-code/src/pipeline.py   → analyze() delegates; CaseResult output identical
```

**Checkpoint:** `python -m pytest src/source-code/tests/ tests/ -v` — 20 original + 23 new = 43 tests pass.  
**Commit M0:** `feat: extract four agent logic modules; pipeline delegates; all 43 tests pass`

---

### Phase 1 — Four specialist tool packages (commit M1)

**Goal:** create four independent Python tool packages, one per specialist, each with a `@tool` entry point, its own copy of the agent module, `pipeline.py`, dataset, and `requirements.txt`.

**Files to create:**

```
tools/investigator_pkg/
  investigate_case.py          ← @tool(permission=READ_ONLY)
  agents/__init__.py
  agents/investigator.py       ← synced copy
  pipeline.py                  ← synced copy
  data/public-service-risk-v1.json  ← synced copy
  requirements.txt

tools/analyst_pkg/             ← same structure, analyse_impact.py
tools/response_pkg/            ← same structure, execute_response.py
tools/verifier_pkg/            ← same structure, verify_and_handoff.py
```

**Tool entry-point signatures:**

```python
# investigate_case.py
@tool(permission=ToolPermission.READ_ONLY)
def investigate_case(case_id: str) -> dict:
    """Validate the configuration snapshot for one case against the approved baseline.
    Returns assessment, violated rules, evidence, and input errors.
    Call this first for every case. All actions are synthetic simulations only."""

# analyse_impact.py
@tool(permission=ToolPermission.READ_ONLY)
def analyse_impact(case_id: str, investigator_result: str) -> dict:
    """Map the case asset to its public service and compute the priority score.
    Returns score, severity, notification requirement, and service context.
    Call this after investigate_case. Pass the investigator_result as a JSON string."""

# execute_response.py
@tool(permission=ToolPermission.READ_ONLY)
def execute_response(case_id: str, investigator_result: str, analyst_result: str) -> dict:
    """Check authorization and execute the allowlisted simulated action if permitted.
    Returns action taken, attempts, result, and post-action state.
    Never retries after success_without_change. Never acts on restricted synthetic data."""

# verify_and_handoff.py
@tool(permission=ToolPermission.READ_ONLY)
def verify_and_handoff(case_id: str, investigator_result: str,
                       analyst_result: str, response_result: str) -> dict:
    """Read post-action state independently and prepare the human handoff packet.
    Returns verification result, outcome, lifecycle status, and all handoff fields.
    Human closure is always required."""
```

**Files to extend:**

```
tests/test_sync.py                     → 8 new sync assertions (agent module + pipeline copies × 4 packages)
tests/test_wxo_specialist_tools.py     → 12 new offline tool wrapper tests
```

**Checkpoint:** 43 + 12 = 55 tests pass. All four tool packages importable offline.  
**Commit M1:** `feat: four specialist tool packages with @tool wrappers and offline tests`

---

### Phase 2 — Five deployable agent YAML specs (commit M2)

**Goal:** write five complete, importable native agent YAML files in `agents/`.

**Files to create:**

```
agents/security_investigator_agent.yaml
agents/risk_analyst_agent.yaml
agents/response_agent.yaml
agents/verification_handoff_agent.yaml
agents/orchestrator_agent.yaml
```

Each YAML contains: `spec_version: v1`, `kind: native`, `name`, `llm: groq/openai/gpt-oss-120b`, `style: react_core`, `description` (routing-precise), `instructions`, `tools`, `collaborators`.

**Files to update (non-executable stubs → annotated references):**

```
src/source-code/agents/configuration_agent.yaml   → note pointing to security_investigator_agent.yaml
src/source-code/agents/impact_agent.yaml          → note pointing to risk_analyst_agent.yaml
src/source-code/agents/prioritization_agent.yaml  → note pointing to risk_analyst_agent.yaml
src/source-code/agents/policy_gate.yaml           → note pointing to response_agent.yaml
src/source-code/agents/handoff_agent.yaml         → note pointing to verification_handoff_agent.yaml
```

**Checkpoint:** `python -m pytest tests/test_delegation.py -v` — 5 structural YAML tests pass offline.  
**Commit M2:** `feat: five deployable native agent YAML specs`

---

### Phase 3 — Import and delete scripts (commit M3)

**Goal:** update `scripts/import-all.ps1` and `scripts/delete-all.ps1` to implement the correct bottom-up import and top-down removal orders.

**Import order (bottom-up):**

```
Step 1  Sync all copies (pipeline.py × 5, dataset × 5, agent modules × 4)
Step 2  Import Python tools:
          investigate_case
          analyse_impact
          execute_response
          verify_and_handoff
          analyze_risk_cases  (original — preserved)
Step 3  Import specialist agents (before Orchestrator):
          security_investigator_agent.yaml
          risk_analyst_agent.yaml
          response_agent.yaml
          verification_handoff_agent.yaml
Step 4  Import Orchestrator (after all collaborators are present):
          orchestrator_agent.yaml
Step 5  Import original single agent (preserved):
          risk_analysis_agent.yaml
```

**Removal order (reverse):**

```
orchestrator_agent → verification_handoff_agent → response_agent →
risk_analyst → security_investigator → risk_analysis_agent →
verify_and_handoff → execute_response → analyse_impact →
investigate_case → analyze_risk_cases
```

**Commit M3:** `feat: update import/delete scripts for five-agent bottom-up deployment`

---

### Phase 4 — Delegation acceptance tests (commit M4)

**Goal:** structural offline tests verifying YAML consistency; live smoke tests verifying actual delegation.

**Files to create:**

```
tests/test_delegation.py        (5 offline structural tests)
tests/test_live_delegation.py   (5 live smoke tests, skipped when WXO_LIVE_TESTS≠1)
```

**Offline structural tests (`test_delegation.py`):**

| Test | Assertion |
|---|---|
| `test_orchestrator_has_four_collaborators_and_no_tools` | `len(collaborators)==4`, `tools==[]` |
| `test_specialist_agents_have_no_collaborators` | All four specialists have `collaborators: []` |
| `test_orchestrator_collaborator_names_match_agent_names` | Each `collaborators` entry matches a `name:` field in a specialist YAML |
| `test_specialist_tools_match_entrypoint_function_names` | Tool name in YAML matches `def <name>` in the corresponding `.py` file |
| `test_all_five_agents_use_react_core` | `style: react_core` for all five |

**Live smoke tests (`test_live_delegation.py`) — skipped offline:**

| Test | Pass condition |
|---|---|
| `test_orchestrator_exists_in_platform` | `orchestrator_agent` appears in `orchestrate agents list` |
| `test_all_five_agents_listed` | All five `name:` values appear in `orchestrate agents list` |
| `test_all_four_tools_listed` | All four tool function names appear in `orchestrate tools list` |
| `test_orchestrator_chat_c03_delegates` | Chat response shows reasoning steps calling all four specialists; outcome `verified_awaiting_human_closure` |
| `test_orchestrator_chat_c05_notifies_before_no_action` | Notification event precedes any action; `handoff_required: true`; Response Agent returns zero attempts |

**Checkpoint:** 55 + 5 = 60 offline tests pass.  
**Commit M4:** `feat: delegation acceptance tests — structural (offline) and live smoke tests`

---

### Phase 5 — Evidence and milestone update (commit M5)

**Goal:** run the pipeline, save results, compare against acceptance criteria, update the milestone tracker.

**Files to create:**

```
data/results/pipeline-run-all-cases.json
data/results/acceptance-criteria-comparison.md
```

**Files to update:**

```
docs/milestones.md   → mark five-agent POC items as complete with evidence references
```

**Commit M5:** `evidence: five-agent POC results, acceptance criteria, milestone update`

---

## 9. Complete file inventory (proposed)

### New files

```
src/source-code/src/agents/__init__.py
src/source-code/src/agents/investigator.py
src/source-code/src/agents/analyst.py
src/source-code/src/agents/response_agent.py
src/source-code/src/agents/verifier.py

src/source-code/tests/test_investigator.py
src/source-code/tests/test_analyst.py
src/source-code/tests/test_response_agent.py
src/source-code/tests/test_verifier.py

tools/investigator_pkg/  (investigate_case.py, agents/, pipeline.py, data/, requirements.txt)
tools/analyst_pkg/       (analyse_impact.py, agents/, pipeline.py, data/, requirements.txt)
tools/response_pkg/      (execute_response.py, agents/, pipeline.py, data/, requirements.txt)
tools/verifier_pkg/      (verify_and_handoff.py, agents/, pipeline.py, data/, requirements.txt)

agents/orchestrator_agent.yaml
agents/security_investigator_agent.yaml
agents/risk_analyst_agent.yaml
agents/response_agent.yaml
agents/verification_handoff_agent.yaml

tests/test_delegation.py
tests/test_live_delegation.py
tests/test_wxo_specialist_tools.py

data/results/pipeline-run-all-cases.json         (Phase 5)
data/results/acceptance-criteria-comparison.md   (Phase 5)
```

### Files to modify

```
src/source-code/src/pipeline.py     → delegates to four modules; CaseResult output unchanged
tests/test_sync.py                  → adds 8 sync assertions for four new packages
scripts/import-all.ps1              → bottom-up import order for all five agents + tools
scripts/delete-all.ps1              → reverse removal order
docs/milestones.md                  → Phase 5 update
```

### Files to annotate (stubs updated with canonical reference, not deleted)

```
src/source-code/agents/configuration_agent.yaml
src/source-code/agents/impact_agent.yaml
src/source-code/agents/prioritization_agent.yaml
src/source-code/agents/policy_gate.yaml
src/source-code/agents/handoff_agent.yaml
```

### Files left completely untouched

```
src/source-code/src/main.py
src/source-code/src/dashboard.py
src/source-code/src/__init__.py
data/samples/public-service-risk-v1.json
tests/fixtures/public-service-risk-v1.expected.json
tests/validate_synthetic_dataset.py
agents/risk_analysis_agent.yaml
tools/risk_tool_pkg/analyze_risk_cases.py
tools/risk_tool_pkg/pipeline.py
src/source-code/tests/test_pipeline.py
tests/test_wxo_tool.py
tests/test_sync.py  (extended but not replaced)
```

---

## 10. Test count checkpoints

| Commit | New tests | Offline total |
|---|---|---|
| Baseline | — | 20 |
| M0 — agent modules | +23 | 43 |
| M1 — specialist tool wrappers | +12 | 55 |
| M2 — YAML structural | +5 | 60 |
| M4 — delegation (offline) | (included above) | 60 |
| M4 — delegation (live, skipped offline) | +5 | 60 offline / 65 live |

The 20 original tests in `src/source-code/tests/test_pipeline.py` and `tests/test_wxo_tool.py` must pass at every commit without modification.

---

## 11. Delegation verification protocol (post-import)

After `scripts/import-all.ps1` completes, the following manual checks confirm that actual delegation is occurring. Screenshots of steps 4–7 are saved to `docs/testing-evidence/` as IBM Bob usage evidence.

| Step | Command | Pass condition |
|---|---|---|
| 1 | `orchestrate agents list` | Five new names visible alongside original `risk_analysis_agent` |
| 2 | `orchestrate tools list` | `investigate_case`, `analyse_impact`, `execute_response`, `verify_and_handoff` present |
| 3 | Export Orchestrator YAML and inspect | `collaborators:` lists four agents; `tools: []` |
| 4 | `orchestrate chat ask --agent-name orchestrator_agent "Analyse case C03"` | Reasoning trace shows calls to all four specialists; outcome `verified_awaiting_human_closure` |
| 5 | `orchestrate chat ask --agent-name orchestrator_agent "Analyse case C05"` | Notification event before any action; `handoff_required: true`; zero action attempts |
| 6 | `orchestrate chat ask --agent-name orchestrator_agent "Analyse case C07"` | Verification `failed`; outcome `handoff`; no retry suggested |
| 7 | `orchestrate chat ask --agent-name orchestrator_agent "Analyse case C11"` | Score `null`; severity `unknown`; handoff required |

---

## 12. Commit milestones

```
M0  feat: extract four agent logic modules; pipeline delegates; all 43 tests pass
M1  feat: four specialist tool packages with @tool wrappers and offline tests
M2  feat: five deployable native agent YAML specs
M3  feat: update import/delete scripts for five-agent bottom-up deployment
M4  feat: delegation acceptance tests — structural (offline) and live smoke tests
M5  evidence: five-agent POC results, acceptance criteria, milestone update
```

Each commit is independently green. No commit reduces the passing test count.

---

## 13. Open questions for team review

Before implementation begins, the following items require team confirmation:

1. **LLM access:** Confirm `groq/openai/gpt-oss-120b` is available in the team's Orchestrate environment, or provide the preferred model identifier.
2. **Tool package sync mechanism:** Confirm whether the existing `import-all.ps1` sync pattern (byte-copy via `[System.IO.File]::WriteAllBytes`) is acceptable for the four new packages, or whether a different approach is preferred.
3. **Stub YAML handling:** Confirm whether the five `src/source-code/agents/` stubs should be annotated (pointing to canonical files) or removed.
4. **Live test environment:** Confirm whether `WXO_LIVE_TESTS` should be part of the CI configuration or run manually only.
5. **IBM Bob evidence:** Confirm that the delegation trace screenshots (Step 4–7 of Section 11) satisfy the IBM Bob usage evidence requirement.

---

## 14. References

- [watsonx Orchestrate ADK — Configuring native agents](https://developer.watson-orchestrate.ibm.com/agents/build_agent)
- [watsonx Orchestrate ADK — Agent styles (ReAct Core)](https://developer.watson-orchestrate.ibm.com/agents/agent_styles)
- [watsonx Orchestrate ADK — Foundational architecture (decompose and delegate)](https://developer.watson-orchestrate.ibm.com/agents/agent_design/foundational_architecture)
- [Project concept (this repository)](project-concept.md)
- [Week 4 deliverables — agent architecture, workflow, tools](week-4-deliverables.md)
- [Milestones and progress](milestones.md)
- [Consolidated baseline and agent test catalog](baseline-test-catalog.md)
