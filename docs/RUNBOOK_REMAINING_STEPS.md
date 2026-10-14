# Runbook: remaining Studionet steps

Both evaluation profiles have now been fully exercised live on Studio Network (see `docs/DEPLOYMENT.md`): API-delivery (`"2"` negative, `"4"` positive) and AI-agent-delivery (`"5"` positive, `"6"` an honest `UNVERIFIABLE`). What remains is small and optional:

**Contract:** `0x6bBcF7E85f8F07B54ba53ae2126E2E9F6485eE68` on `studionet` (chain id `61999`).

## 1. Complete agreement "6"'s refund (`recover_inconclusive`)

Agreement `"6"` is sitting in `RECOVERY_PENDING` with its full funded amount retained (nothing credited to either party — the correct, safe state for an `UNVERIFIABLE` verdict). Calling `recover_inconclusive("6")` (signed by either the buyer or provider of that agreement — their addresses are in `docs/DEPLOYMENT.md`, though those are disposable keys not persisted anywhere, so this would need a fresh `recover_inconclusive` call from whatever account currently has standing, or simply demonstrating the same call on a new test agreement) completes the refund. Already covered functionally by `tests/direct/test_speclock_security.py::test_unverifiable_overall_recovers_funds_without_awarding_either_party`.

## 2. Native escrow verification (capability #3)

Everything proven so far is bookkeeping settlement, not real value custody. Verifying actual GEN moving through a payable contract method would require implementing a `@gl.public.write.payable` method and testing it against a funded signer — a real scope addition, not just a lifecycle run, and not attempted in this pass.

## How to reproduce or extend the lifecycle tests already run

See `docs/DEPLOYMENT.md` "How real on-chain lifecycle execution was achieved" for the full method: `npm install genlayer-js` in a scratch directory, generate a fresh disposable buyer/provider pair with `createAccount()` per agreement, fund both from a wallet you control via `genlayer account send`, then run the full `create_agreement → accept_agreement → fund_agreement → freeze_agreement → submit_evidence → request_evaluation → finalize_verdict ×2 → settle` sequence in one script process (`createAccount()` never exposes a raw private key, so a generated account cannot be reused across separate process invocations — this is what stranded agreement `"3"` on an earlier deployment).
