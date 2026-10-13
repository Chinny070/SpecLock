# Acceptance test matrix

Maps each required scenario (brief Section 13.3) to its actual test and result. All results are from the Gate B run recorded in `docs/TESTING.md` (32/32 passed).

| Area | Required scenario | Test | Result |
|---|---|---|---|
| Agreement | Authorized buyer creates; wrong actor cannot accept; acceptance freezes terms | `test_create_accept_freeze_flow`, `test_wrong_actor_cannot_accept` | PASS |
| Compiler | Bounded structured criteria; ambiguous/contradictory flagged before freeze | `test_ambiguity_detected_before_freeze_and_blocks_without_ack` | PASS |
| Policy | Existing agreement pinned to original fingerprint | `test_create_accept_freeze_flow` (`get_policy_fingerprint` assertion) | PASS |
| API positive | Independently observed artifact satisfies checks | `test_api_positive_schema_consistent_response_passes` | PASS |
| API negative | 200 with false payload does not pass | `test_api_negative_200_with_wrong_payload_does_not_pass` | PASS |
| API uncertain | Unreachable host → UNVERIFIABLE, not fabricated | `test_api_uncertain_unreachable_host_is_unverifiable` | PASS |
| Agent positive | Public/revealed output satisfies frozen task | `test_agent_positive_compliant_output_passes` | PASS |
| Agent negative | Hallucinated/unauthorized output prevents acceptance | `test_agent_negative_hallucinated_citation_fails` | PASS |
| Agent uncertain | Inaccessible/malformed trace does not produce PASS | `test_agent_uncertain_malformed_llm_output_is_unverifiable_not_fabricated`, `test_agent_missing_artifact_without_independent_evidence_is_unverifiable` | PASS |
| Evidence | Immutable snapshot after evaluation begins | `test_evidence_freezes_and_snapshot_is_immutable_after_evaluation` | PASS |
| Independence | Same-submitter URLs not auto-corroborated | `test_multiple_urls_same_control_not_auto_independent` | PASS (documents current PARTIAL behavior, see `docs/FEATURE_MATRIX.md` #19) |
| Consensus | Forged leader PASS with failing criterion rejected by independent validator work | **NOT TESTED under real consensus** | Direct Mode cannot exercise this — see `docs/CONSENSUS.md` "What is NOT verified". `validator_fn` closures exist and are reachable for a future integration test. |
| Equivalence | PASS vs FAIL on critical criterion not equivalent | `_derive_overall` logic, exercised by all profile tests (a FAIL finding always drives overall FAIL for required criteria) | PASS |
| Parser | Invalid JSON, unknown enums, duplicated criteria, oversized response fail closed | `test_malformed_metadata_json_rejected`, `test_invalid_priority_enum_rejected`, `test_duplicate_criterion_ids_rejected`, `test_oversized_spec_text_rejected`, `test_agent_uncertain_malformed_llm_output_is_unverifiable_not_fabricated` | PASS |
| State | Unauthorized/out-of-order transitions reject without mutation | `test_unauthorized_or_out_of_order_transition_does_not_mutate_state` | PASS |
| Appeal | Timely challenge creates filing, not instant reversal | `test_appeal_window_must_be_open_to_file_and_closed_to_finalize` | PASS |
| Appeal abuse | Replay/expired/unauthorized rejected | `test_appeal_replay_after_resolution_rejected` | PASS |
| Remediation | Resubmission only when permitted, never silently rewrites evidence | `test_resubmission_budget_enforced` | PASS |
| Finality | Protocol UNDETERMINED never counted as finalized verdict | Not independently exercised (no live network transaction observed) — guard logic is in place (`finalize_verdict` only runs from contract-internal state, never from external tx status) but this specific scenario needs a live network to truly demonstrate | DESIGNED, NOT LIVE-VERIFIED |
| Settlement | Payout follows frozen remedy exactly; conservation; no double claim | `test_settlement_conservation_on_pass` | PASS |
| Recovery | Every uncertain/expired fund-holding state has bounded recovery | `test_unverifiable_overall_recovers_funds_without_awarding_either_party`, `test_expired_after_deadline_refunds_in_full` | PASS |
| Reputation | Only finalized outcomes update; no double-count | `test_reputation_only_updates_on_finalized_outcome` | PASS |
| Audit | Receipt binds agreement/policy/evidence/evaluation versions | `get_evaluation`/`get_agreement`/`get_policy_fingerprint` field assertions across tests | PASS |
| Replay | Deterministic steps reproducible; live observations labeled non-replayable | Documented in `contracts/speclock.py` module docstring and `docs/THREAT_MODEL.md`; no dedicated replay-harness test written (see `docs/FEATURE_MATRIX.md` #38) | DOCUMENTED, NOT SEPARATELY TESTED |
| Privacy | No secrets/credentials exposed | `test_evidence_url_blocked_schemes_and_hosts_rejected` (embedded-credential URL rejected) | PASS |
| Resource safety | Maxima enforced for criteria/sources/text/output/appeals/pagination | `test_too_many_criteria_rejected`, `test_oversized_spec_text_rejected`, `test_evidence_cap_enforced` | PASS |
