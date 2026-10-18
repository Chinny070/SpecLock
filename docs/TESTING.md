# Testing and verification

## Un-deployed review candidate (2026-10-18)

The working-tree candidate source SHA-256 is `CEC00C69E57E6AE1B70C77BE49CFFEEB912F2D55D15E42AF75A2B6687ABB6F5C`. It adds transaction-time deadlines, extended numeric-IP SSRF rejection, fixes deadline enforcement for subsequent evidence in the `SUBMITTED` phase, and clears the stored warranty holdback amount on waiver. These changes are **not** in the deployed source hash/address below and have no live Studionet evidence yet.

Focused retest of #12, #17, #19, #21, and #33: **14 passed**. Full Direct Mode suite: **97 passed**. GenVM `check` and `validate`: passed (3 checks; **47 methods**, 20 views and 27 writes). The Windows console initially failed to encode the linter checkmark under CP1252; rerunning with `$env:PYTHONIOENCODING='utf-8'` passed. The installed CLI does not expose the current documented fee-estimation command; no deployment or further network write was sent because the earlier authorized cumulative cap is not confirmed fee-inclusive.

## Current source

Contract source SHA-256: `0E7A7723C259DCF1CFAAEC8AFE62F873D6746335D63E9D8A1C2C7B25DFC4A1FE`.
The byte-identical source is deployed at `0x142A372b4cA7cf3784327DFA2e2B0eCF45D4eA14` on Studio Network
(chain `61999`); deployment transaction `0x34ee57640f53c1826dc77e5900d66a81bb05f2c59fb899d4f19168b00143329e`.
The contract pins `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.
Environment: Python 3.12, `genlayer-test==0.29.2`, `genvm-linter==0.11.1rc2`, pytest 8.4.2.

## Gate B — Direct Mode

Command: `pytest -q tests/direct --tb=short`

Result on the current reviewer-fix candidate: **94 passed**. No tests were skipped. The five added regression cases
cover PARTIAL/INSUFFICIENT settlement in ordinary and milestone flows, evidence-bound warranty targeting and appeal
binding carry-forward, bilateral ambiguity acknowledgements, warranty/milestone exclusion in both configuration
orders, and milestone consumer views. The tests cover lifecycle authorization,
API and agent judgments, evidence integrity, appeals, warranty, milestones, settlement conservation, withdrawal, and
adversarial/boundary cases. They use Direct Mode and are not evidence of network consensus by themselves.

## Gate C — GenVM lint and schema

Commands: `genvm-lint check contracts/speclock.py` and `genvm-lint validate contracts/speclock.py`.

Result on the current candidate: **passed** (3 lint checks; schema validation passed). Contract: `SpecLock`; methods:
**45** (20 views, 25 writes). The linter reports that a newer runner exists; this project retains its pinned runtime
hash.

On Windows, set `$env:PYTHONIOENCODING='utf-8'` before running the linter if the console's default code page cannot
print its checkmark output. The initial CP1252 console attempt raised `UnicodeEncodeError`; rerunning with UTF-8 passed.

## Gate D — Clean clone

Verified from a fresh clone of commit `b6fdb8a6e02b93acaa6d2dc942bf04b9edff96df` in `C:\Users\USERpc\AppData\Local\Temp\speclock-clean-b6fdb8a`. `pytest -q tests/direct`: **94 passed**. `genvm-lint check contracts/speclock.py` and `genvm-lint validate contracts/speclock.py`: passed (3 checks; 45 methods) after setting `PYTHONIOENCODING=utf-8` for Windows console output.

## Gate E — Studionet

Latest candidate deployment: `0x142A372b4cA7cf3784327DFA2e2B0eCF45D4eA14`, chain `61999`, deployment transaction `0x34ee57640f53c1826dc77e5900d66a81bb05f2c59fb899d4f19168b00143329e`, source SHA-256 `0E7A7723C259DCF1CFAAEC8AFE62F873D6746335D63E9D8A1C2C7B25DFC4A1FE`. Deployment finalized with `MAJORITY_AGREE` and leader `SUCCESS`; `genlayer schema` returned 45 methods. Current-source API/agent PASS and FAIL, PARTIAL settlement, warranty claim resolution, real withdrawals, and milestone settlement/replay were executed and read back. See `docs/evidence/studionet-reviewer-fix-2026-10-18.md` and `docs/evidence/studionet-negative-regressions-2026-10-18.json`.

This is representative, not exhaustive. The deployed release predates the candidate's #12 deadline implementation; #12 and #17 are local-only pending network verification, while #19, #21, and #33 remain partial as detailed in `docs/FEATURE_MATRIX.md`. Appeal/procedural-review and non-milestone inconclusive recovery were not repeated against this release. Cumulative gross transfer volume is recorded as 0.017038 GEN before unitemized fees; it is not exact fee-inclusive accounting.

## Integration tests

No separate integration-test suite is provided. Direct Mode uses the GenLayer test harness; Studionet transactions
are recorded as reproducible evidence rather than being exposed as a secret-bearing automated test. This report does
not claim all 38 capabilities are complete.
