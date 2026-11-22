# Civic Shield — Public Service Risk Dashboard

🐝 **[Meet Byte into the Future! — Our Team & Mission](TEAM.md)**

**IBM SkillsBuild AI Experiential Learning Lab · Government & Public Services**

**Civic Shield** is a completed **local synthetic-data MVP and recorded demonstration**, as reported by the team on **November 21, 2026**. The project explores how a security-operations dashboard and specialized AI-agent workflows can help analysts identify misconfigurations, assess their potential effects on public services, prioritize risk, and prepare evidence-backed human handoffs.

> **Important repository distinction:** The default `main` branch is an **earlier development baseline**. The more recent five-agent architecture, current Streamlit application, tests, and closeout records are on **[`recovery-five-agent-2026-11-19`](https://github.com/nyashachamp/Byte-into-the-future/tree/recovery-five-agent-2026-11-19)**. The code has **not been merged into `main`**. Do not treat this branch's historical implementation status as the final project status.

## Final implementation — start here

| Resource | Current reference |
|---|---|
| **Current code and architecture** | [Recovery branch](https://github.com/nyashachamp/Byte-into-the-future/tree/recovery-five-agent-2026-11-19) |
| **Engineering and project closeout, Nov. 21** | [Final closeout report](https://github.com/nyashachamp/Byte-into-the-future/blob/recovery-five-agent-2026-11-19/docs/final-project-closeout-2026-11-21.md) |
| **Current implementation README** | [Recovery branch README](https://github.com/nyashachamp/Byte-into-the-future/blob/recovery-five-agent-2026-11-19/README.md) |
| **Streamlit dashboard source** | [Dashboard](https://github.com/nyashachamp/Byte-into-the-future/blob/recovery-five-agent-2026-11-19/src/source-code/src/dashboard.py) |
| **Agent definitions** | [Five-agent system](https://github.com/nyashachamp/Byte-into-the-future/tree/recovery-five-agent-2026-11-19/agents) |
| **Orchestration workflow** | [Sequential flow](https://github.com/nyashachamp/Byte-into-the-future/blob/recovery-five-agent-2026-11-19/tools/flow_pkg/civic_shield_pipeline.py) |
| **Demonstration video** | [Civic Shield on YouTube](https://youtu.be/-Cnd7L0FpTo) |
| **Our team** | [Byte into the Future!](TEAM.md) |

## Implemented project scope

The preserved source includes **one supervisor/orchestrator and four specialist agents**: Security Investigator, Risk & Dependency Analyst, Response Agent, and Verification & Handoff. The system uses a deterministic sequential flow, synthetic Python tools and fixtures, policy/authorization gates, and a Streamlit dashboard with risk visualizations and case-inspection features.

The project uses **12 synthetic cases (C01–C12)** covering configuration findings, exceptions, authorized simulation, verification failure, unknown data, and human handoff. The local prototype and demonstration were reported complete; earlier local 12-case behavior and extensive offline testing are documented in the recovery branch.

## Verification boundaries

- **Local MVP:** Team-reported complete and demonstrated, with versioned source and substantial offline test evidence.
- **IBM watsonx Orchestrate:** Five-agent configurations and flow source are documented. This repository does **not independently establish fresh post-fix 12/12 managed-cloud acceptance, Live publication, or a connected dashboard-to-Orchestrate run**.
- **Cloud hosting:** No verified IBM Code Engine deployment is claimed.
- **Safety:** All scenarios use synthetic data. Actions are simulated and gated; final critical decisions and closure remain with humans.

See the [final closeout report](https://github.com/nyashachamp/Byte-into-the-future/blob/recovery-five-agent-2026-11-19/docs/final-project-closeout-2026-11-21.md) for precise evidence, test results, known limitations, and release notes.

---

**Project phase:** Local MVP and demonstration completed and submitted as reported by the team. The recovery branch is the maintained implementation reference; the default branch is retained as a historical baseline pending a reviewed merge.
