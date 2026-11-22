# IBM watsonx Orchestrate — Agent Launch and Execution Record

**Project:** Civic Shield / Public Service Risk Dashboard  
**Team:** Byte into the Future!  
**Environment:** IBM watsonx Orchestrate (team-reported London / eu-gb workspace; identifiers intentionally omitted here)  
**Evidence cutoff:** November 21, 2026  
**Scope:** Synthetic, sandboxed public-service cybersecurity cases. This is not a production government integration.

## What the team accomplished

The team **created and imported native AI agents and tools into IBM watsonx Orchestrate**, configured a multi-agent system, and **executed synthetic cases through Draft Preview** while inspecting actual workflow traces.

The configured system includes **one supervisor/orchestrator and four specialist agents**:

| Role | Source definition | Tool/operation |
|---|---|---|
| Orchestrator | [`agents/orchestrator_agent.yaml`](../agents/orchestrator_agent.yaml) | `civic_shield_pipeline`; asynchronous flow status |
| Security Investigator | [`agents/security_investigator_agent.yaml`](../agents/security_investigator_agent.yaml) | `investigate_case` |
| Risk & Dependency Analyst | [`agents/risk_analyst_agent.yaml`](../agents/risk_analyst_agent.yaml) | `analyse_impact` |
| Response Agent | [`agents/response_agent.yaml`](../agents/response_agent.yaml) | `execute_response` |
| Verification & Handoff | [`agents/verification_handoff_agent.yaml`](../agents/verification_handoff_agent.yaml) | `verify_and_handoff` |

This is a **five-agent system**, not five specialists. Gate, aggregation, and End nodes are workflow components rather than extra agents.

## Agent launch and execution: separate milestones

| Stage | Evidence in project records | Qualified conclusion |
|---|---|---|
| Agent design and source definitions | Five native YAML configurations and Python tool packages committed | **Versioned in GitHub** |
| Tools and native agents imported | IBM Bob terminal import success reported; team lead observed agents in Orchestrate builder | **Imported/configured in the IBM development environment** |
| Orchestrator routing updated | Final reported export shows `collaborators: []`, `civic_shield_pipeline` and `i__get_flow_status_intrinsic_tool__`; four specialists retained | **Configuration reported and represented in source** |
| Draft Preview workflow execution | Saved Flow Inspector trace analyses for all C01–C12; documented seven-node case flow | **Actual development-environment executions reviewed** |
| Safety/acceptance validation | Previous 12 current-flow traces: 10 scenario outcomes accepted and C09/C10 failed handoff/error consistency; subsequent Bob-reported local corrections | **Historical Draft Preview acceptance was 10/12; not proof of a fresh corrected 12/12 cloud pass** |
| Offline regression | Bob-reported 79 tests passed, 12 skipped; 33 additional invariant checks passed | **Reported local validation, not Live runtime validation** |
| Published Live agent version | No verified Live version ID, published version screenshot, or production endpoint test in the record | **Not independently established** |
| Streamlit dashboard calling watsonx | An optional API client exists, but a credentialed end-to-end dashboard-to-Orchestrate run is not independently confirmed | **Integration not independently verified** |
| IBM Code Engine hosting | Earlier attempt was not completed | **Not claimed** |

## How the orchestrated workflow operates

1. The analyst requests a synthetic case (C01–C12).
2. `orchestrator_agent` invokes `civic_shield_pipeline` instead of delegating directly.
3. The flow executes the Security Investigator, Risk Analyst, notification/authorization gate, Response Agent, and Verification & Handoff stages, followed by aggregation and End.
4. The orchestrator polls asynchronous flow status and only presents a completed report if the result explicitly confirms all required stages.
5. Synthetic actions do not change real systems. Human approval governs unresolved findings and case closure.

**Important architecture refinement:** The initial multi-agent design used direct collaborators. During remediation, direct collaborator routing was removed from the orchestrator to prevent bypass of the deterministic flow and its safeguards. The current [orchestrator YAML](../agents/orchestrator_agent.yaml) shows `collaborators: []`. A deployed configuration export was reported, but this is not equivalent to independently verified final Live publication.

## Reproduction and launch evidence

The repository contains [an import script](../scripts/import-all.ps1) and agent/tool definitions. The import script is **historical** and must be inspected before reuse: it imports legacy assets as well as the five-agent arrangement and does **not** by itself establish that the final `civic_shield_pipeline` flow is deployed. Do not run it against a live workspace automatically. Confirm the target environment and current IBM CLI/API behavior, protect rollback copies, review intended changes, and use least-privilege credentials.

Read-only verification should establish:
- Which IBM workspace/environment is selected
- Which five agent definitions and specialist tool versions are installed
- Whether the supervisor's actual tool list and zero-collaborator state match source
- Whether the registered flow is the intended corrected seven-node version
- Whether Draft Preview traces demonstrate the required output contract
- Whether any specific Live published version exists

**Do not put API keys, tokens, unredacted tenant identifiers, or confidential trace exports in this public repository.**

## Resource limits and cross-tool completion

The team lead reported exhausting the practical IBM Bob credit/token budget and encountering related watsonx resource limitations before completing all intended final launch work. To finish the project deliverables, the team continued **local implementation and UX/UI work with Claude**, producing a finished Streamlit operations dashboard and recorded MVP demonstration. This was a **development tool transition**, not a claim that Claude published the IBM-hosted agents or validated Live deployment.

The five-agent Orchestrate architecture, imports, and Draft Preview testing remain part of the IBM-phase evidence. The final production/Live agent launch and complete post-fix managed-cloud acceptance are **not independently established**. The exact credit usage and limits are team-reported rather than verified against IBM billing logs.

## Evidence and known limitations

- [Chronological watsonx validation and flow-trace analysis](validation-progress-2026-11-20.md) — includes the original C03 failure, C05 false-positive formal grade, corrected-flow trace inspection and C09/C10 cloud output-integrity findings.
- [Final engineering closeout](final-project-closeout-2026-11-21.md) — source inventory and Bob-reported final configuration/tests.
- [Current source architecture](../agents/orchestrator_agent.yaml) and [flow source](../tools/flow_pkg/civic_shield_pipeline.py).
- [Synthetic-case dataset](../data/samples/public-service-risk-v1.json).
- [Project demonstration video](https://youtu.be/-Cnd7L0FpTo) — user-supplied link; video playback, privacy settings, and its exact demonstration of watsonx deployment have not been independently verified here.

### Accurate portfolio statement

> Developed and imported a five-agent AI architecture in IBM watsonx Orchestrate for Civic Shield, integrating Python specialist tools and a deterministic security-analysis workflow. Investigated synthetic cases in Draft Preview, reviewed execution traces and safety controls, and used IBM Bob to support debugging, configuration and offline regression testing. The local Streamlit MVP and demonstration were completed; published Live deployment and end-to-end dashboard connectivity were not independently verified.

**Status:** Agent creation, import/configuration, and Draft Preview execution are documented. **Production/Live launch is not claimed without deployment evidence.**
