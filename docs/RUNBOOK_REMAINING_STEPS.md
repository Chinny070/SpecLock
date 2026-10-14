# Runbook: remaining Studionet step — the agent (AI-delivery) profile

The API-delivery lifecycle has been fully executed and verified live (see `docs/DEPLOYMENT.md` — two complete, settled agreements, one `FAIL` and one `PASS`). The one remaining gap is the `ai_agent_delivery` profile, which has not yet been exercised against the live contract.

**Contract:** `0x6bBcF7E85f8F07B54ba53ae2126E2E9F6485eE68` on `studionet` (chain id `61999`).

## How to do it (either approach works)

**Option A — repeat the SDK approach used for the API profile** (see `docs/DEPLOYMENT.md` "How real on-chain lifecycle execution was achieved" for the full method): `npm install genlayer-js` in a scratch directory, generate a fresh disposable buyer/provider pair with `createAccount()`, fund both from a wallet you control via `genlayer account send`, then run the same `create_agreement → accept_agreement → fund_agreement → freeze_agreement → submit_evidence → request_evaluation → finalize_verdict ×2 → settle` sequence with `profile: "ai_agent_delivery"` and a criterion/evidence pair pointing at a real text artifact (e.g. a public gist or pastebin URL with some actual content to summarize/judge). Do the entire sequence in one script process — `createAccount()` never exposes a raw private key, so a generated account cannot be reused across separate process invocations (this is what stranded agreement `"3"` on the second deployment, documented in `docs/DEPLOYMENT.md`).

**Option B — GenLayer Studio web UI** (`https://studio.genlayer.com`), which has schema-driven call forms and isn't subject to the CLI's digit-string argument bug either.

## Recording results

Append whatever you execute (tx hashes, statuses, decoded return values, and the final `get_evaluation`/`get_settlement` reads) to `docs/DEPLOYMENT.md`, and promote capability #5's agent sub-profile in `docs/FEATURE_MATRIX.md` from `IMPLEMENTED_LOCAL_ONLY` to `IMPLEMENTED_VERIFIED` once done.
