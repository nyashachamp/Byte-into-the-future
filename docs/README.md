# Documentation guide — Byte into the Future

**Current project:** Public Service Risk Dashboard (Civic Shield)  
**IBM SkillsBuild AI Experiential Learning Lab — Government & Public Services**  
**Documentation closeout checkpoint:** 2026-11-21 (Pacific)  
**Target submission:** 2026-11-22

This page distinguishes the completed local Civic Shield MVP/demo, the five-agent Orchestrate source and reported deployment, the historical test evidence, and what GitHub cannot independently verify. **All activity is synthetic; this is not a production government deployment.** The team lead reports that the final local Streamlit app, video demonstration, and presentation were completed on November 21.

## Read in this order

1. **[Final project closeout (Nov 21)](final-project-closeout-2026-11-21.md)** — reported completed local demo, latest GitHub deployment/code audit, test summary, limitations and final sync gate.
2. [Repository overview](../README.md) — problem, architecture, run instructions, scope and project links.
3. [Earlier system status (Nov 20)](current-system-status-2026-11-20.md) — prior checkpoint retained as history, not a replacement for the final closeout.
4. [Validation progress](validation-progress-2026-11-20.md) — chronological tests, original failed evaluations and corrective testing reports.
5. [Claude UX/UI session handoff](ux-session-handoff-2026-11-21.md) — later local Agent Run UI changes, tests and source-synchronization distinction.
6. [Submission checklist](submission-checklist-2026-11-22.md) — remaining evidence and delivery references.

## Technical implementation and testing

| Resource | Purpose | Evidence scope |
|---|---|---|
| [Core Python implementation](../src/source-code/README.md) | Deterministic pipeline, CLI, Streamlit dashboard | Source available in recovery branch; final Claude Agent Run enhancement is reported on laptop but not yet synced to GitHub |
| [Native agent YAML](../agents/) | One orchestrator, four specialists, preserved original single agent | Flow-only supervisor source verified; Bob-reported import/re-export; current Live runtime not independently verified |
| [Specialist tool packages](../tools/) | Investigator, analyst, response, verifier; preserved original tool | Code present; separate formal end-to-end acceptance outstanding |
| [Test directory](../tests/README.md) | Automated tests and validation fixture | Does not itself prove live Orchestrate execution |
| [Local functional test report, Oct 29](cybersecurity-functional-test-report-2026-10-29.md) | 12 synthetic local-case observations, limitations, findings | Historical Ubuntu/Streamlit local scope |
| [Historical screenshot index](testing-evidence/README.md) | 54 archived local test screenshots | Not proof of five-native-agent Live deployment |
| [Technical development report](technical-development-report%20%281%29.md) | Earlier implementation and local test phase | **Historical snapshot**, not latest status |
| [Five-agent recovery plan](five-agent-recovery-plan.md) | Design rationale, phases, data contracts and safeguards | **Historical plan**; later code/configuration exists |
| [Ubuntu installation/testing log](ubuntu-local-installation-log-2026-10-27.md) | Local environment and reproducibility narrative | Historical local phase |

## Project design and history

- [Original problem and concept](project-concept.md)
- [Week 4 architecture/workflow deliverables](week-4-deliverables.md)
- [Consolidated security baselines and test catalog](baseline-test-catalog.md)
- [Dataset testing guide](ghazal-dataset-testing-guide.md)
- [Original Word source documents](original/) — retained as history; Markdown status pages are current.

## GitHub review and change management

- [Issue #5: deployment audit and remediation](https://github.com/nyashachamp/Byte-into-the-future/issues/5).
- Final documentation target: `recovery-five-agent-2026-11-19`. The default `main` is an older baseline. The final locally demonstrated dashboard enhancement still requires review and synchronization to the recovery branch.
- Do not merge the recovery branch or rewrite historical test failures until reviewed integration and acceptance.
- **Historical local validation, Draft Preview output, formal agent evaluation and Live publication are different evidence categories.**

## Security and disclosure

Only synthetic fixtures and redacted evidence belong in the public repository. Do not commit credentials, keys, contact details, or unredacted screenshots/chat exports. A previously shared API key requires rotation/revocation confirmation outside this repository.
