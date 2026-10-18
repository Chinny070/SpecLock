# SpecLock

A single, standalone GenLayer Intelligent Contract for universal digital-delivery agreement and adjudication. One canonical contract (`contracts/speclock.py`), two fully-implemented evaluation profiles, no marketplace frontend/database/off-chain adjudicator.

**Status: deadline-security fix deployed and byte-matched; live positive and negative API lifecycles verified. Natural post-deadline behavior remains unverified.** Current Studionet contract [`0xD47ed31c0b58100101Ec1d7DE1c11bB15A252DBE`](https://genlayer-explorer.vercel.app/address/0xD47ed31c0b58100101Ec1d7DE1c11bB15A252DBE), chain `61999`, deployment tx `0x6505c1e2602432706a9e40d258ae53b1d514e4c7a54384b1eca91a4a695490c7`; source SHA-256 `5F5204E9BF3941D688ABD0F34A31FCF2C788A29772A1A0237585008D8A54AC7F`. Deployment finalized with `MAJORITY_AGREE` and leader `execution_result: SUCCESS`; the callable schema exposes 47 methods. Clean-clone verification passes 103 Direct Mode tests and both GenVM lint/schema checks. Live API `PASS` and `FAIL` evaluations, settlement, and matching beneficiary withdrawals are recorded in `docs/DEPLOYMENT.md` and the evidence JSON files. The expiry route still needs a natural seven-day deadline and on-chain transaction. SpecLock is not yet submission-ready for that required proof.

## Quickstart

```bash
pip install genlayer-test genvm-linter
genvm-lint check contracts/speclock.py
genvm-lint validate contracts/speclock.py
pytest -q tests/direct --tb=short
```

## Trust boundary (short version — full detail in `docs/THREAT_MODEL.md` and `docs/PROTOCOL.md`)

- **Deterministic contract code** owns authorization, lifecycle, bounds, the specification compiler, and settlement math.
- **Validator-adjudicated (nondeterministic) code** only answers "what does the evidence show for this one frozen criterion" — every leader judgment is independently re-derived and compared by validators via `gl.vm.run_nondet_unsafe`, never trusted on the leader's say-so alone (see `docs/CONSENSUS.md`).
- **Native-value escrow — live-verified.** `fund_agreement`/`file_appeal` are payable; `_settle`/`resolve_appeal` credit caller-owned pull balances and `withdraw()` pays them through `gl.evm.contract_interface`. Real deposits, settlement payouts, appeal bonds, rejected-value refunds, double-withdrawal rejection, and no-balance rejection have live evidence. Parent withdrawals finalized successfully; EVM child receipts report `NO_MAJORITY` while `value_credited:true`, so the transfer credit and recipient balance—not the child result label alone—are the payout evidence. Latest evidence and residual risks are in `docs/DEPLOYMENT.md` and `docs/SECURITY.md`.
- **Deadline security:** Contract deadlines use the GenVM transaction-pinned time returned by `datetime.now(timezone.utc)`; callers do not supply the clock. After delivery expiry, no submitted evidence means refund, while timely evidence must pass through validator-backed evaluation before payment is decided. Evaluated evidence follows the existing appeal/finality/settlement path. Early cancellation remains bilateral. The current Studionet deployment predates this correction; see `docs/TESTING.md` and `docs/DEPLOYMENT.md` for the verification state.

## Two evaluation profiles

### API delivery

```python
agreement_id = contract.create_agreement(
    provider_address, "api_delivery",
    "Deliver a GET /health endpoint returning {\"status\": \"ok\"}",
    [{"id": "c1", "description": "GET /health returns status ok",
      "priority": "required", "evidence_method": "http:c1"}],
    max_resubmissions=1,
)
```
Validators distinguish `reachable` from `functional` — an HTTP 200 alone is never treated as delivery (see `_probe_api_criterion` in `contracts/speclock.py`).

### AI-agent delivery

```python
agreement_id = contract.create_agreement(
    provider_address, "ai_agent_delivery",
    "Agent must summarize the attached document in under 200 words with no fabricated citations.",
    [{"id": "c1", "description": "Summary under 200 words, no fabricated citations",
      "priority": "required", "evidence_method": "artifact:c1"}],
    1,
)
```
A self-reported agent trace is never treated as independent proof — every validator independently re-judges the same frozen criterion against the same evidence (see `_judge_agent_criterion`).

## Lifecycle

`create_agreement → accept_agreement → fund_agreement → freeze_agreement → submit_evidence(×n) → request_evaluation → [file_appeal → resolve_appeal]* → finalize_verdict → settle | recover_inconclusive`

Full transition table and terminal fund-allocation matrix: `docs/STATE_MACHINE.md`.

## Documentation index

- `DECISION.md` — repository audit, toolchain, and material empirical findings that shaped the design.
- `docs/PROTOCOL.md`, `docs/STATE_MACHINE.md`, `docs/CONSENSUS.md` — design.
- `docs/THREAT_MODEL.md`, `docs/SECURITY.md` — adversarial analysis.
- `docs/GENLAYER_CAPABILITIES.md` — what is confirmed vs. unverified vs. absent in this runtime.
- `docs/FEATURE_MATRIX.md`, `docs/ACCEPTANCE_TEST_MATRIX.md` — per-capability and per-scenario status.
- `docs/TESTING.md`, `docs/DEPLOYMENT.md` — exact reproducible commands/results and deployment gap.
- `SUBMISSION.md` — reviewer-facing honest verdict.

## License

See `LICENSE`.
