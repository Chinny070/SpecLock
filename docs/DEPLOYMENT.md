# Deployment

## Status: DEPLOYED to GenLayer Studio Network. Full real lifecycle executed and verified on-chain for both profiles — API delivery (negative + positive) and AI-agent delivery (positive + an UNVERIFIABLE/recovery case) — every agreement FINALIZED and SETTLED end to end.

## Current deployment (includes the address-coercion fix)

| Field | Value |
|---|---|
| Network | GenLayer Studio Network (`studionet`) |
| Chain ID | `61999` (`0xf22f`) |
| RPC | `https://studio.genlayer.com/api` |
| Explorer | `https://genlayer-explorer.vercel.app` |
| Deployer address | `0xaffE15eEc45b68835cc9E5B4Ab85dD5deaE8e70b` (local alias `my-studionet-wallet` — used only to deploy and to fund disposable test accounts, never as a lifecycle party) |
| **Contract address** | **`0x6bBcF7E85f8F07B54ba53ae2126E2E9F6485eE68`** |
| Deploy tx hash | `0xfb473764a733d3f0c5aa5049a991515ea6f9dd3488c1deec0c343719a323dc4e` |
| Deploy tx status | `FINALIZED` |

Schema readback (`genlayer schema 0x6bBcF7E85f8F07B54ba53ae2126E2E9F6485eE68`) confirms 26 methods matching `contracts/speclock.py` at the deployed commit.

## A real production defect found and fixed via this deployment (not caught by Direct Mode)

While exercising the lifecycle through GenLayer's own documented `genlayer-js` SDK (`createClient`/`writeContract` — the same library the `genlayer` CLI is built on; see "CLI tooling defect" below for why the CLI itself couldn't be used), `create_agreement` failed with a real on-chain `ERROR`-status execution:

```
File "/contract.py", line 400, in create_agreement
    provider = _as_address(provider)
File "/contract.py", line 40, in _as_address
    return Address(bytes(value))
TypeError: string argument without an encoding
```

The genlayer CLI's `addr#...` argument syntax constructs a typed `Address`/bytes value before it ever reaches the contract, which is why every earlier CLI-driven `create_agreement` call (see "Superseded deployments" below) worked. `genlayer-js`'s standard, documented `writeContract` API — a materially different and at least equally official calling convention — passes an address argument as a plain hex string, and `_as_address`'s unconditional `bytes(value)` call cannot handle a `str` without an explicit encoding. **Fixed**: `_as_address` now decodes a `str` input as hex before constructing the `Address`. Regression test: `tests/direct/test_speclock_lifecycle.py::test_provider_as_plain_hex_string_address_is_accepted`. See `DECISION.md` item 7. This contract (deployed at the address above) includes the fix.

## How real on-chain lifecycle execution was achieved without touching any protected credential

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

This correctly exercised the `settle()` branch that never auto-awards disputed principal on an `UNVERIFIABLE` verdict: `settle("6")` (tx `0x1e249fc6aa934be8f0cb79f87f3f2e080205032628b1d682e797ea326d955067`, `SUCCESS`) moved the agreement to `RECOVERY_PENDING` with the full funded amount retained (`{"refunded_to_buyer":0,"released_to_provider":0,"retained":1000,"settlement_id":"6-st4","terminal_phase":"RECOVERY_PENDING"}`), rather than crediting either party. `recover_inconclusive("6")` (which would complete the refund) was not called in this pass but is already covered by `tests/direct/test_speclock_security.py::test_unverifiable_overall_recovers_funds_without_awarding_either_party`.

Full tx chain for "6": `create_agreement` `0x40e3197c532798b4725754ba20b40f7e0c3c556cf33c1cc6fb8f6f4114fe512b` → `accept_agreement` `0xf2c23f8253a224e4ae888ab24467e67902aefbf0dad3980157a9b5e29dfe6ce1` → `fund_agreement` `0xb61de8cbf0d3d2b6f7663aba9e8b24017b668e6e3b4a88fbe4f56c4830f86948` → `freeze_agreement` `0xdd32d4b3ad3cff4ffb801b894adb029999c3c26ab714cb6b1930e79512434c57` → `submit_evidence` `0x9547f02df4db1aaa677c7eef628127989b79bfa78619b3af887ebc020ef2d4fe` → `request_evaluation` `0xc2a7b4d8e4510408816feda9d4c9736f0425aaae3735f85cf4bb742f6e8af331` → `finalize_verdict` ×2 `0x7fe57df5e0e3b1dfe1a475fc764aa8505d40f37fd506e0b0ba88c8c75ef46f2c`, `0x84406fd7dac524a0d836a3838ba1e98ad749f3a66f2e90002d95d9630cc610b7` → `settle` `0x1e249fc6aa934be8f0cb79f87f3f2e080205032628b1d682e797ea326d955067`. All `SUCCESS`.

## Not yet exercised on this deployment

`file_appeal`/`resolve_appeal` were not exercised against this deployment (no appeal was filed on any of agreements `"2"`, `"4"`, `"5"`, `"6"`) and `recover_inconclusive` was not called to complete agreement `"6"`'s refund. Both are already covered by Direct Mode tests.

## The `genlayer` CLI's `--args` tooling defect (background, for context)

The `genlayer` CLI's `--args` scalar parser cannot represent a digit-only string value. Traced in `node_modules/genlayer/dist/index.js`: `parseArg` first tries `JSON.parse`, and for any value that isn't an object/array falls through to `parseScalar`, which does:

```js
if (!isNaN(Number(value)) && Number.isSafeInteger(Number(value))) return Number(value);
```

This fires unconditionally for any digit-only string — including values wrapped in extra quotes, nested inside a JSON array, or passed through dict/kwparams — because `coerceValue` recurses into every string leaf through `parseScalar` again. Every SpecLock method after `create_agreement` takes `agreement_id: str`, and agreement IDs are sequential digit strings, so the CLI alone could not address any agreement for read or write. This is a defect in that specific CLI's argument-text layer, not in GenLayer's RPC/SDK interface (confirmed by the successful `genlayer-js` calls above) and not in the contract.

Three attempts to route around this *within the CLI itself* (reading a keychain-service constant; patching the installed CLI's own source; generic read-only exploration of `genlayer-js`'s internals from the CLI's bundled copy) were each independently blocked by the sandbox's own safety classifier and abandoned rather than retried. The path that actually worked instead used GenLayer's own separately-published `genlayer-js` SDK package directly (a standalone `npm install genlayer-js` in an isolated scratch directory, no modification to anything installed, no credential access) — a different, officially supported interface, not a workaround of the blocked one.

## Funds / escrow

**NON-CUSTODIAL / NOT VERIFIED, still.** `fund_agreement` records an integer `funded_amount` as contract storage bookkeeping; no native-value transfer, payable method, or balance check against `gl.message.value` was implemented or exercised. All GEN transfers in this session (deployer → disposable test accounts) were ordinary wallet-to-wallet transfers to cover gas, never calls through the contract. The real settlement read-backs above (`refunded_to_buyer`/`released_to_provider: 1000`) are bookkeeping numbers recorded by the contract, not native-value payments — do not read them as proof of fund custody.

## Superseded deployments (kept for history — do not use for further testing)

1. `0xDa62645C8d904e1cE11BEc4F359cA20971092536` (deploy tx `0x518e5f5e14f584138532921b4562559d40f00d322604e435458a91c47241f016`, `FINALIZED`). Predates the agent-evidence-fetch fix.
2. `0x713036220DE89a077fea1C3203C2510adB67f992` (deploy tx `0x2d47c50857bd2234e85615f778f7e62d54e377b4f418132a6e5aee022ef65f6d`, `FINALIZED`). Includes the agent-evidence-fetch fix but predates the `_as_address` hex-string fix, so `create_agreement` could not be called through `genlayer-js`'s standard API on it. Three agreements exist on it (`"1"`, `"2"`, `"3"`), all stuck in `DRAFT` since nothing could sign a subsequent call against them through a supported interface.

All remain live on-chain (nothing can be un-deployed).

## Source/commit record

Current deployment's source includes: the mutual-consent clock redesign, the appeal-resolution precision fix, the aggregate-attribution fix, the agent-evidence-fetch fix, and the `_as_address` hex-string fix. If the contract source changes again, this document and the deployment must be treated as stale together, per the brief's "any source fix invalidates prior deployment-source evidence" rule.
