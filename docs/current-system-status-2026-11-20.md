# Current system status — 20 November 2026

**Project:** Byte into the Future — Public Service Risk Dashboard / Civic Shield  
**Scope:** Synthetic government/public-service cybersecurity case analysis  
**Checkpoint:** Information verified from GitHub and team-lead watsonx Orchestrate screenshots recorded by 2026-11-20. Results later than this checkpoint require a new dated entry.  
**Working branch:** `recovery-five-agent-2026-11-19`  
**Submission deadline:** 2026-11-22

## What exists in the recovery branch

- `src/source-code/src/`: Python risk-analysis pipeline and local Streamlit dashboard.
- `data/samples/public-service-risk-v1.json`: 12 synthetic scenarios with documented expected outcomes in `tests/fixtures/`.
- `src/source-code/tests/` and `tests/`: automated tests and validation utilities.
- `agents/`: orchestrator and four specialist native watsonx Orchestrate agent YAML configurations; original `risk_analysis_agent` preserved.
- `tools/`: Python tool packages for the specialist agents and original single-agent tool.
- `scripts/`: import and delete/maintenance scripts; deletion scripts require particular care and explicit authorization.
- `docs/testing-evidence/`: 54 screenshots from **earlier local** Ubuntu/Streamlit validation, not new Orchestrate Live screenshots.

## Evidence classification

| Capability / milestone | Evidence as of checkpoint | Classification |
|---|---|---|
| 12-case deterministic Python/Streamlit workflow | Oct 27–29 local evaluation report records 12/12 synthetic case behavior checks | **Observed in local prototype**, not five-agent evaluation |
| F-01 and F-02 code fixes | Earlier technical development report describes code updates and regression testing | **Reported/documented code changes**; do not equate with a later Live evaluation |
| Single-agent watsonx Orchestrate tooling | Earlier technical report and audit note single agent plus one coded tool | **Earlier implementation**; preserved alongside recovery |
| Five native agent imports | IBM Bob terminal import success observed by team lead | **Observed import** |
| Four specialists attached to orchestrator | Orchestrate Build > Agents view showed four collaborators, each with one tool | **Observed configuration**; not proof of Live end-to-end pass |
| C03 Draft Preview | Synthetic report showed permitted audit-logging action, verification PASSED, human closure outstanding | **Generated preview**, not formal evaluation |
| C03 first formal evaluation | 2026-11-20 09:16 Pacific: **FAILED 0/1**, 8 calls, tool precision/recall 0.88, routing F1 1.00, journey 0.88 | **Verified failure — preserve** |
| C03 Exact -> Fuzzy matcher | Saved test's `investigator_result` comparison changed | **Test-criteria change** only; no runtime fix established |
| C03 formal rerun | No distinct later evaluation result verified at this checkpoint | **Pending confirmation** |
| C05 / C07 / C11 and other cases in native five-agent flow | No independently verified formal outcomes at checkpoint | **Pending** |
| Orchestrate Live publication | No verified publication/version/live test | **Unverified** |
| Dashboard direct calls to Orchestrate | Prior technical audit describes independent dashboard pipeline; no verified direct connector | **Not established** |
| Streamlit Community Cloud hosting | Developer-reported in earlier technical audit; running application URL not independently verified here | **Reported, not independently verified in this checkpoint** |
| IBM Cloud Code Engine hosting | Prior technical audit says unavailable/not completed | **Do not claim deployed** |

## Architecture and safety boundary

The *new native-agent topology* is an `orchestrator_agent` with four collaborators: `security_investigator`, `risk_analyst`, `response_agent`, `verification_handoff_agent`. The older Python pipeline models the same risk-analysis lifecycle deterministically. **Configured agent relationships are not the same as validated delegation or published Live behavior.**

The project uses synthetic records only. Permitted simulated actions must pass policy checks; high-risk or uncertain cases require human escalation or approval. Do not describe demonstrations as real government remediation, production hardening, or autonomous final incident closure.

## Known engineering/documentation caveats

1. C03 formal evaluation failed on an `investigator_result` tool-argument comparison. Fuzzy matching changes acceptance criteria; precise runtime cause is not confirmed.
2. GitHub source contains `tools/analyst_pkg/analyse_impact.py` (British spelling). Some earlier notes also wrote `analyze_impact.py`; confirm deployed tool metadata before attributing an error to spelling.
3. Several specialist packages carry synchronized copies of pipeline/data; changing the canonical implementation requires deliberate synchronization and regression testing, not a documentation-only edit.
4. `main` is an older baseline. Review and test before integrating any recovery code.
5. Final demo, pitch-deck link, submission confirmation, and complete formal multi-agent regression have not been verified in this checkpoint.

## Next validation and submission steps

1. Confirm whether a newer C03 evaluation exists after 09:16; record actual timestamp, status, metrics, tool traces.
2. Run and document C05, C07 and C11 against the native agent workflow, then the other eight scenarios.
3. Confirm published agent version/status and whether a Live test is possible.
4. Verify demo and pitch links and accurately describe how Streamlit and Orchestrate relate.
5. Review recovery branch changes and decide the authoritative submission branch without overwriting local work.

See [validation-progress-2026-11-20.md](validation-progress-2026-11-20.md), [Milestones](milestones.md), and [GitHub Issue #5](https://github.com/nyashachamp/Byte-into-the-future/issues/5) for the traceable record.
