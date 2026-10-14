# SpecLock

A single, standalone GenLayer Intelligent Contract for universal digital-delivery agreement and adjudication. One canonical contract (`contracts/speclock.py`), two fully-implemented evaluation profiles, no marketplace frontend/database/off-chain adjudicator.

**Status: deployed to GenLayer Studio Network, lifecycle exercise in progress.** See `SUBMISSION.md` for the honest verdict and `docs/FEATURE_MATRIX.md` for per-capability status. 42/42 Direct Mode tests pass; `genvm-lint check`/`validate` are clean. Live at `0x713036220DE89a077fea1C3203C2510adB67f992` (chain id `61999`) with three real, `FINALIZED` `create_agreement` transactions under 5-validator consensus — see `docs/DEPLOYMENT.md` for the evidence and `docs/RUNBOOK_REMAINING_STEPS.md` for what's left.

## Quickstart

```bash
pip install genlayer-test genvm-linter
genvm-lint check contracts/speclock.py
gltest tests/direct/ -v
```

## Trust boundary (short version — full detail in `docs/THREAT_MODEL.md` and `docs/PROTOCOL.md`)

- **Deterministic contract code** owns authorization, lifecycle, bounds, the specification compiler, and settlement math.
- **Validator-adjudicated (nondeterministic) code** only answers "what does the evidence show for this one frozen criterion" — every leader judgment is independently re-derived and compared by validators via `gl.vm.run_nondet_unsafe`, never trusted on the leader's say-so alone (see `docs/CONSENSUS.md`).
- **No verified native-value escrow.** `fund_agreement` is bookkeeping only — see `docs/GENLAYER_CAPABILITIES.md` and `docs/DEPLOYMENT.md`.
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
