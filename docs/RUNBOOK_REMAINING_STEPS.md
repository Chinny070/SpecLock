# Runbook: remaining Studionet steps for the repository owner

This hands off the rest of the live Studionet exercise described in `docs/DEPLOYMENT.md`. It exists because the `genlayer` CLI's `--args` parser cannot encode a digit-only string (every SpecLock `agreement_id` is one), so every call below must be made through a tool that lets you type `agreement_id` as a literal string field — the GenLayer Studio web UI (`https://studio.genlayer.com`, connect the `my-studionet-wallet` account) is the simplest option, since its contract-call forms are schema-driven and not subject to this bug.

**Contract (current, fixed source — commit `badcf10`):** `0x713036220DE89a077fea1C3203C2510adB67f992` on `studionet` (chain id `61999`). Do not use the earlier `0xDa62645C8d904e1cE11BEc4F359cA20971092536` — it predates the agent-evaluator fix.

**Already on-chain, all FINALIZED:**
- Agreement `"1"` — positive-test reference copy (httpbin.org/json spec).
- Agreement `"2"` — negative test: `https://httpbin.org/status/200` (empty body, will `FAIL` the functional check).
- Agreement `"3"` — positive test: `https://httpbin.org/json` (real JSON body, will `PASS`).

All three: buyer `0xaffE15eEc45b68835cc9E5B4Ab85dD5deaE8e70b`, provider `0x32e3eb6fb78bc70ccfee52013c1e6b64e1729754` (local alias `speclock-provider`, a fresh keystore created this session on this machine, already funded with 2 GEN for its own gas; its password is deliberately not written here — ask in chat if you need it to sign as the provider locally, or just use its public address wherever only the address is needed).

## ⚠️ The agent (AI-delivery) profile has not been exercised on this deployment yet

The evidence-fetch fix is live in this contract, but no `ai_agent_delivery` agreement has been created against it yet. If you want to demo that profile, create one (spec + `ai_agent_delivery` profile + a criterion referencing a real text URL) and follow the same steps below, substituting its agreement id and the real URL you choose for `submit_evidence`.

## Recommended order — exercise agreement "2" (negative) and "3" (positive)

For **each** of `"2"` and `"3"`:

1. **`accept_agreement(<id>)`** — signer: provider (`0x32e3...9754`).
2. **`fund_agreement(<id>, 1000)`** — signer: buyer. `1000` is an arbitrary bookkeeping unit, not GEN (see `docs/DEPLOYMENT.md` "Funds / escrow" — never moves real value).
3. **`freeze_agreement(<id>, false)`** — signer: either. `false` for `acknowledge_ambiguity` (neither spec has vague terms, so this value doesn't change the outcome, but the parameter must be present).
4. **`submit_evidence(<id>, <url>, <digest>, "{\"criterion_id\": \"c1\"}")`** — signer: either.
   - For `"2"`: `url="https://httpbin.org/status/200"`, `digest="5a2474b3a617c332f113a5ea8ca1be85fe299636dce3b0217e400c6c97136359"` (sha256 of the URL string — the contract never verifies this against fetched content, it's just a commitment receipt).
   - For `"3"`: `url="https://httpbin.org/json"`, `digest="4e31295c1f9e08faed830ab51b0cb765a939d2f85dc5a6907624b85802488f43"`.
5. **`request_evaluation(<id>)`** — signer: either. Triggers a real `gl.nondet.web.get` fetch by every validator independently.
   - `"2"` expected: `overall_finding="FAIL"`, `failure_attribution="DELIVERY"` (reachable, HTTP 200, but empty/non-JSON body fails the functional check).
   - `"3"` expected: `overall_finding="PASS"`.
6. Read back **`get_evaluation(<the returned evaluation_id>)`** to see the real findings.
7. **`finalize_verdict(<id>)`** — call once as buyer, once as provider (mutual consent; the first call returns `false`, the second returns `true` and actually finalizes — see `docs/STATE_MACHINE.md`).
8. **`settle(<id>)`** — signer: either.
   - `"2"` expected: `released_to_provider=0`, `refunded_to_buyer=1000`.
   - `"3"` expected: `released_to_provider=1000`, `refunded_to_buyer=0`.

## An appeal round (optional, exercises `file_appeal`/`resolve_appeal`)

On either agreement, before `finalize_verdict`, either party can call `file_appeal(<id>, ["c1"], "some grounds text")`, then either party calls `resolve_appeal(<id>)` to trigger re-evaluation (this re-fetches the same URL for real). Compare the new `get_evaluation` result to the old one — if `c1`'s finding is unchanged, the appeal resolves `REJECTED`; if it changed, it resolves `UPHELD`. Bounded by `max_appeal_rounds=2`.

## Recording results

Please append whatever you execute (tx hashes, statuses, decoded return values, and the final `get_evaluation`/`get_settlement` reads) to `docs/DEPLOYMENT.md` under a new "## Lifecycle exercise results" section, in the same format used for the deploy and `create_agreement` transactions above it, so the feature matrix can be updated from `IMPLEMENTED_LOCAL_ONLY` to `IMPLEMENTED_VERIFIED` for the capabilities you exercise.
