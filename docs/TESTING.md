# Testing and verification

## Current deployed release (2026-10-18)

The deployed source SHA-256 is `CEC00C69E57E6AE1B70C77BE49CFFEEB912F2D55D15E42AF75A2B6687ABB6F5C`. It includes transaction-time deadlines, extended numeric-IP SSRF rejection, deadline enforcement for subsequent evidence in the `SUBMITTED` phase, and clearing the stored warranty holdback amount on waiver. Deployment finalized successfully and the source was matched against `genlayer code`; lifecycle writes against this release have not yet been run.

Focused retest of #12, #17, #19, #21, and #33: **14 passed**. Full Direct Mode suite: **97 passed**. GenVM `check` and `validate`: passed (3 checks; **47 methods**, 20 views and 27 writes). The Windows console initially failed to encode the linter checkmark under CP1252; rerunning with `$env:PYTHONIOENCODING='utf-8'` passed. The deployment fee has not yet been reconciled into the cumulative fee-inclusive expenditure ledger.

## Current source

Contract source SHA-256: `CEC00C69E57E6AE1B70C77BE49CFFEEB912F2D55D15E42AF75A2B6687ABB6F5C`.
The byte-matched source is deployed at `0xDFb69c1890F72c7b791A938ed36C5103582E6F19` on Studio Network
(chain `61999`); deployment transaction `0x47a258b79297644bce2d54ba8eea678177b27856181577b685d9d3adfbfc35c3`.
The contract pins `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.
Environment: Python 3.12, `genlayer-test==0.29.2`, `genvm-linter==0.11.1rc2`, pytest 8.4.2.

## Gate B — Direct Mode

Command: `pytest -q tests/direct --tb=short`

Result on the current release source: **97 passed**. No tests were skipped. The reviewed regression cases
cover PARTIAL/INSUFFICIENT settlement in ordinary and milestone flows, evidence-bound warranty targeting and appeal
binding carry-forward, bilateral ambiguity acknowledgements, warranty/milestone exclusion in both configuration
orders, and milestone consumer views. The tests cover lifecycle authorization,
API and agent judgments, evidence integrity, appeals, warranty, milestones, settlement conservation, withdrawal, and
adversarial/boundary cases. They use Direct Mode and are not evidence of network consensus by themselves.

## Gate C — GenVM lint and schema

Commands: `genvm-lint check contracts/speclock.py` and `genvm-lint validate contracts/speclock.py`.

Result on the current deployed source: **passed** (3 lint checks; schema validation passed). Contract: `SpecLock`; methods:
**47** (20 views, 27 writes). The linter reports that a newer runner exists; this project retains its pinned runtime
hash.

On Windows, set `$env:PYTHONIOENCODING='utf-8'` before running the linter if the console's default code page cannot
print its checkmark output. The initial CP1252 console attempt raised `UnicodeEncodeError`; rerunning with UTF-8 passed.

## Gate D — Clean clone

Verified from a fresh clone of commit `528afb3` in `C:\Users\USERpc\AppData\Local\Temp\speclock-clean-528afb3`. `pytest -q tests/direct`: **97 passed**. `genvm-lint check contracts/speclock.py` and `genvm-lint validate contracts/speclock.py`: passed (3 checks; 47 methods) after setting `PYTHONIOENCODING=utf-8` for Windows console output.

## Gate E — Studionet

Current deployment: `0xDFb69c1890F72c7b791A938ed36C5103582E6F19`, chain `61999`, deployment transaction `0x47a258b79297644bce2d54ba8eea678177b27856181577b685d9d3adfbfc35c`, source SHA-256 `CEC00C69E57E6AE1B70C77BE49CFFEEB912F2D55D15E42AF75A2B6687ABB6F5C`. Deployment finalized with `MAJORITY_AGREE`, 5/5 `AGREE`, and leader `SUCCESS`; schema returned 47 methods and a read-only view succeeded. No lifecycle writes have run against this release. Older lifecycle evidence at `0x142A...` is retained in `docs/evidence/studionet-reviewer-fix-2026-10-18.md` and is explicitly historical.

This is representative, not exhaustive. #12 is present in the current deployment but its lifecycle behavior is unverified on-chain; #17 is local-only pending a second signer, while #19, #21, and #33 remain partial as detailed in `docs/FEATURE_MATRIX.md`. Appeal/procedural-review and non-milestone inconclusive recovery were not repeated against this release. Cumulative gross transfer volume is recorded as 0.017038 GEN before unitemized fees; the new deployment fee is not reconciled, so fee-inclusive accounting is incomplete.

## Integration tests

No separate integration-test suite is provided. Direct Mode uses the GenLayer test harness; Studionet transactions
are recorded as reproducible evidence rather than being exposed as a secret-bearing automated test. This report does
not claim all 38 capabilities are complete.
