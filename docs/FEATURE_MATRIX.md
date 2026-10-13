# Feature matrix — 38 numbered capabilities

Status categories: `IMPLEMENTED_VERIFIED` (proven under live multi-validator consensus and/or a live network — none qualify yet, see `docs/DEPLOYMENT.md`), `IMPLEMENTED_LOCAL_ONLY` (real contract code + passing Direct Mode tests, not yet run under live consensus/network), `PARTIAL`, `BLOCKED_BY_RUNTIME`, `DEFERRED_FOR_SECURITY`, `NOT_IMPLEMENTED`.

| # | Capability | Status | Implementation | Test(s) | Blocker / next action |
|---|---|---|---|---|---|
| 1 | Natural-language agreement registration | IMPLEMENTED_LOCAL_ONLY | `create_agreement` | `test_speclock_lifecycle.py::test_create_accept_freeze_flow` | Live consensus run (Gate E). |
| 2 | Specification freeze | IMPLEMENTED_LOCAL_ONLY | `freeze_agreement`, `spec_fingerprint` | `test_create_accept_freeze_flow` | Gate E. |
| 3 | Native escrow and accounting | BLOCKED_BY_RUNTIME | `fund_agreement` records bookkeeping only; no payable method, no verified transfer | — | No funded signer/network access in this environment; see `docs/GENLAYER_CAPABILITIES.md`. Next: implement `@gl.public.write.payable`, verify `gl.message.value` on a funded testnet. |
| 4 | Independently verifiable web evidence | PARTIAL | `gl.nondet.web.get` used (not WebRender); mocked only | `test_speclock_api.py` (3 tests) | Never called against a live network from this environment. |
| 5 | Intelligent semantic delivery evaluation | IMPLEMENTED_LOCAL_ONLY | `_probe_api_criterion`, `_judge_agent_criterion` | `test_speclock_api.py`, `test_speclock_agent.py` | Gate E for real consensus. |
| 6 | Multi-criterion scoring | IMPLEMENTED_LOCAL_ONLY | `_derive_overall`, PARTIAL settlement math | `test_settlement_conservation_on_pass` | — |
| 7 | Cryptographic evidence commitments | IMPLEMENTED_LOCAL_ONLY | `content_digest`, `_evidence_snapshot_commitment` | `test_evidence_freezes_and_snapshot_is_immutable_after_evaluation` | — |
| 8 | Provisional verdict | IMPLEMENTED_LOCAL_ONLY | `PHASE_PROVISIONAL_VERDICT` | `test_api_positive_schema_consistent_response_passes` | — |
| 9 | Application-level appeal | IMPLEMENTED_LOCAL_ONLY | `file_appeal`, `resolve_appeal` | `test_appeal_window_must_be_open_to_file_and_closed_to_finalize` | — |
| 10 | Evidence freeze | IMPLEMENTED_LOCAL_ONLY | `_freeze_all_evidence` | `test_evidence_freezes_and_snapshot_is_immutable_after_evaluation` | — |
| 11 | Bounded re-evaluation | IMPLEMENTED_LOCAL_ONLY | `resolve_appeal` → `request_evaluation`, `max_appeal_rounds` | `test_appeal_replay_after_resolution_rejected` | — |
| 12 | Deadline enforcement | PARTIAL | Caller-supplied `now` + monotonic logical clock (`_advance_clock`), not a verified on-chain timestamp | `test_expired_after_deadline_refunds_in_full`, `test_clock_cannot_move_backward_or_jump_implausibly_far` | No native timestamp exists in the installed runner (`docs/GENLAYER_CAPABILITIES.md`); documented trust boundary, not a bug to "fix" without a different runtime capability. |
| 13 | Agreement-defined partial payments | IMPLEMENTED_LOCAL_ONLY | `settle()` PARTIAL branch | `test_settlement_conservation_on_pass` (PASS case); PARTIAL branch unit-covered by code path, not yet given its own dedicated test | Add an explicit PARTIAL-outcome settlement test. |
| 14 | Evidence-backed reputation | IMPLEMENTED_LOCAL_ONLY | `ReputationCounter`, `_update_reputation` | `test_reputation_only_updates_on_finalized_outcome` | — |
| 15 | Finality and duplicate-proof settlement | IMPLEMENTED_LOCAL_ONLY | `finalize_verdict`, `settle` guard | `test_settlement_conservation_on_pass` (double-settle rejected) | — |
| 16 | Structured specification compiler | IMPLEMENTED_LOCAL_ONLY | `_compile_criteria` (deterministic, rule-based) | `test_duplicate_criterion_ids_rejected`, `test_invalid_priority_enum_rejected` | — |
| 17 | Ambiguity/conflict detection before freeze | IMPLEMENTED_LOCAL_ONLY | Vague-term heuristic + `acknowledge_ambiguity` gate | `test_ambiguity_detected_before_freeze_and_blocks_without_ack` | Heuristic is a fixed keyword list, not full NLP ambiguity detection — reasonable for a deterministic gate, not exhaustive. |
| 18 | Evidence sufficiency classification | IMPLEMENTED_LOCAL_ONLY | `SUFFICIENCY_*` enum returned by both evaluators | `test_speclock_api.py`, `test_speclock_agent.py` | — |
| 19 | Multi-source corroboration / independence assessment | PARTIAL | Evidence list is passed to the judge, but there is no automatic "same submitter ⇒ not independent" upgrade/downgrade rule | `test_multiple_urls_same_control_not_auto_independent` (documents current behavior) | Add a deterministic independence pre-check (e.g. same-submitter flag passed into the judge prompt as a hint) as a follow-up. |
| 20 | Per-requirement verdicts | IMPLEMENTED_LOCAL_ONLY | `findings_json` array, one entry per criterion | `get_evaluation` return shape, all profile tests | — |
| 21 | Adversarial delivery checks | PARTIAL | Wrong-payload, SSRF, embedded-credential, malformed-JSON cases covered | `test_api_negative_200_with_wrong_payload_does_not_pass`, `test_evidence_url_blocked_schemes_and_hosts_rejected` | No forged-leader-under-real-consensus test (Gate E gap, see `docs/CONSENSUS.md`). |
| 22 | Failure attribution | PARTIAL | `ATTRIBUTION_*` enum; derivation is currently binary (`DELIVERY` on any FAIL finding, else `UNKNOWN`) — `EXTERNAL_DEPENDENCY`/`SPECIFICATION` are defined enum values not yet deterministically derived | `test_api_negative_200_with_wrong_payload_does_not_pass` asserts `DELIVERY` | Refine `_evaluate_api_profile`/`_evaluate_agent_profile` to derive `EXTERNAL_DEPENDENCY` from unreachable-host cases and `SPECIFICATION` from ambiguity-report-linked criteria. |
| 23 | Evidence-quality bands (not invented confidence) | IMPLEMENTED_LOCAL_ONLY | `SUFFICIENCY_*` bands only — no fabricated numeric confidence anywhere in the contract | code review of `_judge_agent_criterion`/`_probe_api_criterion` | — |
| 24 | Finding-specific verification challenges | IMPLEMENTED_LOCAL_ONLY | `file_appeal(challenged_finding_ids=...)` | `test_appeal_window_must_be_open_to_file_and_closed_to_finalize` | — |
| 25 | Bounded initial review / evidence appeal / exceptional procedural review | PARTIAL | Only one appeal tier implemented (`file_appeal`/`resolve_appeal`, capped by `max_appeal_rounds`); no separate "exceptional procedural review" tier | appeal tests above | A distinct procedural-review tier was judged not affordable/objectively-definable within this build's scope — honestly deferred rather than faked. |
| 26 | Deterministic appeal admissibility with semantic review only for irreducible questions | PARTIAL | Admissibility checks (window, round cap, known criterion ids) are fully deterministic; re-evaluation itself re-runs the full semantic judgment rather than a narrower "irreducible question only" review | same as #9 | Narrowing re-evaluation to only the challenged criteria (vs. re-running all) is a reasonable follow-up. |
| 27 | Evidence freeze and chain-of-custody receipts | IMPLEMENTED_LOCAL_ONLY | `EvidenceReceipt.status`, `_freeze_all_evidence` | `test_evidence_freezes_and_snapshot_is_immutable_after_evaluation` | — |
| 28 | Verdict consistency checks | NOT_IMPLEMENTED | No dedicated cross-evaluation consistency auditor beyond appeal upheld/rejected comparison | — | Would compare findings across resubmission/appeal rounds for the same criterion id and flag contradictions; not built in this pass. |
| 29 | Appeal spam/replay/bond protections | PARTIAL | Round cap + resolved-state guard implemented; no economic bond | `test_appeal_replay_after_resolution_rejected` | Economic bonds require verified native-value transfer (capability 3), which is itself blocked. |
| 30 | Milestones with independently frozen criteria and bounded count | NOT_IMPLEMENTED | — | — | One evaluation round per agreement currently; a milestone ledger (array of sub-agreements with their own criteria/evidence/settlement) is a real scope extension, not built in this pass. |
| 31 | Conditional settlement per pre-agreed rules | IMPLEMENTED_LOCAL_ONLY | `settle()` PASS/FAIL/PARTIAL/UNVERIFIABLE branches | `test_settlement_conservation_on_pass`, `test_unverifiable_overall_recovers_funds_without_awarding_either_party` | — |
| 32 | Limited remediation/resubmission window | IMPLEMENTED_LOCAL_ONLY | `request_resubmission`, `max_resubmissions` | `test_resubmission_budget_enforced` | — |
| 33 | Optional retained-funds warranty claims | NOT_IMPLEMENTED | — | — | Requires capability 3 (verified escrow) and an expiry/claim window design; deferred rather than faked. |
| 34 | Explainable machine-readable receipts | IMPLEMENTED_LOCAL_ONLY | `get_evaluation`, `get_evidence_receipt`, `get_settlement` all return structured dicts with findings/rationale | all profile/lifecycle tests | — |
| 35 | Bounded evidence-backed reputation | IMPLEMENTED_LOCAL_ONLY | Same as #14 (brief lists this capability twice, once under "Foundational" and once under "Transparency") | `test_reputation_only_updates_on_finalized_outcome` | — |
| 36 | Immutable evaluation-policy version binding | IMPLEMENTED_LOCAL_ONLY | `policy_id`/`policy_version` folded into `spec_fingerprint`, `get_policy_fingerprint` view | `test_create_accept_freeze_flow` | — |
| 37 | Deterministic/intelligent hybrid evaluation | IMPLEMENTED_LOCAL_ONLY | Core architecture — see `docs/PROTOCOL.md` | all tests | — |
| 38 | Reproducible deterministic replay and auditable intelligent evaluation lineage | PARTIAL | Deterministic state transitions are fully replayable from the stored `findings_json`/`evidence_snapshot_commitment`; a live web/LLM observation is explicitly documented as non-replayable once its source changes (module docstring, `docs/THREAT_MODEL.md`) | — | No dedicated replay-harness test was written (would re-run `_derive_overall`/`_settle` against a captured evaluation and assert identical output — straightforward follow-up). |

## Summary

- `IMPLEMENTED_LOCAL_ONLY`: 1,2,5,6,7,8,9,10,11,13,14,15,16,17,18,20,23,24,27,31,32,34,35,36,37 → **25**
- `PARTIAL`: 4,12,19,21,22,25,26,29,38 → **9**
- `BLOCKED_BY_RUNTIME`: 3 → **1**
- `NOT_IMPLEMENTED`: 28,30,33 → **3**
- `IMPLEMENTED_VERIFIED` (live-consensus/network proven): **0** — no live network run was performed (see `docs/DEPLOYMENT.md`).

25 + 9 + 1 + 3 = 38. This is not a "38/38 complete" claim — it is 25 capabilities with real, locally-tested code, 9 with a real but incomplete implementation, 1 blocked purely by lack of funded network access, and 3 honestly not built in this pass.
