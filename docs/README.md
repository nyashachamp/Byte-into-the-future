# Documentation guide — Byte into the Future

**Current project:** Public Service Risk Dashboard (Civic Shield)  
**IBM SkillsBuild AI Experiential Learning Lab — Government & Public Services**  
**Documentation checkpoint:** 2026-11-20 (Pacific)  
**Target submission:** 2026-11-22

This page helps an evaluator distinguish the original design, tested deterministic prototype, native watsonx Orchestrate configuration, and validation still in progress. **All activity is synthetic; this is not a production government deployment.**

## Read in this order

1. [Repository overview](../README.md) — problem, architecture, run instructions, scope, and links.
2. [Current system status](current-system-status-2026-11-20.md) — implemented/configured/observed/evaluated/not verified.
3. [Validation progress](validation-progress-2026-11-20.md) — original C03 failed evaluation, qualified 09:44 pass under Fuzzy criteria, and C05 trace-proven false-positive formal grade (workflow failed).
4. [Milestones and evidence checklist](milestones.md) — remaining submission tasks.
5. [Submission checklist](submission-checklist-2026-11-22.md) — final deliverable verification.

## Technical implementation and testing

| Resource | Purpose | Evidence scope |
|---|---|---|
| [Core Python implementation](../src/source-code/README.md) | Deterministic pipeline, CLI, Streamlit dashboard | Source available in recovery branch |
| [Native agent YAML](../agents/) | One orchestrator, four specialists, preserved original single agent | Import/configuration observed; Live not verified |
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
- Current documentation target: `recovery-five-agent-2026-11-19`. The default `main` is an older baseline and must not be mistaken for the final implementation.
- Do not merge the recovery branch or rewrite historical test failures until reviewed integration and acceptance.
- **Historical local validation, Draft Preview output, formal agent evaluation and Live publication are different evidence categories.**

## Security and disclosure

Only synthetic fixtures and redacted evidence belong in the public repository. Do not commit credentials, keys, contact details, or unredacted screenshots/chat exports. A previously shared API key requires rotation/revocation confirmation outside this repository.
