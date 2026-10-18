# Security

## Bounds (enforced in `contracts/speclock.py`, exercised in `tests/direct/test_speclock_security.py`)

`MAX_CRITERIA=32`, `MAX_SPEC_CHARS=20000`, `MAX_CRITERION_CHARS=2000`, `MAX_EVIDENCE_URL_CHARS=2000`, `MAX_EVIDENCE_METADATA_CHARS=4000`, `MAX_EVIDENCE_PER_AGREEMENT=64`, `MAX_APPEAL_ROUNDS=2`, `MAX_APPEAL_GROUNDS_CHARS=2000`, `MAX_RESUBMISSIONS=3` (per-agreement cap, configurable lower at creation), `MAX_RATIONALE_CHARS=4000`, `MAX_FETCH_BYTES=200000`, `PAGE_SIZE_MAX=50`.

The candidate source uses `datetime.now(timezone.utc)` as a transaction-pinned timestamp for deadlines; no caller can supply the clock. GenLayer's official runtime documentation says validators observe the same transaction timestamp. The candidate passes Direct Mode deadline-boundary tests; its clean-clone and Studionet verification are pending. The existing deployment at `0xDFb69c1890F72c7b791A938ed36C5103582E6F19` predates the post-deadline evidence-routing fix and is not proof of that behavior. See `docs/GENLAYER_CAPABILITIES.md` and `docs/TESTING.md`.

## URL / SSRF handling

`_validate_url` rejects non-HTTPS schemes, embedded userinfo, standard and legacy numeric nonpublic IP literals, scoped IPs, and local hostname suffixes. These checks are in the current deployed source and have Direct Mode coverage; adversarial live URL evaluation has not yet been run against this release. They are defense-in-depth, not a proof against DNS rebinding or a substitute for GenVM's egress policy.

## Parser hardening

- `_parse_json_strict` rejects oversized and non-dict JSON.
- `_judge_agent_criterion`'s `judge()` validates `finding`/`sufficiency` against closed enum sets and raises `[LLM_ERROR]` on any other value, duplicate/extra fields are simply ignored (not trusted as decision-critical) rather than causing a crash.
- `_compile_criteria` rejects duplicate criterion ids, out-of-bounds counts/lengths, and invalid `priority` values before an agreement can ever freeze.
- No `eval()` is used anywhere in the contract.

## Authorization

Every write method checks either exact caller identity (`accept_agreement` requires `caller == agreement.provider`; `fund_agreement`/`freeze_agreement`/etc. require `_is_party`) or an explicit role split (buyer vs. provider in `submit_evidence`). `recover_inconclusive` restricts the caller to a party via `_is_party`; `settle` imposes no caller-identity check at all (callable by anyone) — both are safe regardless, since they only ever move funds according to an already-finalized, deterministic formula into the agreement's own `buyer`/`provider` fields, never the caller's address — there is no discretionary amount or recipient either caller can choose. See "Security audit of the payable funding / claimable / withdraw implementation" below for the full native-value-specific audit.

## Checks-effects-interactions / idempotency

- `settle()` is guarded by `agreement.settlement_id == ""`, preventing double settlement.
- `_settle()` always recomputes the full allocation and asserts conservation (`released+refunded+retained == funded`) before writing state — a reconciliation failure reverts the entire call rather than partially applying.
- `file_appeal`/`resolve_appeal` check `resolution == "FILED_UNADJUDICATED"` before allowing resolution, so a resolved appeal cannot be re-resolved.

## Immutable fingerprints

`spec_fingerprint = sha256(spec_text || criteria_json || policy_id || policy_version)`, computed once in `create_agreement` and never recomputed; `get_policy_fingerprint` exposes it as a view so a caller can confirm an agreement is still pinned to its original terms even after a newer `POLICY_VERSION` constant ships in a future contract revision.

## Native-value custody: root-caused, fixed, redeployed, live-verified

A first real escrow implementation (payable deposit + `gl.get_contract_at(...).emit_transfer(...)` payout) was built and deployed for live testing. Deposits succeeded; the payout failed against a plain wallet address with `result_name:"NO_MAJORITY"` and a decoded `"Contract ... not found"` error. That was root-caused, not merely observed and avoided: `get_contract_at` addresses another GenLayer intelligent contract, which is the wrong tool for paying an ordinary wallet. The fix — `gl.evm.contract_interface`, an EVM-layer proxy (`_EthAccount` in `contracts/speclock.py`) — was found via a sibling project in this account (AgentCourt) that independently solved the identical problem on the identical pinned runner and network, with real live proof (a disposable wallet's balance genuinely moved via this exact call). `fund_agreement`/`file_appeal` are payable again; `_settle`/`resolve_appeal` credit a pull-payment `claimable` balance (never calling `emit_transfer` themselves, keeping checks-effects-interactions intact); a new `withdraw()` method lets the credited party trigger the real payout. This is covered by 8 new Direct Mode tests — 52/52 pass, lint clean. Two attempts to redeploy and live-verify this fix both failed at the constructor-call level (`execution_result: "ERROR"` despite `status_name: "FINALIZED"`) due to a malformed `genlayer deploy --args '[]'` CLI invocation — the variadic `--args` flag passed one literal string argument instead of zero, confirmed by comparing raw deploy calldata byte-for-byte against the working deployment. Not a platform issue and not a contract defect; corrected by omitting `--args` entirely, redeployed to `0xbE2a98135e41B4fE722919b87024D867F8De8343`, and **fully live-verified**: a real `PASS` agreement settled with the provider withdrawing a real GEN payout (independent `getBalance` check matched the settled amount exactly), and a real `FAIL` agreement was appealed with a real bond, correctly `REJECTED` on re-evaluation against unchanged evidence, with the bond correctly credited to the non-appellant party and withdrawn for real. Double-withdrawal and no-balance-withdrawal were both tested live and correctly rejected. See `docs/DEPLOYMENT.md` "Native-value escrow: live-verified" for the full transaction-by-transaction record, `docs/THREAT_MODEL.md`, `DECISION.md` items 8 and 10.

### Residual risk: a failed `withdraw()` payout cannot be reconciled by the contract itself

`withdraw()` zeroes the caller's `claimable` balance before calling `_EthAccount(...).emit_transfer(...)` (checks-effects-interactions, preventing double-withdrawal and reentrancy — see the audit below). But GenVM gives the contract no callback or readable result for whether that triggered external transfer actually lands; if it fails for any reason after the zeroing, the credited amount is not recoverable from on-chain state alone. This is a liveness/availability risk (funds could become stuck, requiring off-chain/support intervention to trace via the triggered transaction's own receipt), not a confidentiality/integrity risk (no double-spend, no unauthorized redirection) — and it is the same architectural tradeoff AgentCourt's identical `withdraw()` pattern accepts. It is not fixable by the contract alone without a GenVM-side transfer-result callback, which does not appear to exist in the installed SDK.

### Security audit of the payable funding / claimable / withdraw implementation

- **Double withdrawal**: prevented, confirmed live. `withdraw()` reads `claimable[caller]`, requires it positive, and sets it to `0` *before* issuing the external transfer — a second call in a later transaction sees a zero balance and reverts (`"nothing to withdraw"`). Covered by `test_withdraw_zeroes_claimable_and_returns_amount`, and live-tested on Studio Network: a provider's real second `withdraw()` call after a successful first one correctly reverted (`docs/DEPLOYMENT.md` "Native-value escrow: live-verified").
- **Unauthorized withdrawal**: prevented, confirmed live. `withdraw()` takes no address parameter; it only ever pays `gl.message.sender_address`'s own balance. No caller can withdraw another party's funds — live-tested by having a party with zero claimable balance call `withdraw()`, which correctly reverted.
- **Reentrancy**: not applicable in the classic sense. `emit_transfer` is an asynchronously scheduled `EthSend` that executes on protocol finalization, not a synchronous call that could re-enter contract code during `withdraw()`'s own execution; and even so, state is zeroed first. No external call appears inside any nondeterministic block (`gl.vm.run_nondet_unsafe`) anywhere in the contract.
- **Balance conservation**: every `claimable` credit traces back to a verified prior real-value transfer — `_settle` only credits amounts that satisfy `released + refunded + retained == funded_amount` (itself set to the exact `gl.message.value` received by `fund_agreement`), and appeal-bond credits are bounded by `bond_amount` (set to the exact value received by `file_appeal`). No code path credits more than was actually received.
- **Unauthorized `settle()`/`recover_inconclusive()` calls**: `settle()` has no caller-identity check (callable by any address), which is safe because the credited beneficiaries are always derived from the agreement's own `buyer`/`provider` fields, never from the caller — a permissionless trigger, not a permissionless beneficiary. `recover_inconclusive()` additionally restricts the caller to a party via `_is_party`. (Note: an earlier draft of this document said `settle()` was "callable by either party"; the code imposes no such restriction — corrected here for accuracy.)
- **Residual risk**: see the subsection above (failed external transfer after zeroing).

## Repository credential-exposure audit (performed on request)

A full `git log --all -p` scan of this repository's history for password/private-key/seed-phrase patterns found exactly one real exposure: the local test keystore password for the `speclock-provider` account (a disposable account created during this project's live Studionet work, holding only a small amount of testnet GEN, never the repository owner's real wallet) was committed in plaintext in an early draft of `docs/RUNBOOK_REMAINING_STEPS.md` (commit `c13bbb1`). It was caught and redacted from the file content in a later commit (`2116a79`) before being noticed as still present in history — **the password remains permanently visible in that commit's diff on GitHub**, since this repository's history has not been rewritten (this project does not force-push; see `DECISION.md`/git safety rules). Treat that keystore's password as burned: it must not be reused for anything else. No other credential pattern (private keys, seed phrases, API keys, other passwords) was found anywhere in the repository's full git history. No private key for `speclock-provider` or any other account was ever written to a file in this repository at any point — only the one password string, for a throwaway testnet-only account.

## What was NOT independently security-tested

- No fuzzing/property-based testing was run (no `hypothesis` strategies written, though the `hypothesis` plugin is present in the test environment).
- No adversarial multi-validator consensus attack (forged leader vs. honest validators) was exercised — Direct Mode cannot run it (see `docs/CONSENSUS.md`).
- No static analysis beyond `genvm-lint check`/`validate` (0 errors, 0 warnings) was run.
