# Runbook: remaining Studionet steps for the repository owner

This hands off the rest of the live Studionet exercise described in `docs/DEPLOYMENT.md`. It exists because the `genlayer` CLI's `--args` parser cannot encode a digit-only string (every SpecLock `agreement_id` is one), so every call below must be made through a tool that lets you type `agreement_id` as a literal string field — the GenLayer Studio web UI (`https://studio.genlayer.com`, connect the `my-studionet-wallet` account) is the simplest option, since its contract-call forms are schema-driven and not subject to this bug.

**Contract:** `0xDa62645C8d904e1cE11BEc4F359cA20971092536` on `studionet` (chain id `61999`).

**Already on-chain:** agreement `"1"` exists (buyer `0xaffE15eEc45b68835cc9E5B4Ab85dD5deaE8e70b`, provider `0x32e3eb6fb78bc70ccfee52013c1e6b64e1729754` — a fresh keystore created this session, named `speclock-provider` locally, already funded with 2 GEN for its own gas; you do not need its private key to see its address work as a counterparty, but you do need it if you want to sign as the provider — it's in your local `genlayer account list`/keystore if this is the same machine, password `speclock-demo-pass-2026`).

## ⚠️ Read before running the agent (AI-delivery) profile

`_judge_agent_criterion` in the deployed contract does not fetch the evidence URL's content — it only hands the LLM a `{url, digest}` pair, never the real artifact text. A live `ai_agent_delivery` evaluation right now will be judged on no real substance and is not meaningful evidence of the "intelligent evaluation" capability working. Recommend holding off on an agent-profile on-chain demo until this is fixed (see `docs/FEATURE_MATRIX.md` #5) and redeployed. The steps below only exercise the **API delivery** profile, which does fetch real content and produces meaningful results.

## Agreement "1" — negative test (already created)

Spec: "Deliver a GET https://httpbin.org/status/200 endpoint that returns HTTP 200", criterion `c1` = "GET https://httpbin.org/status/200 returns HTTP 200". Note `httpbin.org/status/200` returns an **empty body**, which the contract's functional check (JSON-parseable body required) will correctly fail — this makes agreement "1" a real, meaningful **negative** test case (reachable, not functional → `FAIL`).

1. **`accept_agreement("1")`** — signer: provider (`0x32e3...9754`).
2. **`fund_agreement("1", 1000)`** — signer: buyer. `1000` is an arbitrary bookkeeping unit, not GEN (see `docs/DEPLOYMENT.md` "Funds / escrow" — this never moves real value).
3. **`freeze_agreement("1", false)`** — signer: either. `false` for `acknowledge_ambiguity` (this spec has no vague terms, so the ambiguity report is empty and the flag's value doesn't matter, but the contract requires it be present).
4. **`submit_evidence("1", "https://httpbin.org/status/200", "5a2474b3a617c332f113a5ea8ca1be85fe299636dce3b0217e400c6c97136359", "{\"criterion_id\": \"c1\"}")`** — signer: either. (The digest is sha256 of the URL string itself — the contract never verifies it against fetched content, it's just a commitment receipt; any 64-hex-char value works, but this one is reproducible: `sha256("https://httpbin.org/status/200")`.)
5. **`request_evaluation("1")`** — signer: either. This triggers a real `gl.nondet.web.get` fetch of `https://httpbin.org/status/200` by every validator independently. Expected real result: `overall_finding = "FAIL"`, `failure_attribution = "DELIVERY"` (reachable, HTTP 200, but empty/non-JSON body fails the functional check).
6. Read back **`get_evaluation(<the returned evaluation_id, e.g. "1-eval1">)`** to see the real findings.
7. **`finalize_verdict("1")`** — call once as buyer, once as provider (mutual consent; the first call returns `false`, the second returns `true` and actually finalizes — see `docs/STATE_MACHINE.md`).
8. **`settle("1")`** — signer: either. Expected: `released_to_provider=0`, `refunded_to_buyer=1000`, `retained=0`.

## A second agreement — positive test (you create this one)

Create a new agreement pointing at an endpoint that returns real JSON, e.g.:

- spec: `"Deliver a GET https://httpbin.org/json endpoint that returns a JSON object"`
- criteria: `[{"id": "c1", "description": "GET https://httpbin.org/json returns a JSON object", "priority": "required", "evidence_method": "http:c1"}]`
- `max_resubmissions`: `1`

Then repeat steps 1–8 above, substituting the new `agreement_id` (whatever `create_agreement` returns — read it the same way `docs/DEPLOYMENT.md` did, via the receipt's decoded return payload) and evidence:

- `submit_evidence(<id>, "https://httpbin.org/json", "4e31295c1f9e08faed830ab51b0cb765a939d2f85dc5a6907624b85802488f43", "{\"criterion_id\": \"c1\"}")`

Expected real result: `overall_finding = "PASS"` (reachable, HTTP 200, JSON body parses).

## An appeal round (optional, exercises `file_appeal`/`resolve_appeal`)

On either agreement, before `finalize_verdict`, either party can call `file_appeal(<id>, ["c1"], "some grounds text")`, then either party calls `resolve_appeal(<id>)` to trigger re-evaluation (this re-fetches the same URL for real). Compare the new `get_evaluation` result to the old one — if `c1`'s finding is unchanged, the appeal resolves `REJECTED`; if it changed (e.g. the target endpoint's response changed between rounds), it resolves `UPHELD`. Bounded by `max_appeal_rounds=2`.

## Recording results

Please append whatever you execute (tx hashes, statuses, decoded return values, and the final `get_evaluation`/`get_settlement` reads) to `docs/DEPLOYMENT.md` under a new "## Lifecycle exercise results" section, in the same format used for the deploy and `create_agreement` transactions above it, so the feature matrix can be updated from `IMPLEMENTED_LOCAL_ONLY` to `IMPLEMENTED_VERIFIED` for the capabilities you exercise.
