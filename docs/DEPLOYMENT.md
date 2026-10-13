# Deployment

## Status: NOT DEPLOYED

No GenLayer network (Studio, testnet, or mainnet) deployment was performed. This section records exactly why and what would be needed, rather than fabricating a deploy transaction, address, or receipt.

## What was checked

- `gh --version` → 2.95.0, authenticated to push to `https://github.com/Chinny070/SpecLock.git` (confirmed by the backup-branch push in this session).
- `genlayer-test` ships a local simulator (`glsim`) that "executes contracts via the direct mode engine" (its own package docstring) rather than real GenVM/multi-validator consensus — it is not a substitute for Gate E.
- No GenLayer Studio/testnet/mainnet RPC URL, chain id, or funded signer key was provided by the user or discoverable in this environment. `gltest.config.yaml` was not created in this repository (the brief lists it as optional-if-needed), so `gltest` falls back to its own default `localnet` configuration, which is also not a real network.

## What would be required to close this gate (concrete next action)

1. User-supplied (or otherwise provisioned) RPC URL + chain id for GenLayer Studio or a testnet (e.g. `testnet_asimov`/`testnet_bradbury`, both listed as available networks by `gltest`'s own default config output).
2. A funded signer account private key supplied via environment variable (never pasted into chat — consistent with this session's credential-handling rules) in a `.env` file consumed by `gltest`/the GenLayer CLI.
3. `genlayer deploy contracts/speclock.py` (or `gltest`'s Studio Mode) against that network, recording: deployer public address, source commit SHA, contract blob hash, deploy tx hash, contract address, receipt, and Explorer URL.
4. Exercise `create_agreement` → `accept_agreement` → `fund_agreement` → ... → `settle` end to end against the live network for both profiles, with real `gl.nondet.web.get`/`gl.nondet.exec_prompt` calls (no mocks), and capture validator agreement/disagreement evidence.
5. Only then would capabilities currently marked `IMPLEMENTED_LOCAL_ONLY` in `docs/FEATURE_MATRIX.md` be promotable to `IMPLEMENTED_VERIFIED`.

## Funds / escrow

**NON-CUSTODIAL / NOT VERIFIED.** `fund_agreement` records an integer `funded_amount` as contract storage bookkeeping; no native-value transfer, payable method, or balance check against `gl.message.value` was implemented or exercised. Settlement (`settle`, `recover_inconclusive`) computes and records a deterministic allocation (`released_to_provider`/`refunded_to_buyer`/`retained`) but does not move real value. Do not read any amount in this contract's storage as a proof of custody.

## Source/commit record at time of writing this document

See `git log -1` in this repository for the exact commit this document was written against; this file will need updating (not silently left stale) if the contract source changes after a future deployment attempt, per the brief's "any source fix invalidates prior deployment-source evidence" rule.
