# Milestones and Progress

**Next IBM milestone deadline recorded by the team: October 23, 2026**  
**Repository review: October 26, 2026**

This checklist compares the files in the repository with the team's documented deliverables. The original IBM assignment guide and submission slides are not included, so full alignment with the official rubric and deadline has not been independently verified.

## Status meanings

- **Included — draft:** the document exists; approval, validation, or submission may still be needed.
- **Reported complete — evidence missing:** the team reports work is complete, but supporting code or results are not uploaded.
- **Partial:** some supporting material exists; specific gaps remain.
- **Missing:** the required artifact or evidence is absent from this repository; it may exist elsewhere.

## IBM SkillsBuild deliverables

| Deliverable | Included evidence | Status | Still needed |
|---|---|---|---|
| Problem statement and empathy map | [Project concept §3–4](project-concept.md) | Included — draft | Team review; validate empathy-map hypotheses with user or mentor feedback |
| AI Agent Architecture — slide 17 | [Week 4 §1](week-4-deliverables.md) | Included — draft | Review against implementation and update the actual submission slide |
| AI Agent Workflow — slide 18 | [Week 4 §2](week-4-deliverables.md) | Included — draft | Confirm approval conditions, retry limits, escalation triggers, and closure authority; update submission slide |
| Tools & Integrations — slide 19 | [Week 4 §3](week-4-deliverables.md) | Included — draft | Confirm actual tools and service access; distinguish optional services in submission slide |
| MVP scope — slide 22 | [Week 4 §4](week-4-deliverables.md), [concept §12](project-concept.md) | Included — draft | Demonstrate successful authorized sandbox handling and critical-case human escalation |
| GitHub repository | README, contributing guide, configuration template, ignore rules, documentation | Included | Upload implementation and evidence listed below |
| Initial working prototype | [Original prototype files](https://github.com/nyashachamp/Byte-into-the-future/tree/gazal-initial-code/src/gazal-project) are staged on `gazal-initial-code`; IBM Bob integration is not verified | Branch available — review pending | Review code without altering the baseline, confirm installation and integrations, document reproducible tests before merging |
| Compliant dataset | [12-case synthetic dataset and guide](../data/samples/README.md), baseline, assets/services, mock authorizations, and evaluator-only expected outcomes | Included — v1 development fixture; consistency check passed | Team review of scenario, baseline/scoring/policy; adapt to prototype input and verify assignment requirements |
| Project documentation | Concept, Week 4 design, README, contributing guide, test plan | Partial | Installation, confirmed integrations, final decisions, test results, and submission-ready slide deck |
| Three-minute YouTube video | No link included | Missing; previously recorded as not started | Record demonstration, verify duration/accessibility, and add YouTube link |

## Technical progress and evidence

| Item | Owner | Repository status | Evidence needed to mark complete |
|---|---|---|---|
| Initial agent definitions and local Python pipeline | Development workstream | Files staged on `gazal-initial-code`; implementation not finalized | Team review of agent behavior, integration expectations, and reproducible runs |
| Dashboard interface | Development workstream | Prototype source staged on `gazal-initial-code`; review pending | Team-reviewed demo and results |
| Agents connected to dashboard | Development workstream | Integration reported, not independently validated | End-to-end test evidence and any IBM integration proof |
| Initial system test without dataset | Development workstream | Reported complete — verification pending | Dated command, environment, output, and result |
| Original VS Code project staged in GitHub | Development workstream | Uploaded to `gazal-initial-code` only | Review the baseline, preserve it, and do not merge until ready |
| Installation instructions | Development workstream | Draft setup documentation present on the staging branch | Verify supported environments and commands on a clean install; refine on a new branch |
| IBM Bob use | Ghazal; Nyasha documents evidence | Missing | Description of actual use and suitable screenshots, logs, or demonstration references |
| Synthetic dataset | Shared | Included — 12 cases, schema documentation, provenance, and expected outcomes | Team review and prototype input adapter |
| Dataset-based testing | Shared | Fixture consistency validator passed; dashboard execution evidence missing | Run the prototype against cases; save actual outputs and comparisons in `data/results/` |
| Acceptance-criteria validation | Shared | Criteria drafted; results missing | Detection/false-positive metrics, priority rationale, escalation evidence, handoff completeness, and approval/verification checks |
| Submission slides | Nyasha / shared | Missing from repository | Completed deck or accessible link mapped to required guide sections |
| Video | Nyasha / shared | Missing | Three-minute YouTube link |

`data/samples/` now contains the v1 fixture and guide. The initial prototype is staged only on `gazal-initial-code`. No verified dataset-based dashboard outputs have been committed to `main`. A folder name or README does not establish that implementation, data, or testing is complete.

## Completion checklist

- [x] Establish repository and include project/design drafts.
- [x] Include contribution instructions, data rules, configuration template, and test plan.
- [x] Preserve the original prototype files in a separate GitHub branch (`gazal-initial-code`); review and merge remain pending.
- [ ] Development workstream: verify and refine installation and launch instructions on a new working branch.
- [ ] Confirm IBM Bob access and document its actual use.
- [ ] Confirm which watsonx services and IBM Cloud resources are available and adopted.
- [ ] Choose the public-service scenario, baseline, and prioritization rubric.
- [x] Upload documented synthetic data and evaluator-only expected outcomes (v1; consistency check passed).
- [ ] Review v1 scenario, baseline/scoring/policy and adapt it to the prototype.
- [ ] Define allowed actions, human-approval conditions, retry limits, escalation triggers, and human closure authority.
- [ ] Assign remaining security-rule, dataset, QA, slide, and video tasks.
- [ ] Run dataset-based tests and record results against acceptance criteria.
- [ ] Include example verified resolution and complete unresolved-case handoff.
- [ ] Review the actual IBM guide and finish the required submission slides.
- [ ] Add the three-minute YouTube video link.
- [ ] Confirm deadline, submission location, and that all linked artifacts are accessible.

## Documentation conventions

Use **Ghazal** consistently. The maintained design uses five modules: Orchestrator, Security Investigator, Risk & Dependency Analyst, Response Agent, and Verification & Handoff. Policy gates apply across them; the dashboard and case store are supporting components.

IBM watsonx Orchestrate is optional, watsonx.ai / Granite and IBM Cloud are candidates, and adoption/access remain to be confirmed. IBM Bob is required according to the team's documented brief; evidence of use remains outstanding.

The Markdown documents are maintained for current use. Word files in `original/` are historical source copies and may contain earlier names or designs. Update this checklist when new evidence is committed; do not mark reported work as verified solely from a progress statement.
