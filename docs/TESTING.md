# Testing and verification

## Deadline-security candidate (2026-10-18)

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

**Pending.** The source changes have not yet been pushed and tested from a fresh clone. This gate must pass before this candidate is called reproducible or deployed.

## Gate E — Studionet

The latest existing deployment is `0xDFb69c1890F72c7b791A938ed36C5103582E6F19` (chain `61999`, deployment transaction `0x47a258b79297644bce2d54ba8eea678177b27856181577b685d9d3adfbfc35c`). Its source SHA-256 is `CEC00C69E57E6AE1B70C77BE49CFFEEB912F2D55D15E42AF75A2B6687ABB6F5C`; it predates this deadline correction. **It is not evidence that the deadline fix is deployed.**

Redeployment is gated on the clean-clone suite and both GenVM checks. The fixed delivery window is seven days, and the resubmission window is also seven days from its own request time. Direct Mode can verify boundary and expiry behavior deterministically, but it cannot prove elapsed real network time. A live deadline demonstration must wait for the on-chain deadline; no shortened production deadline or mocked network evidence is accepted as a substitute. Deployment and live transaction hashes, outcomes, and balance changes will be recorded in `docs/DEPLOYMENT.md` only after they actually occur.

## Historical verification

Earlier test counts and deployments are retained in `docs/DEPLOYMENT.md` and the feature matrix. Those records remain historical evidence for the exact source versions identified there; they do not establish behavior of this candidate source.
