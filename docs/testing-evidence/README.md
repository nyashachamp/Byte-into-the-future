> **Evidence scope (updated 2026-11-20):** These 54 images document **earlier local Ubuntu/Python/Streamlit testing**, not the later native five-agent watsonx Orchestrate formal evaluation or a published Live deployment. These original screenshots are present in the recovery branch as well. See [current status](../current-system-status-2026-11-20.md) and [Orchestrate validation progress](../validation-progress-2026-11-20.md) for later evidence and the original C03 failure. Historical material below is retained for traceability.

# Ubuntu VM testing screenshot evidence — October 27–28, 2026

**Tester:** Nyasha Champ (independent testing).  
**Status:** All **54 PNG screenshots** (01–54) are present on the `source-code` and `recovery-five-agent-2026-11-19` branches. Installation and C01–C05 are documented by 01–35; C06–C12 by 36–54.  
**Source:** Terminal and Firefox screenshots supplied during testing. No application code or dataset modified.

| # | Evidence file |
|---|---|
| 1 | `01-vm-restart-venv-activated.png` |
| 2 | `02-project-directory-verified.png` |
| 3 | `03-data-directory-inspected.png` |
| 4 | `04-synthetic-json-file-located.png` |
| 5 | `05-json-syntax-pass.png` |
| 6 | `06-json-top-level-structure.png` |
| 7 | `07-twelve-case-count-pass.png` |
| 8 | `08-synthetic-dataset-validator-pass.png` |
| 9 | `09-pytest-four-passed.png` |
| 10 | `10-cli-pipeline-human-approval.png` |
| 11 | `11-streamlit-first-launch.png` |
| 12 | `12-streamlit-server-started.png` |
| 13 | `13-dashboard-first-render-c01.png` |
| 14 | `14-next-session-venv-reactivated.png` |
| 15 | `15-streamlit-restart.png` |
| 16 | `16-c01-baseline-and-handoff.png` |
| 17 | `17-c01-summary-and-baseline.png` |
| 18 | `18-c01-json-assessment-evidence.png` |
| 19 | `19-c01-json-human-intervention.png` |
| 20 | `20-c01-json-lifecycle.png` |

## Verified outcomes and limitations

- JSON parsed successfully; 12-case fixture count PASS; dedicated dataset validator PASS.
- Automated pytest suite: **4 passed in 0.06s**.
- CLI produced JSON, Streamlit started on port 8501, and C01 dashboard UI rendered.
- C01 was classified compliant, score 0, severity none, no action; final human review still required.
- C01–C12 passed their local synthetic scenario checks as documented in the [consolidated test report](../cybersecurity-functional-test-report-2026-10-29.md). Screenshots here cover installation and C01–C12. The GitHub evidence-files check confirms filenames and presence; the independently reviewed screenshots support the local synthetic test results. No claim of end-to-end IBM-hosted agent integration.

**Evidence handling:** Preserve existing filenames 01–54 without duplicates or renumbering. The new screenshots were committed in GitHub on October 30, 2026 (commit `e81c0b2`).

## Additional screenshots — C01 through C05

| # | Evidence file |
|---|---|
| 21 | `21-c01-original-fixture.png` |
| 22 | `22-c02-dashboard.png` |
| 23 | `23-c02-original-fixture.png` |
| 24 | `24-c02-approved-exception.png` |
| 25 | `25-c03-dashboard-summary.png` |
| 26 | `26-c03-execution-events.png` |
| 27 | `27-c03-human-intervention.png` |
| 28 | `28-c03-authorization-fixture.png` |
| 29 | `29-c04-dashboard.png` |
| 30 | `30-c04-execution-events.png` |
| 31 | `31-c04-authorization-fixture.png` |
| 32 | `32-c05-dashboard.png` |
| 33 | `33-c05-handoff-and-baseline.png` |
| 34 | `34-c05-execution-events.png` |
| 35 | `35-c05-authorization-fixture.png` |

**Transfer status:** All 54 numbered PNG screenshots are uploaded and verified present in GitHub. See the [consolidated testing report](../cybersecurity-functional-test-report-2026-10-29.md) and chronological log for scenario assessments. New fixes to F-01 and F-02 are present in the `source-code` branch (Oct. 30), but their independent post-change retest remains pending.


## Additional screenshots — C06 through C12

| # | Evidence file |
|---|---|
| 36 | [`36-c06-dashboard-approval-required.png`](./36-c06-dashboard-approval-required.png) |
| 37 | [`37-c06-authorization-fixture.png`](./37-c06-authorization-fixture.png) |
| 38 | [`38-c07-failed-verification-events.png`](./38-c07-failed-verification-events.png) |
| 39 | [`39-c07-false-success-fixture.png`](./39-c07-false-success-fixture.png) |
| 40 | [`40-c08-dashboard-retry-summary.png`](./40-c08-dashboard-retry-summary.png) |
| 41 | [`41-c08-retry-execution-events.png`](./41-c08-retry-execution-events.png) |
| 42 | [`42-c08-transient-failure-fixture.png`](./42-c08-transient-failure-fixture.png) |
| 43 | [`43-c09-dashboard-invalid-input.png`](./43-c09-dashboard-invalid-input.png) |
| 44 | [`44-c09-empty-execution-events.png`](./44-c09-empty-execution-events.png) |
| 45 | [`45-c09-missing-field-fixture.png`](./45-c09-missing-field-fixture.png) |
| 46 | [`46-c10-dashboard-wrong-boolean-type.png`](./46-c10-dashboard-wrong-boolean-type.png) |
| 47 | [`47-c10-empty-execution-events.png`](./47-c10-empty-execution-events.png) |
| 48 | [`48-c10-string-false-fixture.png`](./48-c10-string-false-fixture.png) |
| 49 | [`49-c11-dashboard-unknown-dependency.png`](./49-c11-dashboard-unknown-dependency.png) |
| 50 | [`50-c11-empty-events-human-handoff.png`](./50-c11-empty-events-human-handoff.png) |
| 51 | [`51-c11-missing-dependency-fixture.png`](./51-c11-missing-dependency-fixture.png) |
| 52 | [`52-c12-dashboard-unencrypted-storage.png`](./52-c12-dashboard-unencrypted-storage.png) |
| 53 | [`53-c12-awaiting-approval-no-events.png`](./53-c12-awaiting-approval-no-events.png) |
| 54 | [`54-c12-unauthorized-encryption-fixture.png`](./54-c12-unauthorized-encryption-fixture.png) |
