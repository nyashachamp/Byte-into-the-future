# 🐝 Civic Shield — Public Service Risk Dashboard

**[Meet Byte into the Future! — Team & Mission](TEAM.md)**

**Team Byte into the Future** · **IBM SkillsBuild AI Experiential Learning Lab** · **Track #4: Government & Public Services**

A synthetic cybersecurity proof of concept that helps analysts identify security configuration deviations, understand dependencies on public services, prioritize cases, simulate **policy-authorized** response steps, verify outcomes, and prepare auditable human handoffs.

> **Safety principle:** AI-assisted analysis and simulated actions do **not** replace human approval for critical actions or final case closure. No real government infrastructure or citizen records are used.

**Project closeout checkpoint:** 21 November 2026 · **Submission target:** 22 November 2026  
**Integrated implementation:** The final application, five-agent source, and testing records are now on **`main`**, merged from [the recovery branch](https://github.com/nyashachamp/Byte-into-the-future/tree/recovery-five-agent-2026-11-19) in [PR #6](https://github.com/nyashachamp/Byte-into-the-future/pull/6).  
**Local demo:** The team lead reports the final Streamlit MVP and presentation video are complete. [Read the final closeout](docs/final-project-closeout-2026-11-21.md) for what is versioned, what was demonstrated locally, and which cloud/runtime claims remain unverified.  
**Branch note:** `main` now contains the final five-agent implementation and Claude Agent Run interface (original source commit `f613bdb`). The recovery branch remains preserved for historical comparison.

## Start here

| Want to understand… | Follow this link |
|---|---|
| **Final build/demo closeout and GitHub audit (Nov 21)** | **[Final project closeout](docs/final-project-closeout-2026-11-21.md)** |
| Earlier implementation and validation checkpoint (Nov 20) | [Prior system status](docs/current-system-status-2026-11-20.md) |
| Architecture, implementation and evidence navigation | [Documentation guide](docs/README.md) |
| Five-agent testing, including a failed formal evaluation | [Validation progress](docs/validation-progress-2026-11-20.md) |
| Earlier local synthetic test results and 54 screenshots | [Functional test report](docs/cybersecurity-functional-test-report-2026-10-29.md) · [Screenshot index](docs/testing-evidence/README.md) |
| Submission readiness | [Milestones](docs/milestones.md) · [Final checklist](docs/submission-checklist-2026-11-22.md) |
| Outstanding engineering audit and remediation | [GitHub Issue #5](https://github.com/nyashachamp/Byte-into-the-future/issues/5) |

## The public-service problem

Government cybersecurity and IT teams contend with alert overload, configuration drift, incomplete service-dependency context, and fragmented incident handoffs. A misconfiguration's technical severity alone may not convey whether it affects a benefits portal, identity service, or other essential public function.

**Design challenge:** How might agentic AI help government teams validate configuration findings, prioritize them by public-service impact, and perform only permitted response work while preserving human oversight?

**Primary users:** SOC analysts, IT operations staff, incident responders, and security managers.  
**Example environment:** A fictional county-government environment represented with a 12-case synthetic dataset.

## What the prototype does

1. Loads a synthetic alert/configuration snapshot and checks the input types.
2. Compares observed settings against approved baselines and exceptions.
3. Evaluates asset-to-public-service dependencies and priority.
4. Applies policy/authorization gates before any simulated action.
5. Independently checks the simulated post-action state and records events.
6. Leaves critical, uncertain, unauthorized, or unresolved cases for human review and handoff.

**Representative cases:** C03 tests permitted synthetic audit-logging correction; C05 tests critical public-read exposure and escalation without an automatic fix; C07 tests a false success report; C11 tests missing service-dependency information.

## Implementation architecture

```text
       Synthetic case / analyst request
                     |
         Orchestrator (watsonx)
                     |
      +--------------+--------------+
      |              |              |
 Security        Risk &           Response       Verification
 Investigator    Dependency       Agent          & Handoff
                 Analyst                         Agent
      |              |              |              |
  investigate      analyse       execute         verify
     case          impact        response       and handoff
       \______________|______________|____________/
                     |
        Synthetic Python tools / data
```

The recovery branch contains native YAML definitions for **one supervisor and four specialists**, each specialist with a dedicated Python tool package. The finalized source routes the supervisor through the deterministic `civic_shield_pipeline` tool (with `collaborators: []` to close the direct-delegation bypass); Bob reported the import and subsequent verification of the installed configuration.

**Evidence boundary:** imported/configured agents and verified GitHub source are **not** independent proof of a fresh post-fix 12/12 cloud run, published Live version, or verified dashboard-to-Orchestrate connectivity. See the [Nov 21 closeout](docs/final-project-closeout-2026-11-21.md).

The preserved `src/source-code/` Python pipeline and Streamlit dashboard provide a **separate deterministic implementation** of the risk-analysis lifecycle. Earlier reported dashboard hosting used Streamlit Community Cloud; the live application URL and availability are not independently verified in this checkpoint. There is no verified Code Engine deployment.

## Test and verification snapshot

The table below is the **historical 20 November checkpoint**, retained to preserve earlier failures and how they were found. Later deterministic-flow fixes and reported validation are documented in the [21 November closeout](docs/final-project-closeout-2026-11-21.md). The team reports a successful final local Streamlit demonstration; do not confuse that with new accepted cloud traces.

| Area | Evidence as of 2026-11-20 |
|---|---|
| Local synthetic Python/Streamlit workflow | 12/12 case behaviors documented in Oct 29 local report; not native-agent formal passes |
| Automated pipeline, fixture and regression tests | Test files and prior results documented; rerun on final integrated version still required |
| Five-agent import / collaborator configuration | Observed in IBM Bob and watsonx builder |
| C03 Draft Preview | Generated a coherent **simulated** case report and human-closure state |
| **First C03 formal evaluation** | **FAILED** at 09:16 Pacific (0/1; tool-call precision/recall 0.88; routing F1 1.00) |
| Saved C03 test adjustment | `investigator_result` matcher changed **Exact → Fuzzy**; this changed test criteria, **not** runtime behavior |
| **C03 formal rerun (09:44 Pacific)** | **PASSED 1/1 under the revised Fuzzy matcher**, 8 tool calls, precision/recall/routing/journey 1.00; this does **not** prove exact JSON matching or a runtime code fix |
| **C05 formal grade (11:09 Pacific)** | **1/1 / 100% reported by evaluation, but workflow acceptance FAILED.** Exported trace showed investigator and analyst calls only; no response or verification specialist calls. The narrative's remediation/verification/completion assertions were unsupported |
| C05 later remediation testing | Evening testing conversation reported continuing C05 work and a `WORKFLOW INCOMPLETE` response; this is a **provisional update**, not an accepted pass or a verified new trace |
| C07 / C11 / remaining native-agent cases | Pending independent formal validation |
| Published Live agent and dashboard integration | Not independently verified |

The original C03 failure, qualified later pass, and **C05 false-positive formal grade** are preserved and explained in the [validation log](docs/validation-progress-2026-11-20.md). Do not conflate a local 12-case pass with acceptance of the newer five-agent Orchestrate workflow.

## Repository map

```text
agents/                 Native agent configurations, including the preserved original agent
tools/                  Specialist watsonx tool packages and original risk-analysis tool
src/source-code/        Python pipeline, CLI, Streamlit dashboard, and local tests
data/samples/           12 synthetic public-service-risk scenarios
tests/                  Dataset fixtures, unit/integration helpers and validation scripts
scripts/                Import and maintenance PowerShell utilities
docs/                   Status, audit, plans, reports and historical evidence
CONTRIBUTING.md         Team contribution and security guidelines
.env.example            Non-secret configuration template
```

Some tool packages intentionally contain synchronized copies of pipeline code and fixtures for import packaging. The original `src/source-code/agents/` describes logical workflow roles; the root `agents/` holds native watsonx definitions. These are **different artifacts**, not interchangeable evidence of deployment.

## Running the deterministic prototype locally

The following is a **local Python/Streamlit path**, not a watsonx Orchestrate deployment procedure. Use an isolated virtual environment and Python 3.10+; install requirements from the repository root:

```bash
python -m venv .venv
# Activate .venv using your OS-specific command.
python -m pip install -r src/source-code/requirements.txt
python -m pip install pytest
python tests/validate_synthetic_dataset.py
cd src/source-code
python -m pytest -q
python -m src.main
python -m streamlit run src/dashboard.py
```

Commands are supplied for reproducibility and should be rerun on the final accepted branch before being treated as a fresh validation. For the original local test sequence, see the [Ubuntu installation log](docs/ubuntu-local-installation-log-2026-10-27.md).

The native watsonx agent tools require separately configured IBM access, deployment, and validation. **Do not run the maintenance/deletion scripts without reviewing their effects and confirming the target environment.**

## Demo and deliverables

- **Dashboard:** Final local Streamlit MVP demonstration reported completed by the team lead; no IBM Code Engine deployment is claimed.
- **Agent demonstration / walkthrough video:** [Civic Shield video demonstration on YouTube](https://youtu.be/-Cnd7L0FpTo) (URL supplied by the team lead on November 21, 2026). The video page's playback, duration and privacy setting were not independently verified in this audit. This is the **demonstration video**, not the hosted Streamlit application URL.
- **Final pitch deck:** Team lead reports presentation completed; public/submission-accessible link is not yet recorded in this repository.
- **Submission:** Confirm only after the official IBM portal receipt is available.

See the [submission checklist](docs/submission-checklist-2026-11-22.md). Missing links are displayed as pending rather than fabricated.

## Security, limitations and team contribution

- Synthetic/public-authorized data only; no live public-service infrastructure, citizen data, or actual incident remediation.
- No credentials, tokens, private contact details, or unredacted evidence in public GitHub.
- Human approval/closure remains separate from simulated automated steps.
- This is a collaborative team project. Use commit/PR history and verified evidence to attribute individual contributions rather than implying that one person built every component.
- This is a **proof of concept**, not a production security product or validated autonomous incident-response service.

For original design rationale and older records, see the [documentation guide](docs/README.md).