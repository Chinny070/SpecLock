# Deployment

## Status: NOT DEPLOYED (RPC connectivity now verified; funding still unavailable)

No GenLayer network (Studio, testnet, or mainnet) deployment was performed. This section records exactly what was checked, what was deliberately not done and why, rather than fabricating a deploy transaction, address, or receipt.

## What was checked (this pass)

- `gh --version` → 2.95.0, authenticated to push to `https://github.com/Chinny070/SpecLock.git` (confirmed by the backup-branch push and the main-branch pushes in this session).
- A `genlayer` CLI (npm package, v0.39.2) is installed in this environment, separate from the Python `genlayer-test`/`genvm-linter` tools, with `deploy`, `call`, `write`, `account`, `network`, `appeal`, `appeal-bond`, `finalize`, and `staking` subcommands. Its `appeal`/`appeal-bond`/`finalize` commands operate on **protocol-level** GenVM transaction finality/appeals — a different layer from SpecLock's own **application-level** `file_appeal`/`resolve_appeal`/`finalize_verdict` methods (see the brief's explicit warning not to conflate the two, and `docs/STATE_MACHINE.md` "Protocol finality vs. SpecLock verdict finality").
- `genlayer network info` confirms the CLI's active network is `studionet` (GenLayer Studio Network, chain id `61999`, RPC `https://studio.genlayer.com/api`, explorer `https://genlayer-explorer.vercel.app`).
- **RPC connectivity independently verified**, separate from any signer/funding: `curl -s -X POST https://studio.genlayer.com/api -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'` returned `{"jsonrpc":"2.0","result":"0xf22f","id":1}` — `0xf22f` = `61999` decimal, matching the CLI's reported chain id. The network is reachable from this environment.
- `genlayer account list` shows a number of pre-existing local keystores on this machine, left over from other, unrelated work (names like `gltest-buyer`, `rc-provider`, etc.) — these were **not created by this session** and were only inspected read-only (`genlayer account show`, which reports balance but never touches key material). Two checked (`default`, `gltest-runner`) both report `0 GEN` and `status: locked`. No private key was requested, displayed, or exported at any point, consistent with the credential-handling rules for this session.
- `genlayer account create`/`account send` exist, but there is no CLI faucet command; funding a Studio-network account appears to require a separate (likely browser-based) faucet or manual top-up that only the account's owner can authorize. No account was created, unlocked, or funded in this session.
- `genlayer-test` ships a local simulator (`glsim`) that "executes contracts via the direct mode engine" (its own package docstring) rather than real GenVM/multi-validator consensus — it is not a substitute for Gate E even though it is reachable.

## What is still missing to close this gate

1. A funded signer on `studionet` (or a testnet) authorized by its owner for this deployment — not one of the pre-existing unrelated local keystores found above. Funding would need to go through whatever faucet/top-up process GenLayer Studio provides; this session did not attempt it since that decision belongs to whoever owns the funds.
2. `genlayer deploy contracts/speclock.py --network studionet` (or equivalent) once a funded signer is available, recording: deployer public address, source commit SHA, contract blob hash, deploy tx hash, contract address, receipt, and the Explorer URL (`https://genlayer-explorer.vercel.app`).
3. Exercise `create_agreement` → `accept_agreement` → `fund_agreement` → ... → `settle` end to end against the live network for both profiles, with real `gl.nondet.web.get`/`gl.nondet.exec_prompt` calls (no mocks), and capture validator agreement/disagreement evidence.
4. Only then would capabilities currently marked `IMPLEMENTED_LOCAL_ONLY` in `docs/FEATURE_MATRIX.md` be promotable to `IMPLEMENTED_VERIFIED`.

## Funds / escrow

**NON-CUSTODIAL / NOT VERIFIED.** `fund_agreement` records an integer `funded_amount` as contract storage bookkeeping; no native-value transfer, payable method, or balance check against `gl.message.value` was implemented or exercised. Settlement (`settle`, `recover_inconclusive`) computes and records a deterministic allocation (`released_to_provider`/`refunded_to_buyer`/`retained`) but does not move real value. Do not read any amount in this contract's storage as a proof of custody.

## Source/commit record at time of writing this document

See `git log -1` in this repository for the exact commit this document was written against; this file will need updating (not silently left stale) if the contract source changes after a future deployment attempt, per the brief's "any source fix invalidates prior deployment-source evidence" rule.
