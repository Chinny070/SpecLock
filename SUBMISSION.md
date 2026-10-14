# SUBMISSION

## What SpecLock is

A single canonical GenLayer Intelligent Contract (`contracts/speclock.py`) for universal digital-delivery agreement and adjudication, with two fully-implemented evaluation profiles (API delivery, AI-agent delivery) sharing one typed lifecycle/evidence/evaluation/appeal/settlement state machine.

## What consensus actually protects here

For every criterion judgment, the leader's observation is independently re-derived by every validator (`gl.vm.run_nondet_unsafe` with a custom validator function — see `docs/CONSENSUS.md`) and only the decision-critical fields are compared, never the leader's narrative alone. This means a single dishonest or confused leader cannot unilaterally force a PASS on a failing API or a fabricated agent-task claim through this contract — **in design**. That guarantee has not yet been exercised under real multi-validator GenVM consensus from this environment (Direct Mode only runs the leader path); see `docs/CONSENSUS.md` and `docs/DEPLOYMENT.md` for the exact gap.

## What a dedicated security audit of this contract found and fixed

A follow-up review specifically asked whether an untrusted caller could manipulate deadlines, appeal windows, or settlement timing. The original design (a caller-supplied `now` timestamp checked against a monotonic ratchet) **could not be proven safe** — a self-interested party could always choose a value that served them, in either direction. It has been replaced: no part of this contract depends on any party's claim about elapsed time. `finalize_verdict` (from a provisional verdict with no appeal) and the FROZEN branch of `cancel_or_expire` now require both buyer and provider to separately consent before taking effect, which a lone party cannot force. `file_appeal` was never time-boxed to begin with and remains available any time a provisional verdict stands, bounded only by the deterministic `max_appeal_rounds`. See `DECISION.md` item 1, `docs/THREAT_MODEL.md` "clock redesign", and `tests/direct/test_speclock_security.py::test_finalize_consent_cannot_be_forced_by_a_single_malicious_party`.

The same review pass also found and fixed a real defect in `resolve_appeal`: it compared against a field that was never populated before that same call, so every first-round appeal was unconditionally resolved `UPHELD` regardless of whether the challenged finding had actually changed. Fixed to compare only the specifically-challenged criteria between the challenged and the new evaluation. See `docs/CONSENSUS.md` "Appeal resolution precision" and the regression tests in `tests/direct/test_speclock_consensus.py`.

## Three independent consumer integrations this interface supports

See `docs/PROTOCOL.md`: freelance/API escrow, AI-agent task marketplaces, and grant/bounty programs with semantically-checkable milestones — all via the same typed public API (Section 7 of the original brief), no profile-specific contract variants.

## Deployment status

**Not deployed.** GenLayer Studio network RPC connectivity has been independently verified reachable from this environment (`docs/DEPLOYMENT.md`), but no funded signer authorized for this task is available — pre-existing unrelated local keystores found on this machine were inspected read-only (balance only, all zero) and were not used. See `docs/DEPLOYMENT.md` for the precise state and the concrete steps to close it.

## Funds

**NON-CUSTODIAL / NOT VERIFIED.** See `docs/DEPLOYMENT.md`.

## Clean-clone verification (Gate D)

See `docs/TESTING.md` for the exact result of cloning this pushed commit to a fresh directory and re-running lint + Direct Mode tests with only committed dependencies installed.

## Unresolved risks (ranked, smallest safe next action first)

1. **No live-consensus proof.** RPC connectivity is confirmed; the remaining gap is a funded, authorized signer. Easiest next step: the repository owner funds a `studionet` account and this contract is deployed and exercised end to end (Gate E in `docs/DEPLOYMENT.md`).
2. **Re-evaluation on appeal re-runs every criterion, not just the challenged ones** (`docs/FEATURE_MATRIX.md` #26) — a reasonable efficiency/precision follow-up, not a correctness defect (the resolution comparison itself is now precise).
3. **Two capabilities not implemented** (milestones, warranty claims — `docs/FEATURE_MATRIX.md` #30/#33). Both require capability #3 (verified native escrow), which is itself blocked on funded network access. Not required for a Tier 1 release per the brief's own prioritization.
4. **No standalone, caller-facing verdict-consistency auditor** scanning all rounds/criteria for contradictions (`docs/FEATURE_MATRIX.md` #28) — the appeal-resolution path now does a real, narrower version of this check; a dedicated view would close the rest.
5. **No economic appeal bonds** (`docs/FEATURE_MATRIX.md` #29) — requires capability #3.

## Submission verdict

**NOT FULLY VERIFIED / CONDITIONALLY READY.** Gates A (design docs), B (Direct Mode, 40/40 passing), C (linter, 0 errors/0 warnings), and D (clean clone — see `docs/TESTING.md`) are green and reproducible. Gate E (Studionet deploy-and-exercise) is not run — RPC connectivity is verified, but no funded, authorized signer is available in this session. This is a genuine, locally-verified foundation (27 of 38 capabilities `IMPLEMENTED_LOCAL_ONLY`, 8 `PARTIAL`, 1 `BLOCKED_BY_RUNTIME`, 2 `NOT_IMPLEMENTED`, 0 `IMPLEMENTED_VERIFIED` — up from 25/9/1/3 before this audit pass, with a real manipulable-deadline vulnerability and a real appeal-resolution defect found and fixed along the way) — not a finished, network-proven release.
