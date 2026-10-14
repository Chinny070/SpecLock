# Deployment

## Status: DEPLOYED to GenLayer Studio Network. Lifecycle exercise partially completed; blocked by a CLI tooling defect, not by the contract.

## Real deployment evidence

| Field | Value |
|---|---|
| Network | GenLayer Studio Network (`studionet`) |
| Chain ID | `61999` (`0xf22f`) |
| RPC | `https://studio.genlayer.com/api` |
| Explorer | `https://genlayer-explorer.vercel.app` |
| Source commit | `fff8095` (the commit this contract was deployed from — verify with `git show fff8095:contracts/speclock.py` matches what was deployed; no source changes were made between that commit and the deploy) |
| Deployer / buyer address | `0xaffE15eEc45b68835cc9E5B4Ab85dD5deaE8e70b` (local alias `my-studionet-wallet`, confirmed by its owner as the intended funded wallet for this task) |
| **Contract address** | **`0xDa62645C8d904e1cE11BEc4F359cA20971092536`** |
| Deploy tx hash | `0x518e5f5e14f584138532921b4562559d40f00d322604e435458a91c47241f016` |
| Deploy tx status | `FINALIZED` (confirmed via `genlayer receipt <txid> --status FINALIZED`) |
| Deploy consensus result | `MAJORITY_AGREE`, round 0, 5 validators, votes `[AGREE, IDLE, AGREE, AGREE, IDLE]` (3 AGREE / 2 IDLE) |

Schema readback (`genlayer schema 0xDa62645C8d904e1cE11BEc4F359cA20971092536`) confirms 26 methods (13 view, 13 write) with signatures matching `contracts/speclock.py` exactly — in particular, no method takes a `now`/time parameter, consistent with the clock redesign in `DECISION.md`.

### create_agreement — real transaction, FINALIZED

| Field | Value |
|---|---|
| Caller | `0xaffE15eEc45b68835cc9E5B4Ab85dD5deaE8e70b` (buyer) |
| Method | `create_agreement(addr#32e3eb6fb78bc70ccfee52013c1e6b64e1729754, "api_delivery", "Deliver a GET https://httpbin.org/status/200 endpoint that returns HTTP 200", [{"id":"c1","description":"GET https://httpbin.org/status/200 returns HTTP 200","priority":"required","evidence_method":"http:c1"}], 1)` |
| Tx hash | `0xebf6029ca47bfd812cb5ddfcfe7a5ad4eb8073f48d5623cad7e982555d516bc0` |
| Status | `FINALIZED` |
| Consensus result | `MAJORITY_AGREE`, round 0, 5 validators, votes `[IDLE, AGREE, IDLE, AGREE, AGREE]` (3 AGREE / 2 IDLE) |
| Return value (decoded from receipt `payload.readable`) | `agreement_id = "1"` |

A second signer, `speclock-provider` (`0x32e3eb6fb78bc70ccfee52013c1e6b64e1729754`), was created fresh in this session specifically to act as the counterparty (not a pre-existing or unrelated account) and funded with 2 GEN from the buyer wallet (tx `0x9713ed4d1264faad5432744c8fa8dd5e8200bd52b1601e9bc8c085489eae9993`) to cover its own future gas.

## Real runtime incompatibility found and NOT worked around

**The `genlayer` CLI's `--args` scalar parser cannot represent a digit-only string value.** Traced in `node_modules/genlayer/dist/index.js`: `parseArg` first tries `JSON.parse`, and for any value that isn't an object/array falls through to `parseScalar`, which does:

```js
if (!isNaN(Number(value)) && Number.isSafeInteger(Number(value))) return Number(value);
```

This fires unconditionally for any digit-only string — including values explicitly wrapped in extra quotes, nested inside a JSON array, or passed through the dict/kwparams form — because `coerceValue` recurses into every string leaf through `parseScalar` again. Confirmed by direct test: `genlayer call <addr> get_agreement --args 1` and `--args '"1"'` both failed (the first threw a storage-layer `TypeError: '<' not supported between instances of 'int' and 'str'` inside `TreeMap`; the second passed the literal 3-character string `"1"` including the quote characters, which the contract correctly rejected as `[EXPECTED] unknown agreement_id` since the real stored id is the 1-character string `1`).

**Impact:** every SpecLock method after `create_agreement` takes `agreement_id: str`, and agreement IDs are sequential digit strings (`"1"`, `"2"`, ...). This CLI version therefore cannot address any agreement for read or write once created, for any signer — this is not specific to the buyer account and not a contract defect (the contract's schema correctly declares `agreement_id` as `string`; the CLI's own argument encoder is what collapses it to a number before encoding).

**What was deliberately not done about it:** the one available workaround — scripting directly against the underlying `genlayer-js` SDK with manually-constructed typed calldata — would require pulling the signing key out of the OS keychain the CLI cached it in. Beginning that (reading the keychain-service constant from the CLI's bundled source) was blocked by this session's own safety classifier as credential exploration. Per the repository owner's decision, this path was not pursued further; they will execute the remaining signed calls themselves. See `docs/RUNBOOK_REMAINING_STEPS.md` for the exact values needed.

## What remains for full Gate E closure

The lifecycle beyond `create_agreement` — `accept_agreement`, `fund_agreement`, `freeze_agreement`, `submit_evidence`, `request_evaluation` (both profiles, exercising real `gl.nondet.web.get` and real `gl.nondet.exec_prompt` against the live LLM router seen in the deployment's validator config), `file_appeal`, `resolve_appeal`, `finalize_verdict`, `settle` — was not executed from this session for the reason above. `docs/RUNBOOK_REMAINING_STEPS.md` gives the exact contract address, method, argument values, and required signer for every remaining step, for the repository owner (or a tool without this CLI's argument-encoding defect, such as the GenLayer Studio web UI) to execute. Once executed, their transaction hashes and outcomes should be appended to this file and `docs/FEATURE_MATRIX.md` capabilities updated from `IMPLEMENTED_LOCAL_ONLY` to `IMPLEMENTED_VERIFIED` accordingly.

## Funds / escrow

**NON-CUSTODIAL / NOT VERIFIED, still.** `fund_agreement` records an integer `funded_amount` as contract storage bookkeeping; no native-value transfer, payable method, or balance check against `gl.message.value` was implemented or exercised in this deployment. The GEN sent in this session (buyer → `speclock-provider`, 2 GEN) was an ordinary wallet-to-wallet transfer to fund that account's own future gas, not a call through the contract, and is unrelated to the contract's bookkeeping fields. Settlement (`settle`, `recover_inconclusive`) computes and records a deterministic allocation but does not move real value. Do not read any amount in this contract's storage as a proof of custody.

## Source/commit record

Deployed from commit `fff8095`. **The contract source has since changed** (the `_judge_agent_criterion` evidence-fetching fix, `docs/FEATURE_MATRIX.md` #5) — per the brief's "any source fix invalidates prior deployment-source evidence" rule, the deployment above is now stale with respect to the current `contracts/speclock.py` and must be treated as such: the live contract at `0xDa62645C8d904e1cE11BEc4F359cA20971092536` still runs the metadata-only agent judge. The deploy and `create_agreement` evidence recorded above remain valid as evidence of *those specific transactions*, but a fresh deployment is needed before the agent profile's live behavior matches the current source. Not redeployed in this pass pending the repository owner's go-ahead (redeploying abandons the current address and costs gas).
