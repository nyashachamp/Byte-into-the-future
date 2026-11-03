# Cybersecurity Functional Testing and Findings Review

**Project:** Byte into the Future — Public Service Risk Dashboard  
**Program:** IBM SkillsBuild AI Experiential Learning Lab  
**Tester:** Nyasha Champ, team lead (independent Ubuntu/VirtualBox testing)  
**Testing period:** October 27–29, 2026  
**Report compiled:** October 29, 2026  
**Environment:** Ubuntu 24.04 VirtualBox VM; Python 3.12.3; virtualenv; Streamlit local interface at localhost:8501  
**Scope:** Local synthetic proof of concept; no real government systems, citizen records, production infrastructure, or verified IBM-hosted agent execution

## Executive summary

**12/12 synthetic scenarios matched their locally expected workflow outcomes**, based on observed dashboard screenshots, case-by-case source fixture inspection, and the repository's expected-results specification. The dedicated synthetic dataset validator reported PASS and the existing pytest run reported **4 passed in 0.06s**. The CLI generated a structured result and the local Streamlit UI opened. These tests show a functional local proof of concept, not production readiness or live watsonx Orchestrate integration.

Two code-review observations remain open: (F-01) the runtime exception logic does not compare an exception's `approved_value` to the actual observed configuration (unlike the dedicated dataset validator), and (F-02) unknown-risk C11 displays severity `NONE` instead of `UNKNOWN`. F-01 merits negative testing before a definitive exploitability rating is assigned; neither has been claimed as a regression in the 12 supplied fixtures.

## Test objectives and method

1. Validate dataset JSON syntax, count (12), references, required Boolean types, scores, labels, and authorization expectations.
2. Run existing Python tests from `src/source-code` using `PYTHONPATH=. python -m pytest -q`.
3. Execute the local pipeline using `PYTHONPATH=. python -m src.main` and start Streamlit with `python -m streamlit run src/dashboard.py`.
4. Inspect each dashboard case and compare assessment, score, finding, action, attempts, verification, and handoff with the case's original fixture.
5. Review the application implementation and expected-results fixture for limitations and discrepancies.

**Result terminology:** PASS below means the supplied synthetic scenario behaved as expected; it does **not** mean every independent security control was tested, an actual action was taken in government infrastructure, or the application is ready for production.

## Consolidated case matrix

| Case | Test focus | Expected risk / action / outcome | Observed local result | Verdict |
|---|---|---|---|---|
| C01 | Compliant private storage | Score 0; none; no_action; human closure review | Baseline matches; no action; human review pending | PASS |
| C02 | Approved public information | Score 0; exact EX-PUBLIC exception; no_action | Matching asset/rule/value and unexpired synthetic exception; no action | PASS |
| C03 | Correct audit logging | MEDIUM, score 30; 1 permitted action; verification passed | enable_audit_logging, 1 attempt, verified_awaiting_human_closure | PASS |
| C04 | Logging on critical service | HIGH, score 60; notification event before action; 1 attempt | Notification-required event, action success and verification passed | PASS |
| C05 | Restricted public storage | CRITICAL, score 100; no automatic action; handoff | Public-read deviation; attempts 0; incident-response handoff | PASS |
| C06 | Unauthorized correction | MEDIUM, score 30; no action; awaiting_approval | Empty allowed_actions; attempts 0; awaiting_approval | PASS |
| C07 | False tool success | MEDIUM, score 30; 1 attempt; verification failed; handoff | Tool success without state change; verification failed; no automatic retry | PASS |
| C08 | Transient failure and retry | MEDIUM, score 30; 2 attempts; verification passed | First temporary failure, then success, independently verified | PASS |
| C09 | Missing logging field | Invalid input; unknown score; request_data; no action | Required field absent; correct request_data response | PASS |
| C10 | Wrong Boolean type | Invalid input; unknown score; request_data; no action | String `"false"` rejected instead of Boolean coercion | PASS |
| C11 | Missing service dependency | Confirmed finding; null score; no action; handoff | Unknown service impact; safe handoff; UI severity NONE (observation) | PASS with finding F-02 |
| C12 | Unencrypted storage | MEDIUM, score 50; no action; awaiting_approval | Encryption disabled; actions unauthorized; human approval requested | PASS |

For C04 and C05, a `notification` event shows the application's requirement to notify, **not evidence that a human actually received a notification**. For C03/C04/C08, `verification passed` refers to the in-memory simulated post-action state, **not** a real infrastructure readback.

## Findings and recommended follow-up

### F-01 — Exception-approved-value mismatch in runtime logic

**Category:** Authorization / exception validation  
**Status:** Code-review finding, negative test pending  
**Suggested priority:** High for review before production-like deployment; final severity requires confirmation

In `src/source-code/src/pipeline.py`, the `active_exceptions` collection checks exception ID, asset ID, and expiration but does not verify `approved_value` against `case["snapshot"][rule["field"]]`. The separate `tests/validate_synthetic_dataset.py` **does** compare the approved value with the snapshot. Therefore the runtime and independent validator have inconsistent exception logic.

**Risk:** A manipulated or inconsistent exception record could suppress a finding that its permitted value does not cover. The supplied C02 fixture is valid and passes; this is a potential edge-case weakness, not an observed C02 failure.

**Next action:** Add a controlled synthetic negative test that changes the exception's `approved_value` or the observed value while keeping rule and asset matching; confirm that the runtime does not waive an unmatched deviation. If reproduced, require an exact rule, asset, approved value, and valid period match in the runtime logic; add a regression test. Coordinate application changes with Ghazal.

### F-02 — Unknown service impact displayed as NONE severity

**Category:** Risk communication / usability  
**Status:** Confirmed from screenshot and source  
**Suggested priority:** Medium

For C11, `AST-UNKNOWN` has `service_ids=[]`, the priority score is `null`, and the expected outcome is `handoff`. The runtime helper `_severity` treats `score is None` as `none` except when the assessment is `invalid_input`. The dashboard therefore shows **NONE**, although the impact is **unknown** and the misconfiguration is confirmed.

**Next action:** Render unknown / undetermined severity for missing score, while preserving NONE for zero score and compliant cases. Add an automated assertion for C11's displayed severity; review with the team.

### F-03 — VirtualBox stability interruption

**Category:** Test environment reliability  
**Status:** Open; root cause unknown

The Ubuntu VM became unresponsive, required shutdown/restart, and once reached the GRUB boot menu before the desktop resumed. Existing project files and environment remained usable afterward.

**Next action:** Check `df -h /`, `free -h`, swap utilization, and prior-boot logs before further resource-heavy work. Do not attribute the freeze to a specific cause without evidence.

### F-04 — Evidence documentation coverage

**Category:** Traceability / documentation  
**Status:** Partial

35 original PNG screenshots for installation and cases C01–C05 were verified in `docs/testing-evidence/`. Screenshots for C06–C12 have been reviewed in the testing conversation but have **not** been verified as uploaded to the repository. The evidence index includes stale `awaiting upload` wording that should be corrected.

**Next action:** Upload C06–C12 screenshot evidence, add direct image links in a refreshed manifest, and check naming and duplicates.

## Test coverage and limitations

- Local tests cover known synthetic inputs and expected workflow behavior. The existing pytest suite comprises **four tests**, with a broad all-case outcome test plus focused C03, C05, and C07 tests. This is **not** 12 independent unit tests.
- The independent fixture validator validates the data and expected labels but explicitly **does not validate dashboard integration or end-to-end behavior**.
- Human approvals, delivered notifications, external APIs, secrets management, RBAC, adversarial input, operational logging, and IBM Cloud / watsonx Orchestrate integration remain unverified.
- The local implementation is a **deterministic Python pipeline with an in-memory action simulator**; the proposed five-agent architecture in the README is not by itself evidence of five independently executing cloud agents.
- No live, production, or government system was touched.

## Acceptance and next gates

**Local synthetic functional test gate:** PASS (12/12 supplied cases).  
**Code-review gate:** OPEN (F-01 and F-02).  
**Production security gate:** NOT TESTED.  
**IBM Cloud multi-agent integration gate:** NOT VERIFIED.  
**VM reliability gate:** OPEN.  
**Final IBM project acceptance:** NOT CLAIMED.

**Recommended order:** (1) capture remaining screenshot evidence and reconcile index, (2) run negative test for F-01 and fix validated issues with developer coordination, (3) stabilize VM, (4) assess security readiness and agent integrations, (5) perform final acceptance and presentation preparation.

## Evidence and source references

- [Local installation and chronological test log](ubuntu-local-installation-log-2026-10-27.md)
- [Evidence images and manifest](testing-evidence/README.md)
- [Original 12-case dataset](../data/samples/public-service-risk-v1.json)
- [Expected scenario results](../tests/fixtures/public-service-risk-v1.expected.json)
- [Dedicated dataset validator](../tests/validate_synthetic_dataset.py)
- [Local pipeline implementation](../src/source-code/src/pipeline.py)
- [Streamlit dashboard](../src/source-code/src/dashboard.py)
- [Unit tests](../src/source-code/tests/test_pipeline.py)

*Prepared from verified session screenshots and repository source review. No source code was modified while preparing this report.*

---

## QA addendum — November 3, 2026: Post-correction independent testing status

**Observation:** Ghazal's corrections addressing F-01 (exception approved-value validation) and F-02 (unknown/null priority severity) were pushed to the `source-code` development branch on October 30, 2026, before Nyasha's independent post-correction regression testing was completed. The technical development report was subsequently merged into this branch through [pull request #4](https://github.com/nyashachamp/Byte-into-the-future/pull/4) on November 2, 2026.

**Developer-reported results:** The [technical development report](technical-development-report%20(1).md) states that the synthetic dataset validator passed and that eight automated pytest tests passed. These are developer-reported local results, not independently reproduced post-correction QA results.

**Independent QA status as of November 3, 2026:** **PENDING — not signed off.** The original October 27–29 local synthetic results (12/12 scenarios and four pytest tests) are pre-correction baseline evidence only. They must not be relabeled as post-correction validation. At the time of this addendum, independent Ubuntu regression execution of the corrected version has not been documented.

**Next action:** Preserve the earlier Ubuntu installation and evidence, establish the exact corrected commit under test in a separate directory, rerun the dataset validator and revised automated suite, check F-01 negative and valid-exception behaviors, verify F-02 C11 UNKNOWN versus C01 NONE, and rerun C01–C12 as needed. Record observed PASS/FAIL outputs and new screenshots beginning at 55. Do not change Ghazal's application code during QA.

**Process note:** Committing code before independent testing is an ordinary development workflow; this observation records the verification boundary, not an allegation of improper conduct. A push, merge, or developer test report does not constitute independent QA approval or IBM Cloud deployment acceptance.

---

## QA update — November 3, 2026: Independent post-correction Ubuntu execution

**Tester:** Nyasha Champ, independent local QA. **Environment:** Ubuntu 24.04 in VirtualBox; Python 3.12.3; pytest 8.4.2; corrected `source-code` archive extracted separately from the October 27 baseline. The existing baseline virtual environment was reused. The precise Git commit SHA inside the downloaded ZIP has not been established locally; this is a source-archive test, not a cryptographically verified commit checkout.

### Observed post-correction checks

- **Dataset consistency validator — PASS.** `python3 tests/validate_synthetic_dataset.py` returned `PASS: 12 fixture cases` with consistent references, strict input types, baselines, scores, notification rules, and authorization expectations. The validator itself expressly excludes dashboard integration and end-to-end behavior.
- **Updated automated pytest suite — PASS (8/8).** From `src/source-code`, using the baseline venv's Python and `PYTHONPATH=.`, independent output was `8 passed in 0.09s`.
- **F-01 focused controls — PASS for tested pipeline conditions.** Source review showed the observed configuration is compared with `approved_value` before an exception becomes active; the automated tests passed for a deliberately mismatched C02 exception (confirmed CFG-PUBLIC finding; no action attempt) and the valid C02 exception (compliant; no finding; score 0). C02 dashboard and JSON showed compliant/none/0/no action. The dashboard's JSON does not expose the exception record itself.
- **F-02 focused controls — PASS for tested pipeline and dashboard conditions.** The C11 automated check covered null priority, unknown severity, no action/attempts, and required human handoff. The C01 check covered score 0 and severity none. Streamlit screenshots showed C11 severity UNKNOWN/priority Unknown with no action and required handoff, and C01 severity NONE/score 0 with no action.
- **C03 dashboard check — PASS.** Streamlit displayed confirmed, score 30, MEDIUM, authorized simulated `enable_audit_logging`, one attempt, verification Passed, and `verified_awaiting_human_closure`.

### Batch pipeline result — PASS (12/12 for displayed assessment/severity/outcome)

The independent CLI batch used `PYTHONPATH=. <baseline-venv-python> -m src.main` from the corrected `src/source-code` directory. The full JSON was saved locally as `~/Downloads/QA-C01-C12-2026-11-03.json` using `tee`. A screenshot of the printed summary was reviewed. Its 12 case IDs, assessments, and outcomes were compared with `tests/fixtures/public-service-risk-v1.expected.json`; severities were consistent with the expected test behaviors and corrected unknown classification.

| Case | Assessment | Severity | Outcome | Selected-field verdict |
|---|---|---|---|---|
| C01 | compliant | none | no_action | PASS |
| C02 | compliant | none | no_action | PASS |
| C03 | confirmed | medium | verified_awaiting_human_closure | PASS |
| C04 | confirmed | high | verified_awaiting_human_closure | PASS |
| C05 | confirmed | critical | handoff | PASS |
| C06 | confirmed | medium | awaiting_approval | PASS |
| C07 | confirmed | medium | handoff | PASS |
| C08 | confirmed | medium | verified_awaiting_human_closure | PASS |
| C09 | invalid_input | unknown | request_data | PASS |
| C10 | invalid_input | unknown | request_data | PASS |
| C11 | confirmed | unknown | handoff | PASS |
| C12 | confirmed | medium | awaiting_approval | PASS |

**Scope and limitations:** This result verifies the 12 local synthetic pipeline summaries, not every field in every case, every Streamlit screen, independent hosted agents, notifications actually delivered to people, production controls, or IBM Cloud/watsonx execution. The automated tests contain some additional action and verification assertions for specific cases. Only C01, C02, C03, and C11 were visually rechecked in the post-correction dashboard session. The screenshots were provided during QA but have **not been uploaded or verified in GitHub's evidence directory**; the next free evidence filename remains 55. The prior 01–54 baseline screenshots are retained unchanged.

**Updated gate assessment (as of the observed November 3 session):** Local synthetic dataset, eight automated tests, focused F-01/F-02 checks, and 12-case CLI assessment/severity/outcome checks: **PASS within stated scope**. Full dashboard revalidation, screenshot archiving, reproducible commit identity, IBM Cloud deployment/integration and production-security acceptance: **PENDING / NOT TESTED**. No final IBM acceptance or independent approval of deployment is implied.
