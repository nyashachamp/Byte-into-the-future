# IBM SkillsBuild — submission readiness checklist

**Team:** Byte into the Future  
**Project:** Public Service Risk Dashboard / Civic Shield  
**Target deadline:** 22 November 2026  
**Checkpoint:** 20 November 2026 — statuses below reflect currently documented evidence, not assumptions about future work.

## Project and source

- [x] Repository exists and is public.
- [x] A 12-case synthetic dataset and evaluator fixture are available.
- [x] Earlier local Python/Streamlit functional testing and 54 screenshots are documented.
- [x] Recovery branch contains a configured five-agent topology and specialist tools.
- [ ] Identify a final authoritative submission branch or reviewed integration; do not assume default `main` contains current code.
- [ ] Verify a clean reproduction of the intended submission version and include exact launch instructions.
- [ ] Inspect published files/screenshots for accidentally exposed credentials or personal data and complete any required key rotation.

## Native watsonx Orchestrate validation

- [x] Team-lead import/configuration observations documented.
- [x] C03 first formal **FAILED** evaluation preserved with metrics.
- [x] Exact-to-Fuzzy matcher adjustment recorded as a test-only change.
- [ ] Verify a distinct post-adjustment C03 formal evaluation and document its actual result.
- [ ] Independently record native multi-agent C05, C07, C11 behavior.
- [ ] Complete remaining synthetic cases or explicitly record incomplete coverage.
- [ ] Verify Orchestrate Live publishing/version and test it if available.
- [ ] Identify and document implementation limitations without implying unverified dashboard-to-Orchestrate integration.

## Demo, presentation and submission

- [ ] Verify the final dashboard URL and availability, if presenting a hosted demo.
- [ ] Provide the demo video link and confirm required format/duration against official guidance.
- [ ] Provide the final pitch-deck link and confirm permissions.
- [ ] Cross-check official IBM lab requirements and distinguish required from optional technologies.
- [ ] Confirm the submitted repository URL points readers to the authoritative code and evidence.
- [ ] Record date/time and confirmation of final IBM submission.

## Completion principle

A checked box indicates documentation or evidence actually seen, not inferred completion. Historical local test results do not satisfy native agent formal-evaluation criteria. Preserve failed runs and the exact limitations of the synthetic proof of concept.

See the [current system status](current-system-status-2026-11-20.md), [validation progress](validation-progress-2026-11-20.md), and [GitHub audit Issue #5](https://github.com/nyashachamp/Byte-into-the-future/issues/5).
