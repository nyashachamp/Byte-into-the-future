# Public Service Risk Dashboard

**Team Byte into the Future** | IBM SkillsBuild AI Experiential Learning Lab | Track #4: Government & Public Services

A proposed multi-agent AI system designed to help government IT and cybersecurity teams detect security misconfigurations, understand how affected systems connect to essential public services, prioritize risks by citizen impact, and hand unresolved work to human responders with a complete, evidence-based case packet.

> **Design principle:** the AI handles permitted, low-risk analysis and documentation. Humans keep authority over critical actions, incident classification, recovery approval, and closure.

---

## The problem

Government security teams face alert overload, fragmented tools, hidden misconfigurations, and incomplete context when work changes hands. Our guiding question:

*How might we use agentic AI to help government agencies proactively identify security misconfigurations, assess vulnerabilities and incidents, understand technical dependencies, prioritize threats to essential public services, and complete authorized response work before handing unresolved tasks to human cybersecurity professionals?*

**Primary users:** government SOC analysts, IT operations staff, incident responders, and security managers.
**Example setting:** a simulated county government running public-facing applications, internal identity services, and emergency-related systems.

## Proposed agent architecture

| Agent / module | Responsibility | Key decision |
|---|---|---|
| Orchestrator | Tracks case state, plans tasks, routes work, preserves audit history | What should happen next? |
| Security Investigator | Validates configuration findings against approved baselines | Is this a confirmed finding? |
| Risk & Dependency Analyst | Maps affected assets to public services and estimates impact | What needs attention first? |
| Response Agent | Proposes or executes only explicitly authorized sandbox actions | Is this action permitted and safe? |
| Verification & Handoff | Independently checks results and prepares the analyst handoff | Resolved, retry safely, or escalate? |

### Data flow

```
Input / Perception      Synthetic alerts, configuration snapshots, asset inventory, service-dependency map
        ↓
Orchestrator / Planning Assigns agents, tracks workflow state, enforces authorization gates
        ↓
Memory / Knowledge      Approved baselines, response procedures, validated prior cases, audit trail
        ↓
Tools / Interfaces      Python validation functions, simulated APIs, SQL records, optional model service
        ↓
Execution               Read-only investigation, prioritization, authorized sandbox actions, handoff creation
        ↓
Verification / Feedback Deterministic tests; results and analyst corrections recorded for future cases
```

## Workflow

1. Receive a simulated alert or configuration finding and create a case record.
2. Validate evidence and compare the configuration with an approved baseline.
3. Assess severity, dependencies, and likely impact on public-service continuity.
4. Choose next action: gather evidence, recommend remediation, perform an authorized sandbox step, or escalate.
5. Check authorization and safety before any action. **Critical findings trigger immediate human notification.**
6. Execute the permitted action and independently verify the result.
7. If verification fails, retry only within bounded rules; otherwise stop and escalate with evidence.
8. Record outcome, analyst feedback, remaining tasks, and case status.

## Technologies

These are proposed tools, not a verified inventory of implemented integrations. IBM Bob use still needs supporting evidence.

| Tool | Purpose |
|---|---|
| IBM Bob | Required IBM development workflow |
| IBM watsonx Orchestrate (optional) | Potential workflow orchestration; access and adoption to be confirmed |
| IBM watsonx.ai / Granite (candidate) | Language reasoning, summarization, planning support |
| IBM Cloud (candidate) | Hosting and IBM service access; availability to be confirmed |
| Python | Baseline comparisons, simulated actions, validation, scoring |
| Synthetic JSON / CSV | Alerts, configurations, assets, service dependencies |
| SQLite | Case status, event logs, audit trail |
| Dashboard | Risk ranking, evidence, approval requests, handoffs |
| VS Code + GitHub | Development and team collaboration |

## MVP demonstration

Detect a misconfigured government cloud-storage resource in synthetic data, identify the affected public service, prioritize the finding, recommend or simulate an authorized correction, verify the state, and generate a structured human handoff when unresolved.

| Priority | Acceptance check |
|---|---|
| 1. Detect & validate | A known misconfiguration is flagged with evidence and a baseline reference |
| 2. Prioritize by service impact | The dashboard explains why the affected public service changes priority |
| 3. Verify & hand off | A successful sandbox action is verified; a failed or unsafe action produces a complete handoff |

## Development status

| Area | Repository evidence / remaining work |
|---|---|
| Project concept and agent design | Drafts included in `docs/`; team review and validation remain |
| Initial agents and dashboard prototype | Original Python/Streamlit source is staged in [`src/ghazal-project/`](src/ghazal-project/) for team review; implementation is not finalized and IBM integrations have not been validated |
| Initial system test without dataset | Reported by development; reproducible evidence and team sign-off are pending |
| Synthetic dataset | [12-case v1 fixture](data/samples/README.md) included; consistency validator passed; team review pending |
| Dataset-based testing and validation | Test plan, evaluator answers, and fixture validator included; dashboard integration and actual results pending |
| IBM Bob use | Required by the documented project brief; usage evidence missing |
| Video | No three-minute YouTube video link included |

See [Milestones and progress](docs/milestones.md) for the detailed evidence checklist.

## Repository structure

```
├── README.md            You are here
├── CONTRIBUTING.md      Team workflow and how to add code safely
├── .gitignore           Keeps keys, credentials, and large files out
├── .env.example         Template for local secrets (copy to .env, never commit .env)
├── docs/
│   ├── project-concept.md      Full integrated project concept
│   ├── week-4-deliverables.md  Architecture, workflow, tools (guide slides 17–19)
│   ├── milestones.md           Deliverables and progress tracker
│   └── original/               Original Word documents
├── src/                 Includes original prototype source staged for team review
├── data/
│   ├── samples/         12-case synthetic dataset and integration guide
│   ├── results/         Planned: test outputs (not yet present)
│   └── README.md        Data rules and documentation
└── tests/               Test plan, evaluator fixtures, and consistency validator
```

## Installation

The original prototype files are in [`src/ghazal-project/`](src/ghazal-project/). Its original README contains preliminary commands, but installation, dependencies, IBM integrations, and the full dataset workflow still need developer verification on a separate refinement branch. This is a baseline, not a finished team release.

## Data and safety rules

- Synthetic or properly authorized public data only. No real citizen data, personal information, or live government systems.
- No real credentials in the repo. API keys and IBM Cloud credentials live in a local `.env` file, which Git ignores.
- No live production changes. All actions run in a sandbox and are logged.

## Team

**Byte into the Future is a collaborative team project.** This branch preserves an initial contribution for review and development, not a finalized individual or team release. New development work should occur on a separate refinement branch and be reviewed by the team.

## Documentation

- [Consolidated security baselines and agent test catalog](docs/baseline-test-catalog.md)

- [Project concept](docs/project-concept.md)
- [Week 4 deliverables: architecture, workflow, tools](docs/week-4-deliverables.md)
- [Milestones and progress](docs/milestones.md)
- [Contributing guide](CONTRIBUTING.md)

The Markdown files are the maintained project documentation. Word documents in `docs/original/` are historical source copies and may contain earlier names or designs.
