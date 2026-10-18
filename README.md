# SpecLock

A single, standalone GenLayer Intelligent Contract for universal digital-delivery agreement and adjudication. One canonical contract (`contracts/speclock.py`), two fully-implemented evaluation profiles, no marketplace frontend/database/off-chain adjudicator.

**Status: deployed release verified; newer local review candidate pending deployment.** Deployed contract `0x142A372b4cA7cf3784327DFA2e2B0eCF45D4eA14` (chain `61999`), deploy tx `0x34ee57640f53c1826dc77e5900d66a81bb05f2c59fb899d4f19168b00143329e`, source SHA-256 `0E7A7723C259DCF1CFAAEC8AFE62F873D6746335D63E9D8A1C2C7B25DFC4A1FE`. Its API/agent outcomes, escrow, warranty and milestone evidence are recorded in `docs/evidence/studionet-reviewer-fix-2026-10-18.md`. The newer local candidate adds transaction-time deadlines and expanded URL/IP checks: 97 Direct Mode tests pass and GenVM lint/schema pass (47 methods), but it is not deployed. Two capabilities are local-only (#12, #17) and three remain partial (#19, #21, #33). Fee-inclusive testnet spending is not established, so this project is not claimed submission-ready.

## Quickstart

```bash
pip install genlayer-test genvm-linter
genvm-lint check contracts/speclock.py
gltest tests/direct/ -v
```

## Trust boundary (short version — full detail in `docs/THREAT_MODEL.md` and `docs/PROTOCOL.md`)

- **Deterministic contract code** owns authorization, lifecycle, bounds, the specification compiler, and settlement math.
- **Validator-adjudicated (nondeterministic) code** only answers "what does the evidence show for this one frozen criterion" — every leader judgment is independently re-derived and compared by validators via `gl.vm.run_nondet_unsafe`, never trusted on the leader's say-so alone (see `docs/CONSENSUS.md`).
- **Native-value escrow — live-verified.** `fund_agreement`/`file_appeal` are payable; `_settle`/`resolve_appeal` credit caller-owned pull balances and `withdraw()` pays them through `gl.evm.contract_interface`. Real deposits, settlement payouts, appeal bonds, rejected-value refunds, double-withdrawal rejection, and no-balance rejection have live evidence. Parent withdrawals finalized successfully; EVM child receipts report `NO_MAJORITY` while `value_credited:true`, so the transfer credit and recipient balance—not the child result label alone—are the payout evidence. Latest evidence and residual risks are in `docs/DEPLOYMENT.md` and `docs/SECURITY.md`.
- **Deadline enforcement is a safety/liveness trade-off, stated plainly.** Mutual two-party consent (no caller-supplied time anywhere) fully closes the manipulation hole that a prior caller-supplied-timestamp design could not. It does not, and cannot, guarantee an agreement always resolves: a silent counterparty after appeals are exhausted can stall it permanently, with no unilateral escape. This was found and honestly reclassified during a capability audit rather than left as an over-claimed status — see `docs/THREAT_MODEL.md` "The honest cost of this design."
- **No wall-clock time is used anywhere.** The installed runner exposes no usable on-chain timestamp (see `docs/GENLAYER_CAPABILITIES.md`). An earlier caller-supplied-timestamp design was audited, found manipulable by a self-interested party, and replaced: `finalize_verdict` and the FROZEN branch of `cancel_or_expire` now require both buyer and provider to separately consent — neither can be forced by one party alone (`docs/THREAT_MODEL.md` "clock redesign").

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
