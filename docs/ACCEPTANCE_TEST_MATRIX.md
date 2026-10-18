# Acceptance test matrix

Maps each required scenario (brief Section 13.3) to its actual test and result. Results are from the latest Gate B run recorded in `docs/TESTING.md` (103/103 passed; no skips).

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
| Appeal | A challenge creates filing, not instant reversal; filing is never time-boxed | `test_filing_appeal_is_never_time_boxed` | PASS |
| Appeal abuse | Replay/unauthorized rejected; resolution precision (a real bug — unconditional UPHELD on first round — was found and fixed) | `test_appeal_replay_after_resolution_rejected`, `test_appeal_rejected_when_challenged_finding_does_not_actually_change`, `test_appeal_upheld_when_challenged_finding_genuinely_changes` | PASS |
| Remediation | Resubmission only when permitted, never silently rewrites evidence | `test_resubmission_budget_enforced` | PASS |
| Deadline/evidence | Timely evidence evaluated permissionlessly after expiry; late evidence rejected; no-evidence expiry refunds | `test_delivery_deadline_evaluates_timely_evidence_and_rejects_late_evidence`, `test_no_evidence_expiry_refunds_permissionlessly_and_conserves_funds`, `test_permissionless_direct_evaluation_after_deadline_does_not_refund` | PASS in Direct Mode; live deployment pending |
| Resubmission deadline | Original deadline does not truncate a later resubmission window; exact boundary accepted, later evidence rejected; expired no-follow-up keeps prior verdict | `test_resubmission_uses_its_own_deadline_through_exact_boundary`, `test_expired_resubmission_without_new_evidence_restores_existing_verdict` | PASS in Direct Mode; live deployment pending |
| Milestone expiry | Relevant timely evidence is evaluated; evidence for another milestone cannot block an evidence-free milestone refund | `test_milestone_expiry_evaluates_relevant_evidence_and_refunds_only_empty_milestone`, `test_milestone_overdue_evaluation_rejects_unrelated_caller_before_deadline` | PASS in Direct Mode; live deployment pending |
| Finality | Protocol UNDETERMINED never counted as finalized verdict | Not independently exercised (no live network transaction observed) — guard logic is in place (`finalize_verdict` only runs from contract-internal state, never from external tx status) but this specific scenario needs a live network to truly demonstrate | DESIGNED, NOT LIVE-VERIFIED |
| Settlement | Payout follows frozen remedy exactly; conservation; no double claim | `test_settlement_conservation_on_pass` | PASS |
| Recovery | Every uncertain/expired fund-holding state has bounded recovery, and neither party can force it alone | `test_unverifiable_overall_recovers_funds_without_awarding_either_party`, `test_frozen_wind_down_requires_both_parties_consent` | PASS |
| Reputation | Only finalized outcomes update; no double-count | `test_reputation_only_updates_on_finalized_outcome` | PASS |
| Audit | Receipt binds agreement/policy/evidence/evaluation versions | `get_evaluation`/`get_agreement`/`get_policy_fingerprint` field assertions across tests | PASS |
| Replay | Deterministic steps reproducible; live observations labeled non-replayable | `test_speclock_consensus.py::test_deterministic_replay_of_settlement_math` | PASS |
| Privacy | No secrets/credentials exposed | `test_evidence_url_blocked_schemes_and_hosts_rejected` (embedded-credential URL rejected) | PASS |
| Resource safety | Maxima enforced for criteria/sources/text/output/appeals/pagination | `test_too_many_criteria_rejected`, `test_oversized_spec_text_rejected`, `test_evidence_cap_enforced` | PASS |
