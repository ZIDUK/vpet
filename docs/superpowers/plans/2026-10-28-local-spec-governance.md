# Local Spec Governance Implementation Plan

Spec: [SPEC-DEV-PROCESS-001](../specs/2026-10-28-local-spec-governance-design.md).
REQ-DEV-SDD-001: registro/validador. REQ-DEV-SDD-002: plantilla y spec separada.
REQ-DEV-SDD-003: runner y huella. REQ-DEV-SDD-004: evidencia sin falsa clausura.

Goal: implement approved requirement traceability and local verification, with no GitHub Actions.
Design: specs describe contracts; plans describe implementation; a JSON registry
links requirement IDs to acceptance criteria, tests and delivery records. A standard-library
checker validates references; a local runner records actual results against a source fingerprint.

- [x] RED: tests reject duplicate IDs, missing sections/tests/criteria, escaping paths and false release claims.
- [x] Implement scripts/spec_check.py and docs/requirements.json; bootstrap process and retrospective Creator specs.
- [x] Add mandatory spec template and separate Creator design from its existing implementation plan.
- [x] RED/GREEN: scripts/verify_local.py records failed/not-run checks and dirty source identity without promoting requirements.
- [x] Add make spec-check, verify-local, verify-local-full and release-check; adapt browser tests to an explicit local URL.
- [x] Update AGENTS.md/development workflow and run structural, focused and browser validation.
- [x] Attempt whole-tree/full-profile validation and record its blocked result without claiming it passed.

## Evidence And Boundaries

Missing checker/runner modules reproduced RED. Later regressions reproduced an
unregistered requirement heading and malformed/incomplete verification reports;
both now fail closed. The checker validates AST references, not test semantics.
Pilot registry: 2 specs, 12 requirements, 2 local-unreleased deliveries.
make spec-check collected 34 registered pytest cases at the initial pilot stage.
make verify-local passed all six steps (Python, traceability, JS and two browser
scripts), against a recorded dirty-tree hash. First evidence:
out/local-verification/20261028T135208Z-128c2204/report.json.
make release-check correctly returns nonzero for pending approval/evidence/commit.
No automatic promotion, hooks, Git config, remote CI, flash or publication.

Skills consulted: writing-plans, test-driven-development, ai-debt-detector and
verification-before-completion. This log is not certification of every skill checklist.

Final focused checks: 53 passed. The full attempt at
out/local-verification/20261028T135324Z-f22e764c/ exhausted disk during pytest;
the original reporter also failed to write its final JSON. Its log remains;
no missing/partial report is treated as proof. Only that run's pytest-12 scratch
directory was removed, not backups or user data. No native/build/browser result
is claimed for that failed full attempt.

Regression added for low-disk refusal, explicit failed-report fallback and no
deploy commands in the full profile. Full preflight now requires 6 GiB free and
preserves all later gates as not-run on refusal. The correctly persisted blocked
attempt is out/local-verification/20261028T135950Z-7ec52bd7/report.json.
The final pilot is rerun separately after documentation settles; its printed
out/local-verification report binds exact source bytes and actual test results.

## Full Follow-Up After Disk Space Was Freed

2026-10-28: workspace had 31 GiB free. Attempt
out/local-verification/20261028T141241Z-1b1dbc3d/report.json passed every check,
but its source fingerprint changed while another delivery plan was updated.
It was not accepted as one stable source snapshot and was not manually overridden.

Repeated full run: out/local-verification/20261028T141943Z-e5a2c08a/report.json.
Result passed, source_unchanged=true. Python: 2084 passed in 297.97 s, 13278
existing deprecation/palette warnings. Native: 185 passed in 0.460 s. Generated
content, assets build, JS syntax, both Chromium flows and ESP32 compilation pass.
Incremental ESP32 build: 2.612 s, static RAM 53460 bytes, app 1116477 bytes.
The report binds that working-tree snapshot; this documentation is appended
after verification. Requirements remain implemented and specs await final review.
No hardware session, flash, publication, Git hooks/config or Actions were used.

No .github/workflows, external service, automatic flash, publication, hooks installation
or Git configuration. Release readiness is a separate check; human approval cannot
be authenticated by a local JSON field. Keep existing user changes untouched.
