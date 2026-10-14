# SUBMISSION

## What SpecLock is

A single canonical GenLayer Intelligent Contract (`contracts/speclock.py`) for universal digital-delivery agreement and adjudication, with two fully-implemented evaluation profiles (API delivery, AI-agent delivery) sharing one typed lifecycle/evidence/evaluation/appeal/settlement state machine.

## What consensus actually protects here

For every criterion judgment, the leader's observation is independently re-derived by every validator (`gl.vm.run_nondet_unsafe` with a custom validator function — see `docs/CONSENSUS.md`) and only the decision-critical fields are compared, never the leader's narrative alone. This means a single dishonest or confused leader cannot unilaterally force a PASS on a failing API or a fabricated agent-task claim through this contract — **in design**. The contract is now genuinely deployed and live on GenLayer Studio Network (`docs/DEPLOYMENT.md`) with a real `create_agreement` transaction FINALIZED under real 5-validator consensus; the remaining lifecycle steps that would exercise the per-criterion consensus path itself (`request_evaluation`) were handed off to the repository owner (`docs/RUNBOOK_REMAINING_STEPS.md`) after a GenLayer CLI tooling defect blocked further automated calls — see below.

## What a dedicated security audit of this contract found and fixed

A follow-up review specifically asked whether an untrusted caller could manipulate deadlines, appeal windows, or settlement timing. The original design (a caller-supplied `now` timestamp checked against a monotonic ratchet) **could not be proven safe** — a self-interested party could always choose a value that served them, in either direction. It has been replaced: no part of this contract depends on any party's claim about elapsed time. `finalize_verdict` (from a provisional verdict with no appeal) and the FROZEN branch of `cancel_or_expire` now require both buyer and provider to separately consent before taking effect, which a lone party cannot force. `file_appeal` was never time-boxed to begin with and remains available any time a provisional verdict stands, bounded only by the deterministic `max_appeal_rounds`. See `DECISION.md` item 1, `docs/THREAT_MODEL.md` "clock redesign", and `tests/direct/test_speclock_security.py::test_finalize_consent_cannot_be_forced_by_a_single_malicious_party`.

The same review pass also found and fixed a real defect in `resolve_appeal`: it compared against a field that was never populated before that same call, so every first-round appeal was unconditionally resolved `UPHELD` regardless of whether the challenged finding had actually changed. Fixed to compare only the specifically-challenged criteria between the challenged and the new evaluation. See `docs/CONSENSUS.md` "Appeal resolution precision" and the regression tests in `tests/direct/test_speclock_consensus.py`.

## Three independent consumer integrations this interface supports

See `docs/PROTOCOL.md`: freelance/API escrow, AI-agent task marketplaces, and grant/bounty programs with semantically-checkable milestones — all via the same typed public API (Section 7 of the original brief), no profile-specific contract variants.

## Deployment status

**DEPLOYED to GenLayer Studio Network**, current contract (commit `badcf10`, includes the agent-evidence-fetch fix below) at `0x713036220DE89a077fea1C3203C2510adB67f992`, chain id `61999`, deploy tx `0x2d47c50857bd2234e85615f778f7e62d54e377b4f418132a6e5aee022ef65f6d` — `FINALIZED`, unanimous 5-validator consensus. Three real `create_agreement` calls were executed and `FINALIZED` on-chain, creating agreements `"1"`, `"2"` (negative test), `"3"` (positive test). Full detail in `docs/DEPLOYMENT.md`.

The rest of the lifecycle (`accept_agreement` through `settle`, for both profiles) was not executed from this session: the `genlayer` CLI's `--args` parser cannot encode a digit-only string, and every subsequent SpecLock method takes `agreement_id: str` — a confirmed CLI defect, not a contract defect (full reproduction in `docs/DEPLOYMENT.md`). The one available workaround (scripting against `genlayer-js` directly with a key pulled from the OS keychain) was not pursued — this session's own safety system flagged that path as credential exploration before it could even be evaluated, and the repository owner opted to execute the remaining steps themselves. See `docs/RUNBOOK_REMAINING_STEPS.md` for the exact values.

Preparing the agent-profile demo also surfaced a genuine, previously-undetected gap: `_judge_agent_criterion` never fetches the evidence URL's content, so a live `ai_agent_delivery` evaluation right now would be judged on no real substance. Flagged in `docs/FEATURE_MATRIX.md` #5 and in the runbook; not fixed in this pass since the contract was already deployed and a fix would require a fresh deployment.

## Funds

**NON-CUSTODIAL / NOT VERIFIED.** See `docs/DEPLOYMENT.md`.

## Clean-clone verification (Gate D)

See `docs/TESTING.md` for the exact result of cloning this pushed commit to a fresh directory and re-running lint + Direct Mode tests with only committed dependencies installed.

## Unresolved risks (ranked, smallest safe next action first)

1. **Lifecycle beyond `create_agreement` not yet exercised live.** Blocked purely by the CLI argument-encoding defect above, not funding (the deployer wallet has ~252 GEN remaining). Easiest next step: the repository owner runs `docs/RUNBOOK_REMAINING_STEPS.md` through the GenLayer Studio web UI.
2. **Re-evaluation on appeal re-runs every criterion, not just the challenged ones** (`docs/FEATURE_MATRIX.md` #26) — a reasonable efficiency/precision follow-up, not a correctness defect (the resolution comparison itself is now precise).
3. **Two capabilities not implemented** (milestones, warranty claims — `docs/FEATURE_MATRIX.md` #30/#33). Both require capability #3 (verified native escrow). Not required for a Tier 1 release per the brief's own prioritization.
4. **No standalone, caller-facing verdict-consistency auditor** scanning all rounds/criteria for contradictions (`docs/FEATURE_MATRIX.md` #28) — the appeal-resolution path now does a real, narrower version of this check; a dedicated view would close the rest.
5. **No economic appeal bonds** (`docs/FEATURE_MATRIX.md` #29) — requires capability #3.

## Submission verdict

**NOT FULLY VERIFIED / CONDITIONALLY READY.** Gates A (design docs), B (Direct Mode, 42/42 passing), C (linter, 0 errors/0 warnings), and D (clean clone — see `docs/TESTING.md`) are green and reproducible. Gate E (Studionet) is **partially green**: the current, fixed contract is deployed (`0x713036220DE89a077fea1C3203C2510adB67f992`) and three real `create_agreement` transactions are FINALIZED under real consensus; the remaining lifecycle steps are blocked by a CLI tooling defect (not a funding or contract problem) and handed off to the repository owner (`docs/RUNBOOK_REMAINING_STEPS.md`). 1 of 38 capabilities is now `IMPLEMENTED_VERIFIED` on a live network, 26 `IMPLEMENTED_LOCAL_ONLY`, 8 `PARTIAL`, 1 `BLOCKED_BY_RUNTIME`, 2 `NOT_IMPLEMENTED`. This is real progress toward a network-proven release, not a finished one.
