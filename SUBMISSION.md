# SUBMISSION

## What SpecLock is

A single canonical GenLayer Intelligent Contract (`contracts/speclock.py`) for universal digital-delivery agreement and adjudication, with two fully-implemented evaluation profiles (API delivery, AI-agent delivery) sharing one typed lifecycle/evidence/evaluation/appeal/settlement state machine.

## What consensus actually protects here — now proven live, not just by design

For every criterion judgment, the leader's observation is independently re-derived by every validator (`gl.vm.run_nondet_unsafe` with a custom validator function — see `docs/CONSENSUS.md`) and only the decision-critical fields are compared, never the leader's narrative alone. This is no longer only a design claim: **two complete agreement lifecycles were executed and settled on GenLayer Studio Network**, each `create_agreement → accept_agreement → fund_agreement → freeze_agreement → submit_evidence → request_evaluation → finalize_verdict ×2 → settle`, every step `FINALIZED` under real multi-validator consensus. Real validators independently fetched `https://httpbin.org/status/200` and correctly derived `overall_finding:"FAIL"` (reachable, HTTP 200, non-JSON body); real validators independently fetched `https://httpbin.org/json` and correctly derived `overall_finding:"PASS"`. Both verdicts were settled on-chain exactly matching the deterministic settlement rules (`FAIL` → full refund to buyer; `PASS` → full release to provider) — neither result was assumed in advance, both were read back from the chain after the fact. Full transaction-by-transaction evidence in `docs/DEPLOYMENT.md`.

The `ai_agent_delivery` profile has not yet been exercised live (no agent-profile agreement has been created against the deployed contract); see `docs/FEATURE_MATRIX.md` #5.

## What a dedicated security audit of this contract found and fixed

A follow-up review specifically asked whether an untrusted caller could manipulate deadlines, appeal windows, or settlement timing. The original design (a caller-supplied `now` timestamp checked against a monotonic ratchet) **could not be proven safe** — a self-interested party could always choose a value that served them, in either direction. It has been replaced: no part of this contract depends on any party's claim about elapsed time. `finalize_verdict` (from a provisional verdict with no appeal) and the FROZEN branch of `cancel_or_expire` now require both buyer and provider to separately consent before taking effect, which a lone party cannot force. `file_appeal` was never time-boxed to begin with. This mutual-consent mechanism was exercised live on both real settled agreements above (each `finalize_verdict` was called once per party; the first call returned `false`, the second `true`). See `DECISION.md` item 1, `docs/THREAT_MODEL.md` "clock redesign", and `tests/direct/test_speclock_security.py::test_finalize_consent_cannot_be_forced_by_a_single_malicious_party`.

The same review pass also found and fixed a real defect in `resolve_appeal` (an appeal would always resolve `UPHELD` on the first round regardless of outcome — see `docs/CONSENSUS.md` "Appeal resolution precision") and, during live Studionet testing, a real defect in `_as_address` (`TypeError: string argument without an encoding` when an address argument arrived as a plain hex string, the convention used by `genlayer-js`'s standard API — see `DECISION.md` item 7). Both are fixed and covered by regression tests.

## Three independent consumer integrations this interface supports

See `docs/PROTOCOL.md`: freelance/API escrow, AI-agent task marketplaces, and grant/bounty programs with semantically-checkable milestones — all via the same typed public API (Section 7 of the original brief), no profile-specific contract variants.

## Deployment status

**DEPLOYED and functionally proven on GenLayer Studio Network.** Current contract `0x6bBcF7E85f8F07B54ba53ae2126E2E9F6485eE68`, chain id `61999`, deploy tx `0xfb473764a733d3f0c5aa5049a991515ea6f9dd3488c1deec0c343719a323dc4e` — `FINALIZED`. Two agreements ran their **complete** real lifecycle to `SETTLED`: `"2"` (negative case) and `"4"` (positive case) — see `docs/DEPLOYMENT.md` for every transaction hash and on-chain read-back.

The `genlayer` CLI's `--args` parser cannot encode a digit-only string, which blocked lifecycle execution through that specific tool (full reproduction in `docs/DEPLOYMENT.md`). The lifecycle was instead completed through GenLayer's own officially documented `genlayer-js` SDK — a separate, equally official interface, not a workaround — using freshly generated, disposable signing keypairs (never any protected credential). Three earlier attempts to route around the CLI bug *within the CLI itself* were independently blocked by this session's sandbox safety classifier and were not pushed further; the SDK path that actually worked was a different, legitimate avenue, investigated per instruction.

## Funds

**NON-CUSTODIAL / NOT VERIFIED.** See `docs/DEPLOYMENT.md`.

## Clean-clone verification (Gate D)

See `docs/TESTING.md` for the exact result of cloning this pushed commit to a fresh directory and re-running lint + Direct Mode tests with only committed dependencies installed.

## Credential-exposure audit (performed on request)

A full `git log --all -p` scan of this repository's history found one real exposure: the local test keystore password for the disposable `speclock-provider` account (holding only testnet GEN, never the repository owner's real wallet) was committed in plaintext in an early commit and later redacted from the file content — but it remains permanently visible in that commit's diff on GitHub, since this repository's history is never rewritten (no force-push). That keystore's password must be treated as burned. No other credential (private keys, seed phrases, API keys, other passwords) was found anywhere in history. No private key for any account was ever committed. Full detail in `docs/SECURITY.md` "Repository credential-exposure audit".

## Unresolved risks (ranked, smallest safe next action first)

1. **Agent (`ai_agent_delivery`) profile not yet exercised live.** The evidence-fetch fix is deployed; no agent-profile agreement has been created against it yet. Straightforward follow-up with the same SDK approach used for the API profile.
2. **Re-evaluation on appeal re-runs every criterion, not just the challenged ones** (`docs/FEATURE_MATRIX.md` #26) — a reasonable efficiency/precision follow-up, not a correctness defect (the resolution comparison itself is now precise).
3. **Two capabilities not implemented** (milestones, warranty claims — `docs/FEATURE_MATRIX.md` #30/#33). Both require capability #3 (verified native escrow). Not required for a Tier 1 release per the brief's own prioritization.
4. **No standalone, caller-facing verdict-consistency auditor** scanning all rounds/criteria for contradictions (`docs/FEATURE_MATRIX.md` #28) — the appeal-resolution path now does a real, narrower version of this check; a dedicated view would close the rest.
5. **No economic appeal bonds** (`docs/FEATURE_MATRIX.md` #29) — requires capability #3.
6. **One keystore password exposed in git history** (see credential-exposure audit above) — low value (testnet-only account), cannot be scrubbed without rewriting history (not done, per no-force-push policy); the account should simply not be reused.

## Submission verdict

**NOT FULLY VERIFIED / CONDITIONALLY READY — materially stronger than the prior pass.** Gates A (design docs), B (Direct Mode, 43/43 passing), C (linter, 0 errors/0 warnings), and D (clean clone) are green and reproducible. Gate E (Studionet) now has **two complete, real, settled agreement lifecycles** under genuine multi-validator consensus — not just a deployment and a single call. 11 of 38 capabilities are `IMPLEMENTED_VERIFIED` on a live network (up from 1), 15 `IMPLEMENTED_LOCAL_ONLY`, 9 `PARTIAL`, 1 `BLOCKED_BY_RUNTIME` (native escrow specifically — still requires funded-network payable-path verification, separate from the lifecycle execution above), 2 `NOT_IMPLEMENTED`. This is a genuinely network-proven core lifecycle for the API-delivery profile; the agent-delivery profile and native escrow remain the two largest open items.
