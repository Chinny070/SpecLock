# SUBMISSION

## What SpecLock is

A single canonical GenLayer Intelligent Contract (`contracts/speclock.py`) for universal digital-delivery agreement and adjudication, with two fully-implemented evaluation profiles (API delivery, AI-agent delivery) sharing one typed lifecycle/evidence/evaluation/appeal/settlement state machine.

## What consensus actually protects here

For every criterion judgment, the leader's observation is independently re-derived by every validator (`gl.vm.run_nondet_unsafe` with a custom validator function — see `docs/CONSENSUS.md`) and only the decision-critical fields are compared, never the leader's narrative alone. This means a single dishonest or confused leader cannot unilaterally force a PASS on a failing API or a fabricated agent-task claim through this contract — **in design**. That guarantee has not yet been exercised under real multi-validator GenVM consensus from this environment (Direct Mode only runs the leader path); see `docs/CONSENSUS.md` and `docs/DEPLOYMENT.md` for the exact gap.

## Three independent consumer integrations this interface supports

See `docs/PROTOCOL.md`: freelance/API escrow, AI-agent task marketplaces, and grant/bounty programs with semantically-checkable milestones — all via the same typed public API (Section 7 of the original brief), no profile-specific contract variants.

## Deployment status

**Not deployed.** No funded signer or network RPC access was available in this session. See `docs/DEPLOYMENT.md` for the precise blocker and the concrete steps to close it.

## Funds

**NON-CUSTODIAL / NOT VERIFIED.** See `docs/DEPLOYMENT.md`.

## Unresolved risks (ranked, smallest safe next action first)

1. **No live-consensus proof.** Easiest next step: provision Studio/testnet RPC + a funded signer and run the existing contract + evidence flows end to end (Gate E in `docs/DEPLOYMENT.md`).
2. **Logical-clock griefing surface** (any time-gated caller can advance the shared clock, within a 10-year bound) — documented in `docs/THREAT_MODEL.md`. A smaller bound or a per-agreement (rather than contract-wide) clock would reduce blast radius; deferred as a design trade-off, not an oversight.
3. **Three capabilities not implemented** (milestones, warranty claims, cross-round consistency auditor — `docs/FEATURE_MATRIX.md` #28/30/33). None are required for Tier 1 release per the brief's own prioritization.
4. **No clean-clone verification performed** (`docs/TESTING.md` Gate D) — straightforward to close post-push.
5. **Failure attribution is coarse** (binary DELIVERY/UNKNOWN rather than the full `ATTRIBUTION_*` enum) — `docs/FEATURE_MATRIX.md` #22.

## Submission verdict

**NOT FULLY VERIFIED / CONDITIONALLY READY.** Gates A (design docs) and B (Direct Mode, 32/32 passing) and C (linter, 0 errors/0 warnings) are green and reproducible. Gates D (clean clone) and E (Studionet) are not run — D for time, E because no network/funds were available or authorized in this session. This is a genuine, locally-verified Tier 1 foundation (25 of 38 capabilities `IMPLEMENTED_LOCAL_ONLY`, 9 `PARTIAL`, 1 `BLOCKED_BY_RUNTIME`, 3 `NOT_IMPLEMENTED`, 0 `IMPLEMENTED_VERIFIED`) — not a finished, network-proven release.
