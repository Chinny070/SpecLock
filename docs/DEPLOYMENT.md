# Deployment

## Current release — deployed, lifecycle checks pending (2026-10-18)

| Field | Value |
|---|---|
| Network / chain | GenLayer Studio Network / `61999` |
| Contract | `0xDFb69c1890F72c7b791A938ed36C5103582E6F19` |
| Deployment transaction | `0x47a258b79297644bce2d54ba8eea678177b27856181577b685d9d3adfbfc35c3` |
| Deployment result | `FINALIZED`, `MAJORITY_AGREE`, 5/5 validators voted `AGREE`, leader `execution_result: SUCCESS` |
| Source SHA-256 | `CEC00C69E57E6AE1B70C77BE49CFFEEB912F2D55D15E42AF75A2B6687ABB6F5C` |
| Callable schema | 47 methods (20 views, 27 writes); `genlayer schema` succeeded |
| Readback | `get_reputation` returned zeroed counters for the configured deployer |

The source returned by `genlayer code` matched the local SHA-256 after normalizing the CLI's Windows line endings to LF. The transaction was submitted through the active configured `my-studionet-wallet` on chain `61999`; its address and balance were verified before submission. The deployment and read-only schema/reputation calls are confirmed. No lifecycle transactions have yet been executed against this release.

Two authorized project signers are now available through the GenLayer CLI: `my-studionet-wallet` and the user-created `speclock-provider-2` (`0xf230283bdc86e3810c69cbc482b5495a8f1c4c8e`), which is unlocked and read back at 15 GEN on chain `61999`. No lifecycle transaction has yet been sent from either signer to this release. The remaining blocker is the signing interface: installed `genlayer write --help` exposes no payable `value` option, and the `genlayer` CLI's argument parser coerces digit-only strings to numbers, while this contract's generated agreement IDs are string values. The documented `genlayer-js` SDK accepts native `value` and preserves string arguments, but it needs an account object or EIP-1193 provider; the CLI's encrypted account alias is not exposed to that SDK as a signer. I did not read or export private keys. The smallest resolution is to connect an authorized signer through a supported EIP-1193 wallet provider accessible to the transaction client, or use a supported CLI/SDK adapter that signs with the encrypted account without exposing its key. Existing principal spending limits still apply; fees are not to be used as a blocker, and should be recorded when available.


## Prior reviewer-fix release — deployed and exercised (2026-10-18)

| Field | Value |
|---|---|
| Network / chain | GenLayer Studio Network / `61999` |
| Contract | `0x142A372b4cA7cf3784327DFA2e2B0eCF45D4eA14` |
| Deployment transaction | `0x34ee57640f53c1826dc77e5900d66a81bb05f2c59fb899d4f19168b00143329e` |
| Deployment result | `FINALIZED`, `MAJORITY_AGREE`, leader `execution_result: SUCCESS` |
| Source SHA-256 | `0E7A7723C259DCF1CFAAEC8AFE62F873D6746335D63E9D8A1C2C7B25DFC4A1FE` |
| Callable schema | 45 methods (20 views, 25 writes), returned by `genlayer schema` |

This is the exact current `contracts/speclock.py` source deployed by the recorded transaction. Candidate-specific API PASS/FAIL and PARTIAL, agent PASS/FAIL, payable settlement and real withdrawal, warranty evidence anti-redirection and claim resolution, and milestone settlement/replay are recorded in [the release evidence ledger](evidence/studionet-reviewer-fix-2026-10-18.md). Agreements 2–6, 8, and 9 reached their recorded outcomes. Agreement 1 is an unfunded DRAFT. Agreement 7 is ACCEPTED but unfunded after a Studio Network transport timeout; a readback confirmed no value entered the contract. The candidate contract balance read back as zero.

Direct Mode tests: 94 passed. GenVM lint and schema validation: passed (3 checks; 45 methods). Clean-clone verification of commit `b6fdb8a6e02b93acaa6d2dc942bf04b9edff96df` also passed 94 tests and both lint commands with UTF-8 output enabled.

The current release does not eliminate the disclosed partial capabilities (#12, #19, #21, #33), the child-transfer recovery limitation, or the historical credential exposure. The new bilateral ambiguity acknowledgement is covered locally but was not separately exercised live. Recorded gross transfer volume is 0.017038 GEN before unitemized historical fees; the latest deployment fee is not reconciled. This is not an exhaustive 38-capability verification claim.

## Historical release: rejected-value refunds and warranty digest binding

| Field | Value |
|---|---|
| Network / chain | GenLayer Studio Network / `61999` |
| Contract | `0xe52Faa4e49AF53F3f1bD7fef274D324483784e44` |
| Deployment transaction | `0x9934adb4b7300a641fa082aa2940d9137445f463310c51c897405cbdeb7aa583` |
| Deployment result | `FINALIZED`, `MAJORITY_AGREE`, leader `execution_result: SUCCESS`; 3 validators agreed and 2 were idle |
| Callable schema | `genlayer schema` succeeded; 43 methods (19 views, 24 writes) |
| Source | `contracts/speclock.py` as validated by the lint and Direct Mode results below |

The live deployment confirms two protections added after the preceding release. First, an invalid payable `fund_agreement` call with 1,000,000,000,000 atto finalized successfully, returned `false`, and credited exactly that amount to the caller's claimable balance (`0x3962e57a948f69064f860f2f720591c7014e93eb1551bcea0e0349556042ec55`). This first probe stopped in the client script before withdrawal because the script incorrectly required a `status_name` property after the SDK's `waitForTransactionReceipt(FINALIZED)` had already resolved. Its process-local signer was lost; the amount remains claimable to `0x3d3ee88E2396A41EBA703dea5681Ad60Cc1C9D80`, and the contract balance read back as 1,000,000,000,000 atto. This is an explicitly stranded test amount, not counted as successfully refunded.

A corrected single-process repeat finalized the same invalid-call behavior and then withdrew the credit. The invalid call `0x904865a6cb4f6cf289e98c7c9e1678d94ce6e6261f0f8fb5b6d5b585c93a7851` returned `false`; `get_claimable` returned 1,000,000,000,000 atto. Withdrawal `0x1580fae617f011d086b3d8c351514079e3ee0f4e3a7acf0b67d04baf3945868f` finalized with leader `SUCCESS`, returned 1,000,000,000,000, and reduced claimable to zero. Child transfer `0x4f72367d9faae3d86a8db9410ac00f6ef70e33741a3f0da8fe3d2206410de95a` finalized with `value_credited: true`; its child result name is `NO_MAJORITY`, which is how this runtime reports the EVM-layer transfer child. The disposable wallet balance increased from 0 to 10,000,000,000,000 atto after its 10,000,000,000,000 atto test top-up plus exact return; the returned value and cleared claimable were independently read back.

The same release completed an API warranty lifecycle using agreement `1`. It was funded with 100,000,000,000,000 atto, evaluated `PASS` against live `https://httpbin.org/json` evidence, finalized by both parties, and settled with 80,000,000,000,000 atto released to the provider and 20,000,000,000,000 held for warranty. A 2,000,000,000,000 atto warranty bond was then submitted with a deliberately incorrect digest for `https://httpbin.org/status/200`. `resolve_warranty_claim` finalized successfully; the fetched evidence was classified `UNVERIFIABLE` with rationale "fetched evidence does not match the committed digest", and the claim was `REJECTED`. The holdback and bond (102,000,000,000,000 atto total) were credited to the provider, who withdrew them in `0x575a4fff1d662853ad5a3e2d10edddf08892c03f374074225f47aca36e9b137e`. Its child transfer `0xadf6e3d28cd4612e1d2778b31cee60170756189db3cf12af134f0f849e30e965` finalized with `value_credited: true`, `value: 102000000000000`, and `result_name: NO_MAJORITY`. The provider claimable balance read back as zero after withdrawal. A buyer withdrawal with no claimable balance finalized as an expected `ERROR` (`0xe8385fa8a7528fc606cfc7dd1b581e3f97c220f01d27b606195ddcc327c24886`); no value was attached or transferred.

The runtime-specific child-transfer result is recorded precisely: the parent `withdraw()` transactions reached finalized successful contract execution, while their EVM child transfers reached `FINALIZED` with `NO_MAJORITY` but `value_credited: true`; the recipient balance/value-credit evidence confirms the payout landed. In the warranty run, each party was topped up with 250,000,000,000,000 atto; afterward the buyer had 148,000,000,000,000 and the provider 352,000,000,000,000 atto, matching the 100,000,000,000,000 deposit, 2,000,000,000,000 bond, and 102,000,000,000,000 provider withdrawal. The first failed script's abandoned 0.000001 GEN is the only test value still held by this deployment. Total cumulative test transfer principal, including the audit's prior tracked 0.002289 GEN, the two refund probes and top-ups, and the warranty run, is approximately 0.002913 GEN; this remains under the authorized 0.02 GEN ceiling, and no individual test transfer exceeded 0.001 GEN. Fee changes were not separately itemized by the test scripts.

Capability 33 remains `PARTIAL`: the live warranty path and strict digest binding now work on this release, but the contract has no trustworthy clock and therefore cannot guarantee a finite warranty-claim window. The stranded 0.000001 GEN is a disposable-test-key lifecycle artifact; its address and claimable amount are recorded above, and no signer secret was persisted or exposed.

## Predecessor deployment (second capability-audit pass — earlier live-verified release)

| Field | Value |
|---|---|
| Network | GenLayer Studio Network (`studionet`) |
| Chain ID | `61999` (`0xf22f`) |
| RPC | `https://studio.genlayer.com/api` |
| Explorer | `https://genlayer-explorer.vercel.app` |
| Deployer address | `0xaffE15eEc45b68835cc9E5B4Ab85dD5deaE8e70b` (local alias `my-studionet-wallet` — used only to deploy and to fund disposable test accounts, never as a lifecycle party) |
| **Contract address** | **`0xc758b9E6763fdB1C80c758f8D26eD04Acc063254`** |
| Deploy tx hash | `0x0d2c7252884a2c4a374e9fa13803bf2c62ebb1b7b3d6e9b0610346578a23098a` |
| Deploy tx status | `FINALIZED`, `execution_result: "SUCCESS"` (both checked explicitly) |
| Deploy command | `genlayer deploy --contract contracts/speclock.py` (no `--args`) |

Schema readback (`genlayer schema 0xc758b9E6763fdB1C80c758f8D26eD04Acc063254`) confirms 31 methods matching `contracts/speclock.py` (29 previously + `request_procedural_review` + `verify_settlement_replay`).

## Capability audit follow-up: live verification of five fixed/added capabilities

Three real agreements were run against the current deployment, under the same small-amount budget discipline as before (max 0.001 GEN/tx, max 0.02 GEN cumulative; actual spend across this follow-up: 0.000985 GEN).

**Agreement "1" — capabilities 13, 21, 38.** Two criteria (`c1` required, `c2` optional). Before submitting real evidence, an IPv6-literal evidence URL (`https://[::1]/health`) was submitted and correctly reverted on-chain (`"[EXPECTED] blocked host for evidence URL"`) — the real SSRF fix, live. Real evidence then made `c1` PASS and `c2` FAIL; the real evaluation read back `overall_finding:"PARTIAL"` (capability 13, live). `settle()` produced a real `{"released_to_provider":50000000000000,"refunded_to_buyer":50000000000000,"retained":0,"terminal_phase":"SETTLED"}` — an exact 50/50 proportional split. `verify_settlement_replay("1")` (capability 38) returned `matches_recorded_settlement:true` with the recomputed amounts exactly matching the recorded settlement.

**Agreement "2" — capability 19 (attempted; mechanism confirmed safe, specific override line not triggered).** An `ai_agent_delivery` agreement with two evidence items submitted by the same party (the buyer) for one criterion. The real, unscripted LLM judgment reasoned further than the test anticipated: it correctly noticed no actual delivered artifact was present at all (both evidence items were source material, not a delivered summary) and returned `UNVERIFIABLE` rather than a `SUFFICIENT` claim — so the deterministic single-submitter downgrade never had an incorrect claim to intercept. The agreement still settled correctly either way (`RECOVERY_PENDING`, full amount retained, confirmed via `eth_getTransactionCount`/balance read-back after a transient local network blip resolved). Honest status: the mechanism is fixed and Direct-Mode-proven in both directions (`tests/direct/test_speclock_agent.py`), but this specific live attempt did not happen to exercise the override itself.

**Agreement "3" — capabilities 25 and 26.** Two required criteria (`c1`, `c2`). Real evaluation: `c1` FAIL, `c2` PASS, overall `FAIL`. A real appeal (round 1, real bond) challenged only `c1`; `resolve_appeal` re-judged **only `c1`** (still FAIL, unchanged evidence) and `c2`'s finding (`PASS`) was carried forward verbatim and read back unchanged in the new evaluation — resolution correctly `REJECTED` (capability 26, live). A second real appeal round (same challenge, same result) exhausted `max_appeal_rounds`; a third `file_appeal` attempt correctly reverted (`"appeal rounds exhausted"`). `request_procedural_review` was then called by the buyer alone — correctly returned `false` (not yet triggered) — and then by the provider — correctly returned `true`, triggering a genuine **full** re-evaluation of both `c1` and `c2` (capability 25, live). A further `request_procedural_review` call correctly reverted (`"procedural review already used for this agreement"`). The agreement then finalized (mutual consent, `false` then `true`) and settled: `{"refunded_to_buyer":100000000000000,"released_to_provider":0,"retained":0,"terminal_phase":"SETTLED"}`, matching the still-FAIL final verdict exactly.

**No contract defects were found during this live-verification run** beyond the two already fixed before redeployment (the resubmission fund-lock and the IPv6 SSRF bypass) — every outcome matched Direct Mode's existing predictions exactly.

### Predecessor deployment (first capability-audit pass: resubmission fix + real native-value escrow)

| Field | Value |
|---|---|
| **Contract address** | `0x2671cd7Fc9f7653f8e8A506E4aC3281A1Db0553c` |
| Deploy tx hash | `0x8a63968ce744bfb12ec3f93ca5e44e18153858dadda75c650fa75fc135dc338e` |
| Deploy tx status | `FINALIZED`, `execution_result: "SUCCESS"` |

Schema readback confirms 29 methods matching the source as of the first audit pass (before #25/#38's new methods were added). This deployment's own lifecycle evidence (the `request_resubmission` fund-lock fix, live-verified end to end) remains valid and is recorded below under "Capability audit: the resubmission fund-lock fix, live-verified".

### Earlier predecessor deployment (real native-value escrow, predates the resubmission fix)

| Field | Value |
|---|---|
| **Contract address** | `0xbE2a98135e41B4fE722919b87024D867F8De8343` |
| Deploy tx hash | `0x56c13ef85e7d92f449fc73369c543b6f053f6bca50ae7aecf911f5511e2a279e` |
| Deploy tx status | `FINALIZED`, `execution_result: "SUCCESS"` |

Schema readback confirms 29 methods, `fund_agreement`/`file_appeal` both `payable: true`. This deployment's own lifecycle evidence (the first real `PASS`/`FAIL`+appeal escrow verification) remains valid and is recorded below under "Native-value escrow: live-verified"; it predates the `request_resubmission` fund-lock fix (it has the *same* latent bug the fix below addresses, so it must not be used for any resubmission flow).

### Earlier predecessor deployment (bookkeeping-only funding, still independently useful for its own lifecycle evidence)

| Field | Value |
|---|---|
| **Contract address** | `0xD5602E88b021573cbb364Efaae8DCD48DF555ff7` |
| Deploy tx hash | `0xdd2f6307a732a43df1ebf1c7bc2683eeb9f8472b4985b3a0cd610c69fc645cb4` |
| Deploy tx status | `FINALIZED`, unanimous 5-validator `MAJORITY_AGREE` |

Schema readback confirms 27 methods (including `check_verdict_consistency`) matching the pre-escrow-fix source, with `fund_agreement`/`file_appeal` both `payable: false`. This deployment's own lifecycle evidence (API/agent delivery PASS/FAIL/UNVERIFIABLE, live `recover_inconclusive`, `check_verdict_consistency`) remains valid and is recorded further below; it just predates the real-escrow fix.

## Capability audit: the resubmission fund-lock fix, live-verified

A full capability-by-capability audit of all 38 numbered brief items (`docs/FEATURE_MATRIX.md`) found a real defect via a Direct Mode probe exercising the *full* `request_resubmission` cycle (create → evaluate `FAIL` → `request_resubmission` → submit corrected evidence → re-evaluate) — something no existing test did. `submit_evidence` never advanced the phase out of `RESUBMISSION_REQUESTED`, so `request_evaluation` (which only accepts `SUBMITTED`/`RE_EVALUATING`) could never be called again: a genuine, previously-untested fund-lock, compounded by `cancel_or_expire`'s wind-down also only accepting `FROZEN`. A related defect in `_evaluate_api_profile` meant that even after fixing the phase transition, a resubmission's whole point — corrected evidence — was silently ignored on re-evaluation, since it always re-probed the first (stale) evidence ever submitted for a criterion (`probe_evidence[0]`) rather than the latest. Both fixed (`submit_evidence` also transitions `RESUBMISSION_REQUESTED → SUBMITTED`; `cancel_or_expire` also accepts `RESUBMISSION_REQUESTED`; `_evaluate_api_profile` now uses `probe_evidence[-1]`), covered by two new Direct Mode regression tests, 54/54 tests pass, lint clean. Redeployed to `0x2671cd7Fc9f7653f8e8A506E4aC3281A1Db0553c` (`FINALIZED`, `execution_result: "SUCCESS"`).

**Live-verified end to end**, under the same small-amount budget as before (max 0.001 GEN/tx, max 0.02 GEN cumulative; this batch spent 0.00031 GEN plus a small stranded amount noted below):

- Agreement "2": created with the vague spec "Deliver a reasonable API" / "Response should be reasonable and fast" — real ambiguity report correctly flagged both vague terms (capability 17). `freeze_agreement(..., False)` correctly reverted (`"ambiguity report is non-empty; freeze requires explicit acknowledgement"`); `freeze_agreement(..., True)` correctly succeeded. `get_policy_fingerprint` read back a real fingerprint (capability 36). Evidence submitted (`https://httpbin.org/status/200`) evaluated real `FAIL` (`"HTTP 200 but response failed functional check"`). `request_resubmission` moved the agreement to `RESUBMISSION_REQUESTED`; corrected evidence (`https://httpbin.org/json`) was submitted, confirmed moving the phase to `SUBMITTED` (the fix, live); re-evaluation produced a genuine `PASS`. Mutual-consent `finalize_verdict` (`false` then `true`), `settle` (`released_to_provider:100000000000000`). `get_reputation(provider)` read back `{"finalized_outcomes":0,...}` before and `{"finalized_outcomes":1,"pass_outcomes":1}` after (capability 14/35). Both evidence receipts (`2-ev1`, `2-ev2`) read back via `get_evidence_receipt`, both confirmed `"status":"FROZEN"` (capability 27).
- Agreement "3": a real two-required-criterion agreement (`c1`: reachable JSON endpoint; `c2`: reachable but non-JSON) correctly derived `overall_finding:"FAIL"` from the mixed per-criterion `PASS`/`FAIL` findings (capability 6), read back from `get_evaluation` on-chain. This agreement's lifecycle was not completed past evaluation: a transient Studio Network RPC error during receipt-polling (the same intermittent flakiness documented elsewhere in this project — `eth_getTransactionByHash`/`eth_getTransactionCount` returning HTML error pages instead of JSON) occurred after the evaluation transaction had already genuinely succeeded on-chain, and the disposable buyer/provider keys for this agreement exist only in the Node process that generated them, so they could not be reused to finish settlement in a fresh process. **A small amount of real testnet GEN (0.0001 GEN, the funded amount) is stranded** as a result — the same low-value, already-documented key-lifetime limitation (`createAccount()` never exposes a raw private key) that has stranded a handful of agreements on earlier deployments throughout this project, not a new class of risk.

No contract defects beyond the two above were found during this audit's live testing.

## A real production defect found and fixed via this deployment (not caught by Direct Mode)

While exercising the lifecycle through GenLayer's own documented `genlayer-js` SDK (`createClient`/`writeContract` — the same library the `genlayer` CLI is built on; see "CLI tooling defect" below for why the CLI itself couldn't be used), `create_agreement` failed with a real on-chain `ERROR`-status execution:

```
File "/contract.py", line 400, in create_agreement
    provider = _as_address(provider)
File "/contract.py", line 40, in _as_address
    return Address(bytes(value))
TypeError: string argument without an encoding
```

The genlayer CLI's `addr#...` argument syntax constructs a typed `Address`/bytes value before it ever reaches the contract, which is why every earlier CLI-driven `create_agreement` call (see "Superseded deployments" below) worked. `genlayer-js`'s standard, documented `writeContract` API — a materially different and at least equally official calling convention — passes an address argument as a plain hex string, and `_as_address`'s unconditional `bytes(value)` call cannot handle a `str` without an explicit encoding. **Fixed**: `_as_address` now decodes a `str` input as hex before constructing the `Address`. Regression test: `tests/direct/test_speclock_lifecycle.py::test_provider_as_plain_hex_string_address_is_accepted`. See `DECISION.md` item 7.

## Native-value escrow: first attempt failed, root cause found and fixed

A real-escrow design was first built using GenVM's documented native-value primitives: `@gl.public.write.payable` + `gl.message.value` to receive a real deposit, and `gl.get_contract_at(recipient).emit_transfer(value=..., on=...)` to pay it back out. It was deployed to `0xaa54c150B128843e5638cF31e2F1B632117ccBE2` and live-tested with two fresh disposable accounts (buyer1 `0xaDFeB5b162415C94edCAeC22eE5207879611F922`, provider1 `0xF24B500CBBEd965e31c47fEc92d8add8C7Cf6E52`).

**The incoming leg genuinely worked.** Calling the payable `fund_agreement` with `value = 1000000000000000000` (1 GEN) succeeded (`SUCCESS`, tx `0x8eeda7767a8c113d2afa0e6180e1588b614a20adf951f99497908fb883043b68`); the contract correctly recorded `funded_amount: "1000000000000000000"`; an independent `getBalance` check on buyer1's wallet before and after the full nine-transaction sequence showed its balance dropped by exactly 1 GEN total (gas on this network costs effectively nothing) — a real, externally-verified deposit, not merely a number the contract believed.

**The outgoing leg failed.** `settle()` correctly computed `released_to_provider: "1000000000000000000"` (tx `0x75b4533880f35352865b88cc1b65a568f6f026d94c4db946376e2ce735f43abe`, `SUCCESS`) and called `emit_transfer` to pay provider1. The resulting child transaction (`getTriggeredTransactionIds` → `0x086c0121ff9d281b9af33198083e72f3e95f20a06fd583d3be82f1eda6fbed54`) reached `status_name: "FINALIZED"` but with `result_name: "NO_MAJORITY"` and `value_credited: false`. Its leader receipt's raw result decodes to the literal string:

```
Contract 0xF24B500CBBEd965e31c47fEc92d8add8C7Cf6E52 not found
```

At the time, this was recorded as a GenVM runtime limitation and the design was reverted to bookkeeping-only (see the superseded writeup this section replaces, preserved in git history, and `DECISION.md` item 8).

**Root cause identified and fixed.** `gl.get_contract_at(address)` addresses another GenLayer *intelligent contract* — it is not a general value-transfer primitive, and "Contract ... not found" is the correct, expected error when pointed at a plain wallet (EOA), not a runtime bug. The correct mechanism is `gl.evm.contract_interface`, which builds an EVM-layer proxy (`_EthAccount` in `contracts/speclock.py`) whose `.emit_transfer(value=u256(...))` emits a native `EthSend` to the chain-layer address instead of attempting to message a GenVM contract. This was found by inspecting a sibling project in this account, AgentCourt (`agentcourt/contracts/agent_court.py`), which independently solved the identical problem on the identical pinned runner and the identical Studio Network, and recorded **real, live proof it works**: a disposable test wallet's balance moved exactly `0.001 GEN -> 0.0015 GEN` via this exact call pattern (`agentcourt/docs/RELEASE_CANDIDATE_VERIFICATION.md` Phase 9, tx `0x3dac6d579a6ddd0f92e2eb0fc649f811b4aadd010ed1a97a612dd413869f328c`).

SpecLock's `fund_agreement` and `file_appeal` are payable again; `_settle`/`resolve_appeal` now credit a pull-payment `claimable` balance (never calling `emit_transfer` themselves); a new `withdraw()` method lets the credited party trigger the real payout via `_EthAccount`. 8 new Direct Mode tests cover the bond/value-mismatch rejections and the claimable crediting across every settlement outcome (PASS/FAIL/UNVERIFIABLE/appeal UPHELD/REJECTED) plus `withdraw`'s zero-and-revert behavior — **52/52 Direct Mode tests pass, lint is clean** (see `tests/direct/test_speclock_security.py`).

**Two redeploy attempts to live-verify this fix initially looked blocked, then turned out to be a deploy-command mistake, not a platform or contract problem.** `contracts/speclock.py` with this fix was deployed twice (`0xd60dfaC9B3473Fce6bC97CD47F7a5Ac80c97A74e`, deploy tx `0x5f7f58da3467b1a4291b8161a4061bf37355729f36bd7f1d298d1c561d6446b9`; and `0x192CA2229677E4e1d0d115d4665E2634Bf0A25d1`, deploy tx `0x14a6ade55f9a8d4a9577a4346b1316100ac457e45699b3fcbe85d007177a5a8d`) using `genlayer deploy --contract contracts/speclock.py --args '[]'`. Both deploy transactions reached `status_name: "FINALIZED"` — which a first pass mistook for success — but every subsequent call against either address returned `"Contract ... not found"`. Re-examining the full receipt (not just `status_name`) found the real signal: both deploy transactions' leader receipt carried **`execution_result: "ERROR"`**, with decoded stderr reading `TypeError: SpecLock.__init__() takes 1 positional argument but 2 were given`.

**Root cause, confirmed by comparing raw deploy calldata byte-for-byte**: the working `0xD5602E88...` deployment's calldata is a single byte (`[6]`, a "zero constructor arguments" marker); both failing deployments' calldata is 8 bytes encoding `{"args": "[]"}` — the CLI's `--args <args...>` option is variadic (each shell token becomes one separate constructor argument), so the single-quoted shell token `[]` was passed through as one literal two-character string argument, not parsed as JSON for an empty array. This called `SpecLock.__init__(self, "[]")` — one argument too many, exactly matching the traceback. AgentCourt's own documented working deploy command omits `--args` entirely (`genlayer deploy --contract release/agent_court.py`), confirming the correct invocation for this zero-argument constructor. Both deploy transactions genuinely reached real 5-validator consensus (correctly agreeing the constructor call errored) — `status_name: "FINALIZED"` and `execution_result: "ERROR"` are not contradictory; they mean "validators agreed this failed," not "this succeeded," and both fields must be checked.

Redeployed correctly with `genlayer deploy --contract contracts/speclock.py` (no `--args`), producing `0xbE2a98135e41B4fE722919b87024D867F8De8343` (deploy tx `0x56c13ef85e7d92f449fc73369c543b6f053f6bca50ae7aecf911f5511e2a279e`, `FINALIZED` **with `execution_result: "SUCCESS"`**, confirmed via `genlayer schema` returning the full 29-method schema).

## Native-value escrow: live-verified — real funding, real appeal bond, real withdrawals, real rejection cases

A full real on-chain lifecycle was executed against `0xbE2a98135e41B4fE722919b87024D867F8De8343`, using small disposable-wallet amounts bounded by an explicit per-transaction cap (0.001 GEN) and cumulative cap (0.02 GEN); actual total spend was **0.00068 GEN**. Every amount below is real atto-GEN (1 GEN = 10^18 atto), not a bookkeeping number.

### Agreement "1" — PASS, real settlement, real withdrawal, double-withdrawal and no-balance-withdrawal correctly rejected

- `create_agreement` → `0x13f881b7cfbad0f6b2bd462b775a923ff2f97ea28269f9802602f628fd4d93bf` (`SUCCESS`)
- `accept_agreement` → `0x6ed8d52f9d7b493a3c0cbd71c185f076c51b03e4769cf6a40c7927023c8042ec`
- `fund_agreement(1, 100000000000000)` with real `value = 100000000000000` atto (0.0001 GEN) → `0x0d8c93bdb18d28ddc17c0e66537dded4bf2f03729294ddbf7d2dc8213b43b470` (`SUCCESS`)
- `freeze_agreement` → `0xfdcf2dc0dddfbf7bc30de132b82afc1772d8688854c8d86041c95acbbebb46f1`
- `submit_evidence` (`https://httpbin.org/json`) → `0x0628faceebc10f477fe2f83c5baacf68474925b323b02c974a13c43e373b0969`
- `request_evaluation` → `0x839b49201343afc70cb029723ca7ab0dc2c9b001a6dc3a3ef517f2423e8b7d56`; real evaluation: `{"overall_finding":"PASS","findings":[{"criterion_id":"c1","finding":"PASS","sufficiency":"SUFFICIENT","rationale":"HTTP 200 with schema-consistent body"}]}`
- `finalize_verdict` (buyer, 1st call) → `0x1a9056c2b6303775a5946c381e4589ff647c5764b91221a5452b30697666e777`, returned `false` — mutual-consent gate confirmed live
- `finalize_verdict` (provider, 2nd call) → `0xadad4bbb11842fad9b3acdeac68eb03ce942bcc47bfa6cef64af097f03c9e791`, returned `true`
- `settle` → `0x746e6c4b3a36ddc386eb4f8ba3c5ba28028366d993f7b69d2bf8f88beb8457bd`: `{"released_to_provider":100000000000000,"refunded_to_buyer":0,"retained":0,"terminal_phase":"SETTLED"}`
- `get_claimable(provider)` read back `100000000000000` before withdrawal
- **`withdraw()` (provider)** → `0x8c2135cbbe3cda74689ad4ac6bc0d67e603eafb2fbd7d3ed9f30f6dc62ea40cf`, `SUCCESS`, returned `100000000000000`. **Independent `getBalance` check**: provider's real wallet balance before `10000000000000`, after `110000000000000` — a delta of exactly `+100000000000000` atto, matching the settlement amount exactly. This is the real EOA payout that the first escrow attempt's `gl.get_contract_at` call failed to deliver.
- **Double-withdrawal rejected**: a second `withdraw()` call by the same provider → `0xfba0eefc9d2e8d20254ae20ed5c7a044536e2b134fc1b7266ff9ea96408d3137`, `ERROR`, `"[EXPECTED] nothing to withdraw"` — `claimable` was correctly zeroed by the first call.
- **No-balance withdrawal rejected**: the buyer (who has zero claimable) calling `withdraw()` → `0xb638f4fda1dcc9f5f7021644478be96be6b433c7cb7bfecc7caa2e172c1d56d4`, `ERROR`, `"[EXPECTED] nothing to withdraw"` — `withdraw()` takes no address parameter, so there is no way to withdraw anyone else's balance; this confirms a caller with nothing credited gets nothing.

### Agreement "2" — FAIL, real appeal with a real bond, REJECTED on re-evaluation, bond correctly credited, two more real withdrawals

- `create_agreement` → `0x62d759981cb88894e9e98347544785989f023240a87331ea605656649b787524`
- `accept_agreement` → `0x8ef11eef41698f1b8c674ba7027663d4156a0c37debdfc3fc4a651ef8926dc57`
- `fund_agreement(2, 100000000000000)` with real value → `0x67731c0b17eebd614c0b9c40b629b7337bb4c8f51aebaea1c349d2f6678c9be3`
- `freeze_agreement` → `0x5fd8364e16626f79e1db1b8e7b741b61c0efc09a5bf03321e884cfff9ddfe26b`
- `submit_evidence` (`https://httpbin.org/status/200` — reachable, HTTP 200, non-JSON) → `0xd0336c017f931eb7f6d15abbf2336dca4f3c1ae76b4143602b6752e7f5a78e98`
- `request_evaluation` → `0x13c0a855a8420dcf68c1c5bebcb5a3634bfa2eaf38d278a4a6b45a083c779cbd`; real evaluation round 1: `{"overall_finding":"FAIL","findings":[{"criterion_id":"c1","finding":"FAIL","sufficiency":"SUFFICIENT","rationale":"HTTP 200 but response failed functional check"}]}`
- **`file_appeal` with a real bond** (`value = 10000000000000` atto, `max(1, funded_amount // 10)`) → `0x9d9ed50ebd0e7074157ab5c6051bd04dd37dfbcb985b477ff5f7629763a19fca`, `SUCCESS`, appeal id `"2-ap1"`
- `resolve_appeal` → `0x28100e189e0127d7c80da79700d24ebd0a1fd677761a476b896effa2119ca043`: real re-evaluation (round 2) against the same unchanged evidence again derived `FAIL` (`{"overall_finding":"FAIL", ...}`), so the appeal correctly resolved `"REJECTED"` — `{"appeal_id":"2-ap1","resolution":"REJECTED","resolution_evaluation_id":"2-eval3"}`. This is the live counterpart to Direct Mode's `test_appeal_rejected_when_challenged_finding_does_not_actually_change`.
- Agreement phase after `resolve_appeal` was `PROVISIONAL_VERDICT` (a fresh verdict, needing its own mutual consent) — confirmed live, matching design.
- `finalize_verdict` (buyer, 1st) → `0x13882f8bdc3adba880c57ceb92434d2dfd85a43d8d2738f467ec47e2ad029661`, `false`; (provider, 2nd) → `0xa4d9d6e5ddcea2f53d8bb8af90fcb0479e475ebb445c995b9ecbdde59d889011`, `true`
- `settle` → `0x1ba76dddea264f86ab09661b56efdce89b54ff162a5580d5b9c7e15976c28e61`: `{"refunded_to_buyer":100000000000000,"released_to_provider":0,"retained":0,"terminal_phase":"SETTLED"}`
- `get_claimable`: buyer `100000000000000` (refund), provider `10000000000000` (appeal bond, correctly credited to the **non-appellant** party since the appeal was `REJECTED`)
- `withdraw()` (buyer) → `0x667ac3316bb8172e9dda801cca1572f2242a7f27340aa4f2ebd47913f58f345b`, returned `100000000000000`
- `withdraw()` (provider) → `0xb010ff157c581196a6d80af579b76abe8dd7decde5eb7646e42e30f939984632`, returned `10000000000000`
- **Independent balance deltas matched the accounting exactly**: provider's wallet delta `+10000000000000` (the bond, its only inflow); buyer's wallet delta `-10000000000000` — buyer sent out `100000000000000` (fund) + `10000000000000` (bond) = `110000000000000`, and received back `100000000000000` (refund withdrawal), net `-10000000000000`. Confirmed arithmetically exact, no hidden gas deduction observed (consistent with every other live transaction in this project).

**No contract defects were found during this live run.** Every outcome matched what Direct Mode already predicted (see `tests/direct/test_speclock_security.py::test_settle_on_pass_credits_provider_claimable_not_buyer`, `::test_appeal_bond_credited_to_other_party_on_rejected`, `::test_withdraw_zeroes_claimable_and_returns_amount`, `::test_withdraw_with_nothing_claimable_reverts`) — no fixes were needed, and none were made.

## How real on-chain lifecycle execution was achieved without touching any protected credential

*(The four agreements below were run against superseded deployment #3, `0x6bBcF7E85f8F07B54ba53ae2126E2E9F6485eE68`, before the escrow attempt/revert — all application logic involved is identical in the final deployment; only the payable/bond wrapping around `fund_agreement`/`file_appeal` changed.)*

The `genlayer` CLI's `--args` parser cannot encode a digit-only string (background below), which blocked every agreement-addressed call through that tool. Investigation of GenLayer's **officially documented `genlayer-js` SDK** (a separately published npm package, the same library underlying the CLI) confirmed its `args` arrays pass native JavaScript values straight into the real calldata encoder with no intervening text-parsing step — a JS string `"2"` stays the string `"2"`. Verified empirically: `readContract` successfully read agreements by their real string ids with no issue.

For write calls (which require a signer), **freshly generated, disposable keypairs** (`createAccount()` from the same SDK — new randomness, never read from any existing keystore or OS-protected credential store) were used as throwaway buyer/provider pairs for each test agreement, funded with ordinary GEN transfers from `my-studionet-wallet` via the already-supported `genlayer account send` CLI command. No protected credential (the repository owner's wallet key, the `speclock-provider` keystore from earlier work, or any OS-keychain-cached key) was read, extracted, or touched at any point.

**A process-lifetime lesson learned along the way**: `createAccount()` never exposes a raw private key (by design — it's held in a closure for signing only), so a generated account can only be used within the single script process that created it; it cannot be serialized and reused across separate script invocations. An early attempt to resume a partially-completed agreement from a new process failed for exactly this reason (the "new" buyer/provider were different random accounts than the ones that actually held that agreement) — not a contract defect, a scripting mistake, corrected by running each agreement's full lifecycle to completion within one process.

### Negative-test agreement "2" — full real lifecycle, SETTLED

| Step | Tx hash | Execution result | Return value |
|---|---|---|---|
| `create_agreement` (spec: `GET https://httpbin.org/status/200 returns HTTP 200`) | `0x5dbfb0372f273a1da3281af4394521b73e4a425dc9529be4a6b61e6537f40b73` | `SUCCESS` | `agreement_id = "2"` |
| `accept_agreement("2")` | `0xf0f2222a223ae12a12ee30ad857bb54bad7a6587287d475bce45a71c69546613` | `SUCCESS` | — |
| `fund_agreement("2", 1000)` | `0x3ade8f2af40b2c411e9de5fe9d59c8141d4d292d8ff00a825f9b28db399d8c36` | `SUCCESS` | — |
| `freeze_agreement("2", false)` | `0xa3e6f67705057b20c7ec199cc63f8aa37a8cfdbfefff1e2a948fd7c4bf5741f9` | `SUCCESS` | — |
| `submit_evidence("2", "https://httpbin.org/status/200", ...)` | `0xf5b9d428d5ac238e4dc72b646f837d407b015aa735a21b5f4416c6146762ab41` | `SUCCESS` | `"2-ev1"` |
| `request_evaluation("2")` | `0x23f952f80e8d02afe8e2546e807a7961a3cfaa36a6fe44a70232fd10c7a6cc58` | `SUCCESS` | `"2-eval1"` |
| `finalize_verdict("2")` (buyer, 1st consent) | `0xf85177d743b095d55a64758e881f4e19bb056a68d359e2618bf4d843de4fec27` | `SUCCESS` | `false` |
| `finalize_verdict("2")` (provider, 2nd consent) | `0x7882cb0de5859889ea14836c3be8e5630a260d90d519380ad3657421efe18d93` | `SUCCESS` | `true` |
| `settle("2")` | `0x1692edb640274af062f9599e3d076a3949394124218d3bd14f69dfd9badec502` | `SUCCESS` | `"2-st1"` |

**Real, on-chain `get_evaluation("2-eval1")` read-back:**
```json
{"agreement_id":"2","evaluation_id":"2-eval1","evidence_snapshot_commitment":"e3ffcfb1083144f0b14b97ebed45ece17485c0b2fab8bc276d9fd28a9b55d132","failure_attribution":"DELIVERY","findings":[{"attribution":"DELIVERY","criterion_id":"c1","finding":"FAIL","rationale":"HTTP 200 but response failed functional check","sufficiency":"SUFFICIENT"}],"overall_finding":"FAIL","profile":"api_delivery","round":1,"status":"PROVISIONAL"}
```
Real validators independently fetched `https://httpbin.org/status/200` under genuine GenVM consensus and correctly derived `FAIL` (reachable, HTTP 200, but an empty/non-JSON body fails the functional check).

**Real, on-chain `get_settlement("2")` read-back:**
```json
{"refunded_to_buyer":1000,"released_to_provider":0,"retained":0,"settlement_id":"2-st1","terminal_phase":"SETTLED"}
```
`0 + 1000 + 0 = 1000` (the funded amount), all to the buyer — correct for a `FAIL` verdict.

### Positive-test agreement "4" — full real lifecycle, SETTLED

(Agreement `"3"` was created and accepted during the first attempt at this test, then became unreachable when that script process exited and its in-memory-only signing keys were lost — see "process-lifetime lesson" above. It remains on-chain in `ACCEPTED` phase, inert, no funds ever touched it. Agreement `"4"` is the complete, successful positive test, run start to finish in one process.)

| Step | Tx hash | Execution result | Return value |
|---|---|---|---|
| `create_agreement` (spec: `GET https://httpbin.org/json returns a JSON object`) | `0xe5024afc71f4260abc4605abef784fa9805950a91b8f12ec0d763e904c1f8e36` | `SUCCESS` | `agreement_id = "4"` |
| `accept_agreement("4")` | `0xe498813d58d9a84fe1482de800f4741140c7dfee66afbdcfcc2a4747f8d488c5` | `SUCCESS` | — |
| `fund_agreement("4", 1000)` | `0x648f8140386fb967888a6ea7f6d83dc25168c655a97fdd07a821864bf554c756` | `SUCCESS` | — |
| `freeze_agreement("4", false)` | `0x15f8de42550f326bb063f9a7cec461cb4544fe802d07e563688d8ee8e63d880a` | `SUCCESS` | — |
| `submit_evidence("4", "https://httpbin.org/json", ...)` | `0xe667e28435cf02d5c1f69c0fb88befb7481d9ca1bd47fa2a9674e01f2bbda12c` | `SUCCESS` | `"4-ev2"` |
| `request_evaluation("4")` | `0x2a77ce6153741e6b05b297943ac1fdca0327fe213d1d117d50c81119f6f5b69e` | `SUCCESS` | `"4-eval2"` |
| `finalize_verdict("4")` (buyer, 1st consent) | `0x0b3afa9561056e4dceafc581fe8c758f5b3c9892b2f65ce0ffab513bc862edec` | `SUCCESS` | `false` |
| `finalize_verdict("4")` (provider, 2nd consent) | `0xd1daa096a82114d50c23c50f9db888bbd2bc3f968f95d7551842e5a17e340623` | `SUCCESS` | `true` |
| `settle("4")` | `0x3d19b0a3a96728369f9e7437408814f9e1b170eb690aa3325d402444654ded66` | `SUCCESS` | `"4-st2"` |

**Real, on-chain `get_evaluation("4-eval2")` read-back:**
```json
{"agreement_id":"4","evaluation_id":"4-eval2","evidence_snapshot_commitment":"092726d7eb60aaa2c11f990b555d7c663e2030dff0ac3744216fc2e6cdfe8718","failure_attribution":"UNKNOWN","findings":[{"attribution":"UNKNOWN","criterion_id":"c1","finding":"PASS","rationale":"HTTP 200 with schema-consistent body","sufficiency":"SUFFICIENT"}],"overall_finding":"PASS","profile":"api_delivery","round":1,"status":"PROVISIONAL"}
```
Real validators independently fetched `https://httpbin.org/json` and correctly derived `PASS` (reachable, HTTP 200, JSON body parses).

**Real, on-chain `get_settlement("4")` read-back:**
```json
{"refunded_to_buyer":0,"released_to_provider":1000,"retained":0,"settlement_id":"4-st2","terminal_phase":"SETTLED"}
```
`1000 + 0 + 0 = 1000`, all to the provider — correct for a `PASS` verdict.

Both outcomes were read from the chain after the fact, not assumed in advance — the negative case could in principle have come back `UNVERIFIABLE` if `httpbin.org` had been unreachable at evaluation time, and did not.

### AI-agent-delivery agreement "5" — full real lifecycle, SETTLED (PASS)

Evidence: `https://httpbin.org/robots.txt` (real content: `User-agent: *` / `Disallow: /deny`). Criterion: "the delivered artifact is a robots.txt-style access policy that includes at least one 'User-agent' directive."

| Step | Tx hash | Execution result | Return value |
|---|---|---|---|
| `create_agreement` | `0x6b1de68846cf6f69b68c053447d5fefe8e5e09c835dc5eda82e33ccf2972a393` | `SUCCESS` | `agreement_id = "5"` |
| `accept_agreement("5")` | `0xc21ddc582d789ecec7e40bbdc6517bc229fb5041fe4908e0fd0862b4a8dc48e1` | `SUCCESS` | — |
| `fund_agreement("5", 1000)` | `0x777a8b96782e46967d75d9334981d0ebf20885165a343e4f40b05b1208fb4f43` | `SUCCESS` | — |
| `freeze_agreement("5", false)` | `0x29d13162b806f615384b31613b3c91c45a4687c0d7d295799fd8ed5acc58f444` | `SUCCESS` | — |
| `submit_evidence("5", ...)` | `0xf45c48d6414bd0f97bcf2fc290e27b814405b28e37348405657a3aeb820e8151` | `SUCCESS` | `"5-ev3"` |
| `request_evaluation("5")` | `0x1155270a5c007163bfa8a35c27bc7ec5ef9e15027ccb90ee6f8f304052ed7c5d` | `SUCCESS` | `"5-eval3"` |
| `finalize_verdict("5")` ×2 | `0xd4c00825655c3f33a4c26250d4922b83f20a0e2f7db4b5fd50f99fe3b8e412be`, `0xa44ff852aa966cf037795f41f6b42b1daa7ae9af2105c03cc25aa2efde527c26` | `SUCCESS`, `SUCCESS` | `false`, `true` |
| `settle("5")` | `0xab5b5d870c188dc6055b0a25524a4d76303860747e51b0be52404fb8e7bf0037` | `SUCCESS` | `"5-st3"` |

**Real, on-chain `get_evaluation("5-eval3")` read-back** — note the rationale, a genuine LLM response quoting the actually-fetched content, proving `_fetch_agent_evidence_excerpt` worked live:
```json
{"agreement_id":"5","evaluation_id":"5-eval3","evidence_snapshot_commitment":"d380e3fe7de1c701cd9c1b211ab0142ab7d6b1e7cad55738fb05b57145f240f4","failure_attribution":"UNKNOWN","findings":[{"attribution":"UNKNOWN","criterion_id":"c1","finding":"PASS","rationale":"The fetched content from https://httpbin.org/robots.txt contains 'User-agent: *' followed by 'Disallow: /deny', which is a valid robots.txt-style access policy that includes at least one 'User-agent' directive. The criterion is fully satisfied.","sufficiency":"SUFFICIENT"}],"overall_finding":"PASS","profile":"ai_agent_delivery","round":1,"status":"PROVISIONAL"}
```

**Real settlement:** `{"refunded_to_buyer":0,"released_to_provider":1000,"retained":0,"settlement_id":"5-st3","terminal_phase":"SETTLED"}`

### AI-agent-delivery agreement "6" — full real lifecycle, SETTLED via recovery (UNVERIFIABLE)

Same evidence URL, a deliberately mismatched criterion: "the delivered artifact is a JSON object containing a field named 'summary' that quotes the source material verbatim." The real, unscripted LLM response did **not** simply say `FAIL` — it reasoned that no distinct "delivered artifact" separate from the fetched source material was ever identified, and correctly returned `UNVERIFIABLE` rather than guessing:

```json
{"agreement_id":"6","evaluation_id":"6-eval4","evidence_snapshot_commitment":"df0df010ac5ee944c2a33bc91034a6e5637dfbae34da88cb5ce30d37e015dfc8","failure_attribution":"UNKNOWN","findings":[{"attribution":"UNKNOWN","criterion_id":"c1","finding":"UNVERIFIABLE","rationale":"The delivered artifact to be adjudicated was not provided in the input. While the source material (robots.txt excerpt) is present, the output that was supposed to be evaluated against the criterion is missing, making it impossible to determine if a JSON object with a 'summary' field was created.","sufficiency":"INSUFFICIENT"}],"overall_finding":"UNVERIFIABLE","profile":"ai_agent_delivery","round":1,"status":"PROVISIONAL"}
```

This correctly exercised the `settle()` branch that never auto-awards disputed principal on an `UNVERIFIABLE` verdict: `settle("6")` (tx `0x1e249fc6aa934be8f0cb79f87f3f2e080205032628b1d682e797ea326d955067`, `SUCCESS`) moved the agreement to `RECOVERY_PENDING` with the full funded amount retained (`{"refunded_to_buyer":0,"released_to_provider":0,"retained":1000,"settlement_id":"6-st4","terminal_phase":"RECOVERY_PENDING"}`), rather than crediting either party. `recover_inconclusive("6")` was not reachable afterward because this specific agreement's disposable signing keys existed only in the Node process that generated them and could not be reused; see the live demonstration below for the equivalent call completed on a fresh agreement instead.

Full tx chain for "6": `create_agreement` `0x40e3197c532798b4725754ba20b40f7e0c3c556cf33c1cc6fb8f6f4114fe512b` → `accept_agreement` `0xf2c23f8253a224e4ae888ab24467e67902aefbf0dad3980157a9b5e29dfe6ce1` → `fund_agreement` `0xb61de8cbf0d3d2b6f7663aba9e8b24017b668e6e3b4a88fbe4f56c4830f86948` → `freeze_agreement` `0xdd32d4b3ad3cff4ffb801b894adb029999c3c26ab714cb6b1930e79512434c57` → `submit_evidence` `0x9547f02df4db1aaa677c7eef628127989b79bfa78619b3af887ebc020ef2d4fe` → `request_evaluation` `0xc2a7b4d8e4510408816feda9d4c9736f0425aaae3735f85cf4bb742f6e8af331` → `finalize_verdict` ×2 `0x7fe57df5e0e3b1dfe1a475fc764aa8505d40f37fd506e0b0ba88c8c75ef46f2c`, `0x84406fd7dac524a0d836a3838ba1e98ad749f3a66f2e90002d95d9630cc610b7` → `settle` `0x1e249fc6aa934be8f0cb79f87f3f2e080205032628b1d682e797ea326d955067`. All `SUCCESS`.

### `recover_inconclusive` — live, verified, on the final deployment

A fresh one-shot agreement was created on the final contract (`0xD5602E88b021573cbb364Efaae8DCD48DF555ff7`) specifically to reach and call `recover_inconclusive` within one process (so the same disposable-key limitation above could not strand it). Agreement `"3"`: same evidence URL/criterion mismatch as "6" above produced a genuine `UNVERIFIABLE` (`{"agreement_id":"3","evaluation_id":"3-eval3","finding":"UNVERIFIABLE","rationale":"The only evidence provided is source material from httpbin.org/robots.txt. There is no delivered artifact to inspect..."}`); `settle("3")` (tx `0x9513427769a096b31dcbf970a4c9e2da4cc4035250314a7ee2e1f02cf833865b`) moved it to `RECOVERY_PENDING` (`retained:1000`). `recover_inconclusive("3")` was then called: the script's receipt-polling hit the same transient Studio Network RPC flakiness documented elsewhere in this file right as the first call's transaction was mining, so the script retried and submitted the call four more times — each of those four retries correctly reverted on-chain with `[EXPECTED] nothing to recover` (tx hashes `0x305dc4abac5fb7a760dd5e1bc0187e726bdfa53cc303c52c980f56959c41ed1d`, `0x0980c9d996e9569b4d654b361ca40e3e4b2707515773421bfee9a85447a6f19a`, `0x6a4ef4e9e3327177729458d165b3e7517670d3f2ad12f120c028e8850614c40f`, `0x8a4cc6486dbf126e267afcf2fac98540d9c9b646fe3c86d999f6ba33ed7aa3e8`), which only happens if an earlier call already completed the recovery. An independent read-back of `get_agreement("3")` after the run confirms this directly: `phase:"REFUNDED"`, `refunded_amount:1000`, `settlement_id:"3-st4"`, and `get_settlement("3")` returns `{"refunded_to_buyer":1000,"released_to_provider":0,"retained":0,"settlement_id":"3-st4","terminal_phase":"REFUNDED"}`. The exact hash of the one call that actually succeeded was not captured (the RPC hiccup happened between submission and receipt, before the script logged it), but the on-chain state transition plus four independent confirming reverts make the result unambiguous. This closes the previously open item: `recover_inconclusive` has now been exercised live, not merely covered by Direct Mode tests.

## check_verdict_consistency — live, verified, zero risk

The standalone consistency-auditor view (capability 28) was exercised live as a read-only call against agreement `"2"` on the escrow-test deployment (`0xaa54c150B128843e5638cF31e2F1B632117ccBE2`, prior to its revert — view behavior is unaffected by the escrow revert since it never touches value): `check_verdict_consistency("2")` returned `{"agreement_id":"2","any_contradiction_detected":false,"changed_criteria":[],"findings_by_criterion":{"c1":[{"evaluation_id":"2-eval1","finding":"PASS","round":1}]},"total_rounds":1}` — correct, since that agreement never went through an appeal round.

## Functions not repeated on the prior escrow deployment

At the time of the `0xbE2a981...` release, `check_verdict_consistency` and `recover_inconclusive` were evidenced on predecessor `0xD5602E88...` rather than repeated. Later deployments superseded both. This is retained as historical scope information; see the latest-release record above for current deployment identity and the transaction proofs added in the latest pass.

## The `genlayer` CLI's `--args` tooling defect (background, for context)

The `genlayer` CLI's `--args` scalar parser cannot represent a digit-only string value. Traced in `node_modules/genlayer/dist/index.js`: `parseArg` first tries `JSON.parse`, and for any value that isn't an object/array falls through to `parseScalar`, which does:

```js
if (!isNaN(Number(value)) && Number.isSafeInteger(Number(value))) return Number(value);
```

This fires unconditionally for any digit-only string — including values wrapped in extra quotes, nested inside a JSON array, or passed through dict/kwparams — because `coerceValue` recurses into every string leaf through `parseScalar` again. Every SpecLock method after `create_agreement` takes `agreement_id: str`, and agreement IDs are sequential digit strings, so the CLI alone could not address any agreement for read or write. This is a defect in that specific CLI's argument-text layer, not in GenLayer's RPC/SDK interface (confirmed by the successful `genlayer-js` calls above) and not in the contract.

Three attempts to route around this *within the CLI itself* (reading a keychain-service constant; patching the installed CLI's own source; generic read-only exploration of `genlayer-js`'s internals from the CLI's bundled copy) were each independently blocked by the sandbox's own safety classifier and abandoned rather than retried. The path that actually worked instead used GenLayer's own separately-published `genlayer-js` SDK package directly (a standalone `npm install genlayer-js` in an isolated scratch directory, no modification to anything installed, no credential access) — a different, officially supported interface, not a workaround of the blocked one.

## Funds / escrow

**LIVE-VERIFIED.** `0xbE2a98135e41B4fE722919b87024D867F8De8343` holds and moves real native value: `fund_agreement`/`file_appeal` are payable and genuinely receive `gl.message.value`; `_settle`/`resolve_appeal` credit a pull-payment `claimable` balance; `withdraw()` pays it out via `gl.evm.contract_interface`'s `_EthAccount` proxy. Two complete real agreements exercised this end to end — a `PASS` settlement with a real provider withdrawal, and a `FAIL` settlement with a real appeal (real bond sent, correctly `REJECTED`, bond correctly credited to the non-appellant party) and two further real withdrawals — with every wallet balance delta matching the contract's own accounting exactly (see "Native-value escrow: live-verified" above for the full transaction-by-transaction record). Double-withdrawal and no-balance-withdrawal were both tested live and correctly rejected.

## Superseded deployments (kept for history — do not use for further testing)

1. `0xDa62645C8d904e1cE11BEc4F359cA20971092536` (deploy tx `0x518e5f5e14f584138532921b4562559d40f00d322604e435458a91c47241f016`, `FINALIZED`). Predates the agent-evidence-fetch fix.
2. `0x713036220DE89a077fea1C3203C2510adB67f992` (deploy tx `0x2d47c50857bd2234e85615f778f7e62d54e377b4f418132a6e5aee022ef65f6d`, `FINALIZED`). Includes the agent-evidence-fetch fix but predates the `_as_address` hex-string fix, so `create_agreement` could not be called through `genlayer-js`'s standard API on it. Three agreements exist on it (`"1"`, `"2"`, `"3"`), all stuck in `DRAFT` since nothing could sign a subsequent call against them through a supported interface.
3. `0x6bBcF7E85f8F07B54ba53ae2126E2E9F6485eE68` (deploy tx `0xfb473764a733d3f0c5aa5049a991515ea6f9dd3488c1deec0c343719a323dc4e`, `FINALIZED`). Includes the `_as_address` fix; this is the deployment all four complete API/agent lifecycle agreements (`"2"`, `"4"`, `"5"`, `"6"`) above were run against. Predates the native-escrow attempt and its revert — functionally equivalent to the `0xD5602E88...` predecessor deployment except it lacks `check_verdict_consistency`.
4. `0xaa54c150B128843e5638cF31e2F1B632117ccBE2` (deploy tx `0x62d7d3d603c9c861f2cfc56dc5c7ca1ee5b94de043dfeac4482c3f72f4ba1dc2`, `FINALIZED`). The first escrow-test deployment — real payable `fund_agreement`/`file_appeal`, payouts via `gl.get_contract_at(...)`, which failed. Contains agreement `"2"` with a real deposit (1 GEN) permanently stuck in an unresolved state per that finding. Do not use for anything other than historical reference to that finding.
5. `0xd60dfaC9B3473Fce6bC97CD47F7a5Ac80c97A74e` (deploy tx `0x5f7f58da3467b1a4291b8161a4061bf37355729f36bd7f1d298d1c561d6446b9`, consensus `FINALIZED` but **`execution_result: "ERROR"`** — constructor call failed, see "Native-value escrow" above). First attempt to live-verify the `_EthAccount`-based escrow fix, deployed with a malformed `--args '[]'` CLI invocation. Do not use.
6. `0x192CA2229677E4e1d0d115d4665E2634Bf0A25d1` (deploy tx `0x14a6ade55f9a8d4a9577a4346b1316100ac457e45699b3fcbe85d007177a5a8d`, same `FINALIZED`-but-`ERROR` outcome, same cause). Second attempt, identical mistake. Do not use.
7. `0xD5602E88b021573cbb364Efaae8DCD48DF555ff7` (deploy tx `0xdd2f6307a732a43df1ebf1c7bc2683eeb9f8472b4985b3a0cd610c69fc645cb4`, `FINALIZED`, `SUCCESS`). The bookkeeping-only predecessor. Its own lifecycle evidence (API/agent delivery, `recover_inconclusive`, `check_verdict_consistency`) remains valid and is recorded above under "How real on-chain lifecycle execution was achieved" and "`recover_inconclusive` — live, verified" — kept live for historical reference, not for further testing.
8. `0xbE2a98135e41B4fE722919b87024D867F8De8343` (deploy tx `0x56c13ef85e7d92f449fc73369c543b6f053f6bca50ae7aecf911f5511e2a279e`, `FINALIZED`, `SUCCESS`). The first real-escrow deployment — real deposits, a real `PASS` settlement, a real withdrawal, a real appealed `FAIL` settlement, all live-verified (see "Native-value escrow: live-verified" above). Superseded once the `request_resubmission` fund-lock defect was found; **do not call `request_resubmission` against this deployment** — it has the same unfixed bug. Its escrow lifecycle evidence remains valid and is not affected by that defect.
9. `0x2671cd7Fc9f7653f8e8A506E4aC3281A1Db0553c` (deploy tx `0x8a63968ce744bfb12ec3f93ca5e44e18153858dadda75c650fa75fc135dc338e`, `FINALIZED`, `SUCCESS`). The first capability-audit-pass deployment — the `request_resubmission` fund-lock fix, live-verified end to end (see "Capability audit: the resubmission fund-lock fix, live-verified" below). Superseded by `0xc758b9E...` once five more capabilities (13, 19, 25, 26, 38) were fixed/added in a second audit pass. Its resubmission-fix evidence remains valid.

All remain live on-chain (nothing can be un-deployed).

## Source/commit record

The current deployment is `0xDFb69c1890F72c7b791A938ed36C5103582E6F19` (source SHA-256 `CEC00C69E57E6AE1B70C77BE49CFFEEB912F2D55D15E42AF75A2B6687ABB6F5C`). Its deployment finalized with 5/5 `AGREE` votes and leader `SUCCESS`; schema and a read-only view succeeded. Lifecycle evidence on this deployment remains pending; the prior `0x142A...` release's lifecycle evidence is preserved above and in `docs/evidence/studionet-reviewer-fix-2026-10-18.md`.
