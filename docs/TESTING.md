# Testing and verification

## Current source

Contract source SHA-256: `AFCDF4D9841F5F170644586A564DB4740961280654E0545F6B6C2C65E8C8734D`.
The contract pins `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.
Environment: Python 3.12, `genlayer-test==0.29.2`, `genvm-linter==0.11.1rc2`, pytest 8.4.2.

## Gate B — Direct Mode

Command: `pytest -q tests/direct --tb=short`

Result on the pushed corrected source: **89 passed**. No tests were skipped. The tests cover lifecycle authorization,
API and agent judgments, evidence integrity, appeals, warranty, milestones, settlement conservation, withdrawal, and
adversarial/boundary cases. They use Direct Mode and are not evidence of network consensus by themselves.

## Gate C — GenVM lint and schema

Commands: `genvm-lint check contracts/speclock.py` and `genvm-lint validate contracts/speclock.py`.

Result: **passed** (3 lint checks; schema validation passed). Contract: `SpecLock`; methods: **45** (20 views, 25
writes). The linter reports that a newer runner exists; this project retains its pinned runtime hash.

On Windows, set `$env:PYTHONIOENCODING='utf-8'` before running the linter if the console's default code page cannot
print its checkmark output. The initial CP1252 console attempt raised `UnicodeEncodeError`; rerunning with UTF-8 passed.

## Gate D — Clean clone

Verified from GitHub clone `3a9c0b08530c69844438856c8663ca332d824fa8` in
`C:\Users\USERpc\AppData\Local\Temp\speclock-clean-3a9c0b0` using committed files only. Installed
`requirements-dev.txt`, ran both GenVM lint/schema commands, and ran `pytest -q tests/direct --tb=short`:
**89 passed**, lint and validation passed. No contract source or tests were changed after this check; a later
 documentation-only commit updates this record.

## Gate E — Studionet

Corrected deployment `0xCEE0430CcC760f1Dce94d2E416CbeCe2b1CB8c79`, chain ID `61999`, deployment transaction
`0xc4f1be49ed4f0af80e12e6abc4d2b16f5d3e9acc2bf26c8a4ed2c20146148312`, finalized with `MAJORITY_AGREE` and leader
`execution_result: SUCCESS`. Representative current-source API/agent PASS and FAIL, actual native funding and
withdrawal, warranty anti-redirection and claim resolution, milestone settlement, and inconclusive recovery with
recovery-aware replay were executed and read back. The detailed transaction ledger is
`docs/evidence/studionet-corrected-release-2026-10-18.md`.

This gate is **representative, not exhaustive**: four of 38 capabilities remain partial (#12, #19, #21, #33); two
incomplete milestone probes and one warranty probe left small test amounts unsettled/claimable, and test fees were not
itemized. See `SUBMISSION.md`, `docs/FEATURE_MATRIX.md`, `docs/DEPLOYMENT.md`, and `docs/SECURITY.md`.

## Integration tests

No separate integration-test suite is provided. Direct Mode uses the GenLayer test harness; Studionet transactions
are recorded as reproducible evidence rather than being exposed as a secret-bearing automated test. This report does
not claim all 38 capabilities are complete.
