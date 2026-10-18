# Testing and verification

## Deadline-security release (2026-10-18)

The candidate changes `contracts/speclock.py` so expiry does not treat a missing evaluation request as proof of failed delivery. Timely evidence is evaluated through the existing validator-backed API/agent process even when evaluation is triggered after the delivery deadline. No-evidence expiry still refunds. Prior evaluated verdicts return to their normal finality and settlement path if a requested resubmission receives no new evidence. Milestone expiry is criterion-scoped, and the resubmission deadline remains anchored to the resubmission request.

The prior 97 test cases remain present. The vulnerable refund expectation was corrected in place to require evaluation of timely evidence; six new tests were added. The full candidate suite contains **103 tests**.

## Gate B — full Direct Mode suite

Command: `pytest -q tests/direct --tb=short`

Result: **103 passed in 25.20s; zero failures; zero skipped**.

Focused changed areas:

- `pytest -q tests/direct/test_speclock_lifecycle.py tests/direct/test_speclock_security.py tests/direct/test_speclock_milestones.py --tb=short`
- Result: **54 passed; zero failures; zero skipped**.

Regression coverage includes timely evidence evaluated after expiry; direct permissionless overdue evaluation; no-evidence refund and exact fund conservation; evidence rejection after the deadline; exact inclusive deadline boundary; separate resubmission timing and deadline; no-follow-up resubmission restoring an already evaluated verdict; relevant-vs-unrelated milestone evidence; and pre-deadline caller authorization. Existing API/agent evaluation, digest integrity, appeals, warranties, milestones, withdrawal protection, and settlement replay tests remain in the suite.

## Gate C — GenVM lint and schema

Commands:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
genvm-lint check contracts/speclock.py
genvm-lint validate contracts/speclock.py
```

Both passed. `check`: **3 checks passed**. `validate`: passed for `SpecLock`, **47 methods (20 views, 27 writes)**. On Windows the UTF-8 environment setting avoids a CP1252 console encoding error when the linter prints its checkmark. The contract retains the pinned `py-genlayer` runner hash.

## Gate D — clean GitHub clone

**Passed** at commit `b1412efa0e0279aaaa967aec62205722a09b916a`: fresh clone reported 103 passed, zero failures, zero skipped; both GenVM commands passed. Normalized source SHA-256: `5F5204E9BF3941D688ABD0F34A31FCF2C788A29772A1A0237585008D8A54AC7F`.

## Gate E — Studionet

The corrected release is deployed at `0xD47ed31c0b58100101Ec1d7DE1c11bB15A252DBE` (chain `61999`, transaction `0x6505c1e2602432706a9e40d258ae53b1d514e4c7`). Receipt is FINALIZED/MAJORITY_AGREE with leader SUCCESS; retrieved source hash matches the tested source. The schema is callable with 47 methods. Positive and negative live API lifecycles, including evaluation, settlement, and withdrawal, are recorded in `docs/evidence/studionet-deadline-candidate-lifecycle-2026-10-18.json` and `docs/evidence/studionet-deadline-candidate-lifecycle-attempt2-2026-10-18.json`.

The fixed delivery window is seven days, and the resubmission window is seven days from its own request time. Direct Mode proves boundary and expiry behavior deterministically, but not elapsed real network time. The required live post-deadline run must wait for the on-chain deadline; no shortened production deadline or mocked timestamp is accepted. Deployment and ordinary PASS/FAIL lifecycle success do not satisfy live deadline acceptance.

## Historical verification

Earlier test counts and deployments are retained in `docs/DEPLOYMENT.md` and the feature matrix. Those records remain historical evidence for the exact source versions identified there; they do not establish behavior of this candidate source.
