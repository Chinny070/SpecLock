# SpecLock

A single, standalone GenLayer Intelligent Contract for universal digital-delivery agreement and adjudication. One canonical contract (`contracts/speclock.py`), two fully-implemented evaluation profiles, no marketplace frontend/database/off-chain adjudicator.

**Status: deployed and functionally proven on GenLayer Studio Network, both evaluation profiles — 33 of 38 numbered capabilities now `IMPLEMENTED_VERIFIED` on a live network, including a fully live-verified real native-value escrow, a real fund-lock bug, and a real SSRF bypass, all found and fixed during a full two-pass capability audit.** See `SUBMISSION.md` for the honest verdict and `docs/FEATURE_MATRIX.md` for the complete per-capability table. 66/66 Direct Mode tests pass; `genvm-lint check`/`validate` are clean. Current contract `0xc758b9E6763fdB1C80c758f8D26eD04Acc063254` (chain id `61999`): real payable funding, real appeal bonds, real GEN withdrawals, a fixed `request_resubmission` fund-lock, a fixed IPv6 SSRF bypass, deterministic `PARTIAL` settlement, a bounded procedural-review tier, narrowed appeal re-evaluation, and an on-chain settlement-replay audit view — all live-verified. Predecessor contracts (`0x2671cd7...`, `0xbE2a981...`, `0xD5602E88...`) carry the resubmission fix, the escrow's first live verification, and four complete API/agent lifecycle agreements (`FAIL`/`PASS`/`UNVERIFIABLE` with a live `recover_inconclusive` refund). See `docs/DEPLOYMENT.md` for the full transaction-by-transaction evidence on all of it.

## Quickstart

```bash
pip install genlayer-test genvm-linter
genvm-lint check contracts/speclock.py
gltest tests/direct/ -v
```

## Trust boundary (short version — full detail in `docs/THREAT_MODEL.md` and `docs/PROTOCOL.md`)

- **Deterministic contract code** owns authorization, lifecycle, bounds, the specification compiler, and settlement math.
- **Validator-adjudicated (nondeterministic) code** only answers "what does the evidence show for this one frozen criterion" — every leader judgment is independently re-derived and compared by validators via `gl.vm.run_nondet_unsafe`, never trusted on the leader's say-so alone (see `docs/CONSENSUS.md`).
- **Native-value escrow — live-verified.** `fund_agreement`/`file_appeal` are payable, using `gl.evm.contract_interface` (not `gl.get_contract_at`, which is the wrong primitive for paying a plain wallet and the root cause of an earlier live failure); `_settle`/`resolve_appeal` credit a pull-payment `claimable` balance and `withdraw()` pays it out. Direct-Mode-verified (66/66 tests) and fully live-verified on Studio Network: real deposits, real settlements, a real appeal bond, and real GEN withdrawals, with double-withdrawal and no-balance-withdrawal both live-tested and correctly rejected — see `docs/GENLAYER_CAPABILITIES.md`, `docs/DEPLOYMENT.md`, and `docs/SECURITY.md`.
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
