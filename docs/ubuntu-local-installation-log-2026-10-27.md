# Ubuntu Local Installation Log — October 27, 2026

**Project:** Byte into the Future — Public Service Risk Dashboard  
**Workstream:** Local VM installation and independent testing preparation  
**Tested and documented by:** Nyasha Champ (team lead; independent testing in personal Ubuntu VirtualBox VM)  
**GitHub branch containing application:** `source-code`  
**Status:** Dependencies successfully installed; dataset validation and application tests have **not yet** been executed in this VM.

## Purpose

Document the team's first local Ubuntu setup attempt, troubleshooting observations, and reproducible steps. The goal is to test the synthetic dashboard without spending IBM BOB credits. This is an **installation checkpoint**, not a claim that the application, agents, IBM integrations, or the complete 12-case workflow has passed acceptance testing.

## Environment observed

| Component | Observed status |
|---|---|
| Virtualization | Oracle VirtualBox, Ubuntu guest |
| Operating system | Ubuntu 24.04.3 LTS (shown in TTY console) |
| Python | 3.12.3 |
| Git | 2.43.0 |
| Python virtual environment | `.venv` created and activated (prompt displayed `(.venv)`) |
| Application source | ZIP of the repository's `source-code` branch downloaded and extracted in Ubuntu |
| Extracted project location | `~/Downloads/Byte-into-the-future-source-code/` |
| Dashboard requirements | `src/source-code/requirements.txt` |
| Synthetic dataset | `data/samples/public-service-risk-v1.json` |
| IBM credits | None used for the observed local setup |

These details document one VM, not a verified supported-OS matrix.

## Verified progress

- Ubuntu's package manager completed the installation of Git and Python support packages; `git --version` returned **2.43.0**.
- The existing Ubuntu VM experienced slow or unresponsive graphical login sessions. A text console (TTY3) remained accessible. The display manager reported `active`; a normal graphical login eventually succeeded. The cause of the sluggish GUI was **not established**.
- A Git HTTPS clone was attempted, but private-repository authentication blocked it; the working source was instead downloaded as a ZIP through the authenticated Ubuntu browser.
- The extracted project was opened in a terminal and both files were found by a successful `ls` command:
  - `src/source-code/requirements.txt`
  - `data/samples/public-service-risk-v1.json`
- A Python environment was created using `python3 -m venv .venv` and activated using `source .venv/bin/activate`.
- Initial pip installation timed out retrieving packages from `files.pythonhosted.org`. A subsequent attempt used a longer timeout and reused cached downloads.
- The dependency installation **completed successfully**; terminal output showed `Successfully installed` including **Streamlit 1.66.1**, **pytest 8.4.2**, and **PyYAML 6.0.3**.
- No dataset-validator output, pytest result, CLI pipeline output, or running Streamlit page has yet been recorded from this VM.

## Reproduction commands

The following commands reproduce the setup from the root of the **extracted** `source-code` branch ZIP in Ubuntu. They do not install or configure IBM-hosted services.

```bash
# From the extracted project root:
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --timeout 180 -r src/source-code/requirements.txt
```

If pip times out again, verify the network and retry; cached and already-installed packages are ordinarily reused. Do not commit `.venv/`, downloaded wheels, API keys, login passwords, or GitHub tokens.

## Outstanding verification — not yet complete

Execute these **one at a time**, recording command, result, and date:

```bash
# At the extracted repository root, after activating .venv:
python tests/validate_synthetic_dataset.py

# Enter the application directory:
cd src/source-code
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python -m src.main
python -m streamlit run src/dashboard.py
```

Expected *targets* (not observed test results yet):

1. Dataset consistency validator reports `PASS` for the 12-case fixture.
2. Application's pytest suite passes and the summary is preserved.
3. CLI pipeline processes the synthetic dataset and outputs case results.
4. Streamlit dashboard loads in the Ubuntu browser, displays its case selector, and shows evidence, severity/score, action, verification, and human handoff for selected cases.
5. Run all 12 cases against the evaluator-only expected file; record actual vs. expected results and any mismatches in `data/results/` or a test log.
6. Review authorization and unknown-service-mapping safeguards; passing the four current pytest functions alone is not full acceptance coverage.
7. Confirm IBM Bob/watsonx integration **separately**; YAML agent definitions and a deterministic local simulation do not prove IBM-hosted agent execution.

## Troubleshooting record

| Issue encountered | Action taken / observation | Current status |
|---|---|---|
| VirtualBox clipboard initially unavailable | Opened ChatGPT in the Ubuntu browser and copied commands within the VM | Workaround succeeded |
| Ubuntu desktop/lock screen slow or apparently frozen | Used text console, checked available memory and display-manager state; eventually logged in graphically | Desktop accessible at last observation; cause unconfirmed |
| Git not installed | Installed Git and Python supporting packages with apt | Resolved |
| Private repository clone asked for authentication | Downloaded the correct `source-code` branch as an authenticated ZIP | Resolved for this setup; not a configured Git clone |
| pip read timeout on PyPI | Retried with `--timeout 180`; cached files reused | Resolved; dependencies installed |
| Accidental duplicate pip command | Command returned an option error; corrected and reran | Resolved, no repository change |

## Next checkpoint

Capture screenshots or copied text of the dataset validator, application pytest summary, CLI execution, and dashboard launch. **Do not mark those steps as complete until run.** Keep personal credentials, terminal password prompts, tokens, and any private data out of the shared testing evidence.

*This entry records local setup work. It does not change the application source, claim end-to-end validation, or represent approval to merge code into `main`.*


## October 28, 2026 — Dataset inspection and JSON syntax checkpoint

**Evidence source:** Screenshots of terminal output from the Ubuntu 24.04 VirtualBox VM. These are observed results, not inferred application behavior.

- Restarted the Ubuntu VM, opened the extracted project directory at `~/Downloads/Byte-into-the-future-source-code/`, and successfully reactivated the existing `.venv` environment (terminal prompt showed `(.venv)`). No packages were reinstalled.
- `ls -la` confirmed the project folders `data/`, `docs/`, `src/`, `tests/`, and `.venv/`.
- `ls -lah data/` confirmed `README.md` and `samples/`.
- `ls -lah data/samples/` confirmed `public-service-risk-v1.json` (approximately 12 KB) and a sample `README.md`.
- Executed the read-only syntax check:

  ```bash
  python -m json.tool data/samples/public-service-risk-v1.json > /dev/null && echo "JSON validation PASSED"
  ```

  **Observed terminal result:** `JSON validation PASSED`.

**Interpretation:** The dataset file exists and is syntactically valid JSON. This check **does not** establish that it contains 12 cases, that required fields and values are correct, or that the application processes the dataset successfully.

**Next pending action (Step 1E):** Inspect JSON top-level structure, then confirm the case count and dataset-specific constraints. The repository's `python tests/validate_synthetic_dataset.py` validator and application tests have **not yet** been run in this VM. Streamlit and cybersecurity scenario testing also remain pending.

**Scope:** Documentation-only update; no application source, dataset, or dependencies changed.


### October 28, 2026 — JSON structure and case-count verification

**Evidence:** Ubuntu Terminal screenshots from local VirtualBox testing, with active `(.venv)` prompt.

- Loaded `data/samples/public-service-risk-v1.json` using Python's `json.load`.
- **Observed root type:** `dict`.
- **Observed top-level keys:** `dataset_id`, `schema_version`, `synthetic`, `created_date`, `simulation_clock`, `provenance`, `services`, `assets`, `baselines`, `exceptions`, `policy`, `cases`.
- Inspected `d['cases']`: **12 cases found**, collection type **list**; comparison with expected count printed **`12-case count: PASS`**.

**Limits:** Count and basic JSON structure are confirmed, but individual required fields, values, cross-references, and scenario expectations are not yet validated. The repository's dedicated dataset validator has not yet been executed in this VM.

**Next command (pending):** `python tests/validate_synthetic_dataset.py` from the extracted project root with `.venv` active. Record actual output before claiming validator PASS.


### October 28, 2026 — Dedicated synthetic dataset validator: PASS

**Command executed in active Ubuntu VM environment, from project root:**

```bash
python tests/validate_synthetic_dataset.py
```

**Observed terminal output (verbatim):**

```text
PASS: 12 fixture cases; references, strict input types, baseline labels, scores,
notification rules, and action authorization expectations are consistent.
Dashboard integration and end-to-end behavior have NOT been tested.
```

**Assessment:** Step 1 dataset validation completed successfully in the Ubuntu VM. This verifies the constraints checked by the existing validator, not independent functionality of the app, Streamlit UI, agent orchestration, or IBM Cloud integrations. Next step: run the application's pytest suite and record its actual results.


## Testing attribution clarification — October 28, 2026

**Tester:** Nyasha Champ only. The Ubuntu installation verification, dataset inspection, JSON syntax check, 12-case count, and synthetic dataset validator execution documented above were performed independently by Nyasha Champ. Ghazal was unavailable to participate in this testing session. This attribution concerns testing only and does not change authorship or credit for Ghazal's application and dashboard development.


### October 28, 2026 — Step 2A: Automated Python tests PASS

**Tester:** Nyasha Champ (independent local Ubuntu VM session; Ghazal not present).

**Working directory:** `~/Downloads/Byte-into-the-future-source-code/src/source-code/`

```bash
PYTHONPATH=. python -m pytest -q
```

**Observed terminal output:** `4 passed in 0.06s` (100% test run completion).

**Assessment:** All four discovered tests in the existing application pytest suite passed in the local VM. An initial malformed pasted `cd` command produced `cd: command not found`, but the directory change was corrected before pytest ran. No production code or dataset edits were made. These passing unit tests do not establish Streamlit UI functionality, scenario-by-scenario outcomes, IBM Cloud integration, or end-to-end acceptance.

**Next pending check:** Application CLI execution followed by Streamlit dashboard launch and scenario assessment, one verified step at a time.


### October 28, 2026 — Step 2B: Local CLI pipeline execution

**Tester:** Nyasha Champ, independently in Ubuntu 24.04 VirtualBox VM.

**Command:** `PYTHONPATH=. python -m src.main` from `src/source-code/` with `.venv` active.

**Observed:** Terminal displayed a structured JSON output, then returned to the shell prompt without a visible traceback. The visible end of the JSON includes `handoff_required: true`, `lifecycle_status: "awaiting_human_approval"`, empty `events`, human intervention to approve/reject correction and review evidence before closure, and completed AI work describing a loaded isolated synthetic case, non-coercing validation, approved-baseline comparison, and mapping to a simulated public service.

**Assessment:** The CLI pipeline executed and produced output with a human-approval guardrail for the displayed case. Screenshot captures the final output portion only; it does not verify all 12 scenario outputs, a zero exit status explicitly, dashboard UI behavior, or live IBM integration. Streamlit launch and scenario-by-scenario tests remain pending.


### October 28, 2026 — Step 3B: Streamlit web server startup verified

**Tester:** Nyasha Champ, independent Ubuntu VirtualBox VM session.

**Command previously issued:** `python -m streamlit run src/dashboard.py` from `src/source-code/`.

After the first-time Streamlit email prompt was left blank, the terminal displayed `2026-10-28 02:17:32.274 Uvicorn server started on :::8501`, `You can now view your Streamlit app in your browser`, and `Local URL: http://localhost:8501` (plus network URL `http://10.0.0.201:8501`). No startup traceback was visible in the supplied screenshot.

**Scope:** Confirms a listening local server; Firefox page rendering, dashboard controls, scenario results, and integration remain unverified. **Next:** open `http://localhost:8501` in the Ubuntu browser and inspect the interface. No source files changed.


### October 28, 2026 — Step 3C: Streamlit interface rendered in Firefox

**Tester:** Nyasha Champ, independent Ubuntu 24.04 VirtualBox VM session.

**Observed URL:** `http://localhost:8501` in Firefox within the VM. Screenshot shows the **Public Service Risk Dashboard** rendered, with synthetic test mode, in-memory actions and human-closure notice, a case selector and assessment/priority/severity/verification metrics.

**Initially displayed case C01:** “Compliant private storage”; assessment **Compliant**, priority score **0**, severity **NONE**, verification **Not Run**. Asset **AST-PERMIT** (object_storage); affected service **Fictional county permit portal**; finding **No baseline deviation**; action **none**. Sections for evidence/baseline and action/human intervention are visible.

**Assessment:** Initial UI rendering and first-case display verified. Interactive selection, verification, workflow safeguards and other 11 cases have not yet been tested. No source code changed.


### October 28, 2026 — Step 4A: C01 preliminary workflow inspection (in progress)

**Tester:** Nyasha Champ, Ubuntu VirtualBox Firefox at `http://localhost:8501`.

**Screenshot observations, lower part of case C01:** Baseline requirements shown: `public_read=False`, `encryption_enabled=True`, `audit_logging_enabled=True`. Workflow shows `tool result: not_run`, `workflow outcome: no_action`, `handoff required: No`, a human review of evidence and approval of final case closure, and an empty ordered execution events table. Collapsible completed AI work and full-result JSON controls are visible.

**Status:** Preliminary UI inspection only. Actual observed configuration values have not yet been compared with the baseline in this session; C01 acceptance remains **pending**. No verification/action controls were invoked and no code was changed.


### October 28, 2026 — C01 expanded JSON examination (provisional)

**Tester:** Nyasha Champ; evidence: three Firefox screenshots of expanded full-result JSON.

**Visible values:** case_id `C01`; title `Compliant private storage`; asset_id `AST-PERMIT`; asset_name `object_storage`; service `Fictional county permit portal`; assessment `compliant`; finding `No baseline deviation`; severity `none`; score `0`; confidence `1`; `finding_rule_ids=[]`; `evidence=[]`. Baseline evidence requires public_read false, encryption_enabled true, audit_logging_enabled true. Downstream output: action_attempts 0, action_result `not_run`, verification_result `not_run`, outcome `no_action`, escalation_required false, handoff_required false, human evidence review and approval before final closure, events empty, lifecycle_status `awaiting_human_review`.

**Assessment:** No action on the compliant case and pending human closure review are consistent with expected safeguards. **C01 not yet marked PASS:** the JSON screenshots do not show the fixture's actual observed control values; compare those to the baseline before completing acceptance. No code changes or live remediation performed.


## Screenshot evidence manifest

A numbered index of 20 testing screenshots has been created at [`docs/testing-evidence/README.md`](../testing-evidence/README.md). The original PNG files are prepared in a separately downloadable ZIP but **are not yet uploaded to GitHub**. The image evidence links are pending upload. This distinction is intentional: the narrative outcomes above are documented, but image preservation within the repository remains incomplete.


### October 28, 2026 — C01 baseline cross-check: PASS (local synthetic assessment)

**Tester:** Nyasha Champ. **Evidence:** Ubuntu terminal screenshot of read-only Python extraction of the original C01 fixture.

**Dataset C01:** `AST-PERMIT`, `BASE-STORAGE-V1`; original `snapshot` values: `public_read=false`, `encryption_enabled=true`, `audit_logging_enabled=true`. These each match the baseline requirements displayed in the Streamlit UI. `exception_ids=[]`, `authorization.sandbox_only=true`, `authorization.allowed_actions=[]`, and simulated `tool_behavior=not_called`.

**Result:** **PASS — C01 local baseline classification and no-action workflow**. Dashboard displayed compliant/score 0/severity none, outcome no_action, zero action attempts, with human review required prior to closure. Expected non-remediation behavior aligns with fixture controls. **Limit:** No human final closure, production exposure assessment, or IBM Cloud agent execution tested. Subsequent cases remain untested.


### October 28, 2026 — C02 exception review (pending)

**Tester:** Nyasha Champ. Screenshot of original fixture C02 (`Approved public information`, `AST-PUBLIC`, `BASE-STORAGE-V1`): observed snapshot `public_read=true`, `encryption_enabled=true`, `audit_logging_enabled=true`; `exception_ids=["EX-PUBLIC"]`; `sandbox_only=true`, `allowed_actions=[]`, simulated tool behavior `not_called`. Case observation timestamp `2026-10-20T12:00:00Z`. Dashboard previously displayed no baseline deviation and `no_action` despite default baseline `public_read=false`.

**Assessment:** Public-read deviation is potentially covered by exception EX-PUBLIC, but the exception's approval, scope and valid time window are not yet checked. **C02 status: pending**, not PASS. Next: inspect exception definition and compare against the synthetic observation timestamp. No code modified.


### October 28, 2026 — C02 approved public-information exception: PASS (local synthetic logic)

**Tester:** Nyasha Champ. Screenshot shows exception `EX-PUBLIC` from original JSON: `asset_id=AST-PUBLIC`, `rule_id=CFG-PUBLIC`, `approved_value=true`, `expires_at=2026-12-31T23:59:59Z`, reason `Fictional approved publication of non-sensitive public information`. C02 observed on `2026-10-20T12:00:00Z`, before expiration. Observed `public_read=true`, encryption and logging true; dashboard presented `No baseline deviation`, `no_action`, 0 attempts, and human closure review.

**Result:** PASS for C02 **synthetic exception matching and no-remediation decision**. The dataset provides an exception record but not an identifiable human approver or auditable approval history; production governance review remains necessary. Does not constitute live system security validation. No application code modified.


### October 28, 2026 — C03 authorized logging remediation: PASS (local synthetic workflow)

**Tester:** Nyasha Champ. Evidence: Firefox screenshots of C03 dashboard and ordered events, plus Ubuntu Terminal screenshot of original fixture.

- **Fixture:** `C03`, `AST-PERMIT`, `BASE-STORAGE-V1`; snapshot `public_read=false`, `encryption_enabled=true`, `audit_logging_enabled=false`; no exceptions.
- **Authorization:** `sandbox_only=true`; `allowed_actions=["enable_audit_logging"]`; expires `2026-10-21T00:00:00Z`, after simulated observation `2026-10-20T12:00:00Z`.
- **Simulated behavior:** `tool_behavior=success`, maximum 2 attempts.
- **Dashboard:** confirmed misconfiguration `CFG-LOGGING`, severity MEDIUM, score 30; action `enable_audit_logging`, attempts 1, tool result success, verification passed, outcome `verified_awaiting_human_closure`.
- **Event sequence:** action_attempt → tool_result (success) → independent verification (passed). Human review and approval of final closure still required.

**Result: PASS** for the locally simulated authorized-remediation and verification path, not proof of production infrastructure changes or live IBM service integration. No source modifications.


### October 28, 2026 — C04 critical-service logging scenario (preliminary, pending authorization)

**Tester:** Nyasha Champ. Firefox screenshots of C04 dashboard and execution events.

C04 `Same logging failure on critical service`, asset `AST-EMERGENCY`, fictional emergency coordination portal: finding `audit_logging_enabled` expected true/observed false; assessment Confirmed, priority 60, severity HIGH, verification Passed. The simulated action `enable_audit_logging` had 1 attempt, reported tool success, and workflow outcome `verified_awaiting_human_closure`; final human closure review required. Ordered events: (1) immediate human notification required before action; (2) action attempt; (3) tool success; (4) independent verification passed. Compared with C03 (same finding, priority 30, MEDIUM), C04 received higher priority for critical-service impact.

**Limitations:** Notification event reports requirement, not evidence of actual human receipt or acknowledgment. Original fixture's `allowed_actions`, timing and simulation settings have not yet been cross-checked. **C04 status: pending final PASS.**


### October 28, 2026 — C04 fixture authorization cross-check: PASS (local synthetic scenario)

**Tester:** Nyasha Champ. Original C04 fixture screenshot: `AST-EMERGENCY`, baseline `BASE-STORAGE-V1`, observed at `2026-10-20T12:00:00Z`; public_read=false, encryption_enabled=true, audit_logging_enabled=false; exception_ids=[]; sandbox_only=true; allowed_actions=["enable_audit_logging"]; authorization expires `2026-10-21T00:00:00Z`; tool_behavior=success, max_attempts=2.

**Result:** PASS for local synthetic authorized action, priority/notification sequencing and simulated verification, combined with previously observed dashboard events (notification required before action, one attempt, success, independent verification passed, final human closure pending). Does not prove real-world notification delivery, live infrastructure remediation, or external IBM integration. No source changes.


### October 28, 2026 — C05 restricted storage exposure (preliminary, pending authorization)

**Tester:** Nyasha Champ. Three screenshots show C05 `Restricted storage exposed`, asset `AST-AID`, fictional county assistance portal. Dashboard assessment Confirmed, score 100, severity CRITICAL, verification Not Run. Finding `CFG-PUBLIC`: `public_read` expected false, observed true. Action `none`, attempts 0, tool result `not_run`, workflow `handoff`, handoff required Yes. Human intervention: incident response review of public exposure; no automatic correction permitted; final closure review. Ordered events contain `notification` with detail `Immediate human notification required before action`. AI work shows initial loading, validation, baseline comparison and service mapping only.

**Preliminary assessment:** Appropriate critical alert and non-remediation/handoff reported. The fixture's authorization, exceptions and policy constraints have not yet been checked; do not mark C05 PASS yet. Actual delivery of notification is not established. No source changed.


### October 28, 2026 — C05 critical exposure authorization cross-check: PASS (synthetic)

**Tester:** Nyasha Champ. Original C05 fixture screenshot: `AST-AID`, `BASE-STORAGE-V1`, observed `2026-10-20T12:00:00Z`; `public_read=true`, encryption=true, audit_logging=true, no exceptions, sandbox_only=true, `allowed_actions=[]`, authorization expiry `2026-10-21T00:00:00Z`, simulated `tool_behavior=not_called`.

**Result:** PASS for local synthetic policy restriction and handoff: dashboard identified CRITICAL score 100, attempted zero actions, tool not run, workflow `handoff`, incident response human review required and notification-required event shown. No evidence of actual human notification delivery or production remediation; these remain outside test scope.


### October 29, 2026 — C06 correction not authorized: PASS (local synthetic authorization gate)

**Tester:** Nyasha Champ. Screenshots of Streamlit C06 workflow and original C06 JSON fixture in Ubuntu VM.

- C06 `Correction not authorized`, asset `AST-PERMIT`, baseline `BASE-STORAGE-V1`, observed `2026-10-20T12:00:00Z`.
- Snapshot: `public_read=false`, `encryption_enabled=true`, `audit_logging_enabled=false`; `exception_ids=[]`.
- Authorization: `sandbox_only=true`, `allowed_actions=[]`, expires `2026-10-21T00:00:00Z` (after observation).
- Simulation: `tool_behavior=not_called`, maximum attempts 2.
- Dashboard evidence: `CFG-LOGGING` expected true/observed false; action `none`, attempts 0, tool result `not_run`, workflow `awaiting_approval`, handoff required yes, approval/rejection requested before correction and human closure review required.

**Result: PASS** for local synthetic no-unauthorized-action gate and human approval handoff. Actual approval execution and production enforcement remain untested. No application code modified.


### October 29, 2026 — C07 false-success remediation verification: PASS (local synthetic scenario)

**Tester:** Nyasha Champ. Evidence: Firefox ordered-events and handoff screenshot, plus Ubuntu terminal showing original C07 JSON fixture.

- `C07`, `Action returns success but state unchanged`, asset `AST-PERMIT`, baseline `BASE-STORAGE-V1`, observed `2026-10-20T12:00:00Z`.
- Snapshot: `public_read=false`, `encryption_enabled=true`, `audit_logging_enabled=false`; no exceptions.
- Sandbox authorization explicitly permits `enable_audit_logging`; expires `2026-10-21T00:00:00Z` (after simulated observation).
- Fixture simulation: `tool_behavior=success_without_change`, maximum attempts 2.
- Dashboard event sequence: one `enable_audit_logging` action attempt, reported tool success, then independent verification **failed**. Outcome `handoff`; human investigation of unchanged state required and no automatic retry recommended.

**Result: PASS** — expected detection of false-positive tool success and safe escalation in the synthetic workflow. The failed verification is an intentionally expected scenario outcome, not a failed acceptance test. No live infrastructure or human notification delivery validated. No source code modified.


### October 29, 2026 — C08 transient failure then recovery: PASS (local synthetic scenario)

**Tester:** Nyasha Champ. Evidence: Streamlit C08 summary and execution-event screenshots, plus original JSON fixture screenshot in Ubuntu VM.

- C08 `Transient failure then recovery`, asset `AST-PERMIT`, baseline `BASE-STORAGE-V1`, observed `2026-10-20T12:00:00Z`.
- Snapshot: `public_read=false`, `encryption_enabled=true`, `audit_logging_enabled=false`; no exceptions.
- Authorization: `sandbox_only=true`, `allowed_actions=["enable_audit_logging"]`, expires `2026-10-21T00:00:00Z`, after observation.
- Simulation: `tool_behavior=transient_then_success`, `max_attempts=2`.
- Dashboard: finding CFG-LOGGING, priority 30, MEDIUM, two attempts; first temporary tool failure, second reported success, then independent verification passed. Outcome `verified_awaiting_human_closure`, with final human closure review still required.

**Result: PASS** for the synthetic bounded-retry-and-recovery path; exactly two attempts match the fixture's maximum. Not a test of live infrastructure or external agent integration. No code modified.


### October 29, 2026 — C09 missing required logging field: PASS (local synthetic validation)

**Tester:** Nyasha Champ. Evidence: Streamlit C09 summary and events screenshots, plus terminal output of original C09 JSON fixture.

- C09 `Missing required logging field`, asset `AST-PERMIT`, baseline `BASE-STORAGE-V1`, observation `2026-10-20T12:00:00Z`.
- Original snapshot has `public_read=false` and `encryption_enabled=true` but **omits** `audit_logging_enabled`.
- Authorization: `sandbox_only=true`, `allowed_actions=[]`, expires `2026-10-21T00:00:00Z`. Simulated `tool_behavior=not_called`.
- Dashboard displayed `Invalid Input`, unknown priority and severity, `missing required field: audit_logging_enabled`, no action attempts, tool not run, workflow `request_data`, and no execution events. It requested a corrected snapshot with strict Boolean fields.

**Result: PASS** for synthetic missing-field validation and safe refusal to infer a value or remediate on incomplete input. This does not test live data ingestion. No application source modified.


### October 29, 2026 — C10 wrong type for public access: PASS (local synthetic validation)

**Tester:** Nyasha Champ. Evidence: Streamlit C10 screenshots and Ubuntu terminal screenshot of original fixture.

- C10 `Wrong type for public access`, `AST-PERMIT`, `BASE-STORAGE-V1`, observed `2026-10-20T12:00:00Z`.
- Original snapshot: `public_read="false"` (string, **not** JSON Boolean false); `encryption_enabled=true`, `audit_logging_enabled=true`; exceptions empty.
- Authorization: `sandbox_only=true`, `allowed_actions=[]`, expires `2026-10-21T00:00:00Z`; simulated tool behavior `not_called`.
- Dashboard: `Invalid Input`, priority Unknown, severity UNKNOWN, verification Not Run; evidence `field must be a JSON boolean: public_read`; no corrective action or execution attempts; outcome `request_data`; requested a corrected snapshot with strict Boolean fields. Ordered execution events empty.

**Result: PASS** for local synthetic strict-type rejection and safe request for corrected data instead of coercion, scoring, or remediation. This does not validate live data ingestion or production controls. No source code modified.


### October 29, 2026 — C11 missing service dependency: PASS with display observation

**Tester:** Nyasha Champ. Ubuntu fixture screenshot plus earlier Streamlit UI screenshots; repository cross-check against the asset inventory and evaluator-only expected fixture.

- C11 `Missing service dependency`, asset `AST-UNKNOWN`: observed `public_read=false`, `encryption_enabled=true`, `audit_logging_enabled=false`, no exceptions, sandbox-only, `allowed_actions=[]`, `tool_behavior=not_called`.
- Verified `AST-UNKNOWN` has `service_ids=[]` in source dataset. Expected-results fixture prescribes `assessment=confirmed`, `finding_rule_ids=[CFG-LOGGING]`, `priority_score=null`, no action, zero attempts, `verification=not_run`, `outcome=handoff`, `handoff_required=true`.
- Dashboard reports confirmed logging finding, Unknown priority, no attempted correction, and human handoff: **matches expected functional behavior**.

**Result: PASS** for local dependency-missing and handoff behavior. **Display observation for review:** Streamlit renders severity as `NONE` despite a confirmed finding with unknown/null priority. This is semantically ambiguous; recommend evaluating `UNKNOWN`/`UNDETERMINED` label for null risk score. Not yet classified as functional test failure; score and response follow expected fixture. No source modifications.


### October 29, 2026 — C12 unencrypted storage: PASS (local synthetic authorization gate)

**Tester:** Nyasha Champ. Evidence: Firefox dashboard screenshots and Ubuntu terminal screenshot of original C12 fixture.

- C12 `Unencrypted storage`, asset `AST-PERMIT`, baseline `BASE-STORAGE-V1`, observed `2026-10-20T12:00:00Z`.
- Snapshot: `public_read=false`, `encryption_enabled=false`, `audit_logging_enabled=true`; no exceptions.
- Authorization: `sandbox_only=true`, `allowed_actions=[]`, expires `2026-10-21T00:00:00Z`; simulation `tool_behavior=not_called`.
- Dashboard: Confirmed misconfiguration `CFG-ENCRYPTION` expected true/observed false; score 50, severity MEDIUM, verification Not Run; zero action attempts; workflow `awaiting_approval`, human handoff required, and approval before any correction and case closure.

**Result: PASS** for local synthetic encryption finding, correct priority and no-unauthorized-action/human-approval workflow. No live storage encryption modified or production approval tested. No source changes.

## Twelve-scenario local testing checkpoint — October 29, 2026

**Independently tested by Nyasha Champ:** C01–C12 each passed its observed synthetic acceptance checks, including fixture comparison and dashboard workflow review. This is a local proof-of-concept checkpoint, **not** end-to-end IBM-hosted agent validation or production-readiness approval. C11 UI displays severity `NONE` with an unknown priority due to an unmapped service dependency; preserve as a usability/semantic review item. Further work: consolidated scenario results report, updated screenshot uploads for C06–C12, production security readiness assessment, VM stability review and IBM integration validation.
