# Security

## Bounds (enforced in `contracts/speclock.py`, exercised in `tests/direct/test_speclock_security.py`)

`MAX_CRITERIA=32`, `MAX_SPEC_CHARS=20000`, `MAX_CRITERION_CHARS=2000`, `MAX_EVIDENCE_URL_CHARS=2000`, `MAX_EVIDENCE_METADATA_CHARS=4000`, `MAX_EVIDENCE_PER_AGREEMENT=64`, `MAX_APPEAL_ROUNDS=2`, `MAX_APPEAL_GROUNDS_CHARS=2000`, `MAX_RESUBMISSIONS=3` (per-agreement cap, configurable lower at creation), `MAX_RATIONALE_CHARS=4000`, `MAX_FETCH_BYTES=200000`, `PAGE_SIZE_MAX=50`, `MAX_CLOCK_ADVANCE_SECONDS` (10 years, bounds the logical-clock griefing surface described in `docs/THREAT_MODEL.md`).

## URL / SSRF handling

`_validate_url` rejects: non-`https` schemes, embedded userinfo (`user:pass@`), and a hostname blocklist (`localhost`, `127.`, `0.0.0.0`, `::1`, `169.254.`, `10.`, `192.168.`). This is a contract-level defense-in-depth check; it does not replace and was not verified against GenVM's own network egress policy, which could not be independently inspected from this environment (see `docs/GENLAYER_CAPABILITIES.md`).

## Parser hardening

- `_parse_json_strict` rejects oversized and non-dict JSON.
- `_judge_agent_criterion`'s `judge()` validates `finding`/`sufficiency` against closed enum sets and raises `[LLM_ERROR]` on any other value, duplicate/extra fields are simply ignored (not trusted as decision-critical) rather than causing a crash.
- `_compile_criteria` rejects duplicate criterion ids, out-of-bounds counts/lengths, and invalid `priority` values before an agreement can ever freeze.
- No `eval()` is used anywhere in the contract.

## Authorization

Every write method checks either exact caller identity (`accept_agreement` requires `caller == agreement.provider`; `fund_agreement`/`freeze_agreement`/etc. require `_is_party`) or an explicit role split (buyer vs. provider in `submit_evidence`). `recover_inconclusive` and `settle` are callable by either party since they only ever move funds according to an already-finalized, deterministic formula — there is no discretionary amount either caller can choose.

## Checks-effects-interactions / idempotency

- `settle()` is guarded by `agreement.settlement_id == ""`, preventing double settlement.
- `_settle()` always recomputes the full allocation and asserts conservation (`released+refunded+retained == funded`) before writing state — a reconciliation failure reverts the entire call rather than partially applying.
- `file_appeal`/`resolve_appeal` check `resolution == "FILED_UNADJUDICATED"` before allowing resolution, so a resolved appeal cannot be re-resolved.

## Immutable fingerprints

`spec_fingerprint = sha256(spec_text || criteria_json || policy_id || policy_version)`, computed once in `create_agreement` and never recomputed; `get_policy_fingerprint` exposes it as a view so a caller can confirm an agreement is still pinned to its original terms even after a newer `POLICY_VERSION` constant ships in a future contract revision.

## What was NOT independently security-tested

- No fuzzing/property-based testing was run (no `hypothesis` strategies written, though the `hypothesis` plugin is present in the test environment).
- No adversarial multi-validator consensus attack (forged leader vs. honest validators) was exercised — Direct Mode cannot run it (see `docs/CONSENSUS.md`).
- No static analysis beyond `genvm-lint check`/`validate` (0 errors, 0 warnings) was run.
