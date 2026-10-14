# Security

## Bounds (enforced in `contracts/speclock.py`, exercised in `tests/direct/test_speclock_security.py`)

`MAX_CRITERIA=32`, `MAX_SPEC_CHARS=20000`, `MAX_CRITERION_CHARS=2000`, `MAX_EVIDENCE_URL_CHARS=2000`, `MAX_EVIDENCE_METADATA_CHARS=4000`, `MAX_EVIDENCE_PER_AGREEMENT=64`, `MAX_APPEAL_ROUNDS=2`, `MAX_APPEAL_GROUNDS_CHARS=2000`, `MAX_RESUBMISSIONS=3` (per-agreement cap, configurable lower at creation), `MAX_RATIONALE_CHARS=4000`, `MAX_FETCH_BYTES=200000`, `PAGE_SIZE_MAX=50`.

There is no caller-supplied time/clock bound in this contract at all (a prior revision had one; it was audited, found manipulable, and removed — see `docs/THREAT_MODEL.md` "clock redesign"). Deadline-shaped behavior is now enforced by mutual two-party consent (`finalize_verdict`, `cancel_or_expire`), which cannot be forced by a single sender regardless of any value they might supply.

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

## Native-value custody: root-caused, fixed, Direct-Mode-verified; live re-verification pending a platform outage

A first real escrow implementation (payable deposit + `gl.get_contract_at(...).emit_transfer(...)` payout) was built and deployed for live testing. Deposits succeeded; the payout failed against a plain wallet address with `result_name:"NO_MAJORITY"` and a decoded `"Contract ... not found"` error. That was root-caused, not merely observed and avoided: `get_contract_at` addresses another GenLayer intelligent contract, which is the wrong tool for paying an ordinary wallet. The fix — `gl.evm.contract_interface`, an EVM-layer proxy (`_EthAccount` in `contracts/speclock.py`) — was found via a sibling project in this account (AgentCourt) that independently solved the identical problem on the identical pinned runner and network, with real live proof (a disposable wallet's balance genuinely moved via this exact call). `fund_agreement`/`file_appeal` are payable again; `_settle`/`resolve_appeal` credit a pull-payment `claimable` balance (never calling `emit_transfer` themselves, keeping checks-effects-interactions intact); a new `withdraw()` method lets the credited party trigger the real payout. This is covered by 8 new Direct Mode tests — 52/52 pass, lint clean. Two attempts to redeploy and live-verify this fix on Studio Network were both blocked by a deployment-registration outage unrelated to the contract (confirmed via raw RPC calls against the chain, bypassing the CLI/SDK, and confirmed not a general outage since calls against a pre-existing deployment succeeded normally in the same session) — not retried further per the standing instruction against repeatedly retrying a blocked approach. The current contract therefore holds no real native value at any point in its *deployed* lifecycle yet, even though the fix is complete and corroborated by independent live evidence on the same runtime. Full record: `docs/DEPLOYMENT.md` "Native-value escrow", `docs/THREAT_MODEL.md`, `DECISION.md` items 8 and 10.

## Repository credential-exposure audit (performed on request)

A full `git log --all -p` scan of this repository's history for password/private-key/seed-phrase patterns found exactly one real exposure: the local test keystore password for the `speclock-provider` account (a disposable account created during this project's live Studionet work, holding only a small amount of testnet GEN, never the repository owner's real wallet) was committed in plaintext in an early draft of `docs/RUNBOOK_REMAINING_STEPS.md` (commit `c13bbb1`). It was caught and redacted from the file content in a later commit (`2116a79`) before being noticed as still present in history — **the password remains permanently visible in that commit's diff on GitHub**, since this repository's history has not been rewritten (this project does not force-push; see `DECISION.md`/git safety rules). Treat that keystore's password as burned: it must not be reused for anything else. No other credential pattern (private keys, seed phrases, API keys, other passwords) was found anywhere in the repository's full git history. No private key for `speclock-provider` or any other account was ever written to a file in this repository at any point — only the one password string, for a throwaway testnet-only account.

## What was NOT independently security-tested

- No fuzzing/property-based testing was run (no `hypothesis` strategies written, though the `hypothesis` plugin is present in the test environment).
- No adversarial multi-validator consensus attack (forged leader vs. honest validators) was exercised — Direct Mode cannot run it (see `docs/CONSENSUS.md`).
- No static analysis beyond `genvm-lint check`/`validate` (0 errors, 0 warnings) was run.
