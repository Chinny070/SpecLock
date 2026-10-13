# Testing

## Environment

- Python 3.12.10, `genvm-linter` 0.11.1rc2, `genlayer-test` 0.29.2 (`gltest`, pytest 8.4.2), `genlayer-py` 0.16.3.
- GenLayer SDK (`genlayer.gl`, `genlayer.py`) auto-downloaded by both tools from `genlayerlabs/genvm` GitHub releases on first use; cached locally. Runner pinned in the contract header: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.

## Gate B — Direct Mode (reproducible: `gltest tests/direct/ -v`)

```
============================= test session starts =============================
collected 32 items

tests/direct/test_speclock_agent.py::test_agent_positive_compliant_output_passes PASSED
tests/direct/test_speclock_agent.py::test_agent_negative_hallucinated_citation_fails PASSED
tests/direct/test_speclock_agent.py::test_agent_uncertain_malformed_llm_output_is_unverifiable_not_fabricated PASSED
tests/direct/test_speclock_agent.py::test_agent_missing_artifact_without_independent_evidence_is_unverifiable PASSED
tests/direct/test_speclock_agent.py::test_multiple_urls_same_control_not_auto_independent PASSED
tests/direct/test_speclock_api.py::test_api_positive_schema_consistent_response_passes PASSED
tests/direct/test_speclock_api.py::test_api_negative_200_with_wrong_payload_does_not_pass PASSED
tests/direct/test_speclock_api.py::test_api_uncertain_unreachable_host_is_unverifiable PASSED
tests/direct/test_speclock_api.py::test_missing_evidence_for_criterion_is_unverifiable_not_fail PASSED
tests/direct/test_speclock_api.py::test_evidence_url_blocked_schemes_and_hosts_rejected PASSED
tests/direct/test_speclock_api.py::test_evidence_freezes_and_snapshot_is_immutable_after_evaluation PASSED
tests/direct/test_speclock_api.py::test_settlement_conservation_on_pass PASSED
tests/direct/test_speclock_api.py::test_appeal_window_must_be_open_to_file_and_closed_to_finalize PASSED
tests/direct/test_speclock_api.py::test_appeal_replay_after_resolution_rejected PASSED
tests/direct/test_speclock_lifecycle.py::test_create_accept_freeze_flow PASSED
tests/direct/test_speclock_lifecycle.py::test_wrong_actor_cannot_accept PASSED
tests/direct/test_speclock_lifecycle.py::test_only_buyer_can_create_mismatched_provider_rejected PASSED
tests/direct/test_speclock_lifecycle.py::test_ambiguity_detected_before_freeze_and_blocks_without_ack PASSED
tests/direct/test_speclock_lifecycle.py::test_duplicate_criterion_ids_rejected PASSED
tests/direct/test_speclock_lifecycle.py::test_unauthorized_or_out_of_order_transition_does_not_mutate_state PASSED
tests/direct/test_speclock_lifecycle.py::test_cancel_before_funding_by_party PASSED
tests/direct/test_speclock_lifecycle.py::test_expired_after_deadline_refunds_in_full PASSED
tests/direct/test_speclock_lifecycle.py::test_clock_cannot_move_backward_or_jump_implausibly_far PASSED
tests/direct/test_speclock_security.py::test_too_many_criteria_rejected PASSED
tests/direct/test_speclock_security.py::test_oversized_spec_text_rejected PASSED
tests/direct/test_speclock_security.py::test_malformed_metadata_json_rejected PASSED
tests/direct/test_speclock_security.py::test_invalid_priority_enum_rejected PASSED
tests/direct/test_speclock_security.py::test_unsupported_profile_rejected PASSED
tests/direct/test_speclock_security.py::test_evidence_cap_enforced PASSED
tests/direct/test_speclock_security.py::test_unverifiable_overall_recovers_funds_without_awarding_either_party PASSED
tests/direct/test_speclock_security.py::test_reputation_only_updates_on_finalized_outcome PASSED
tests/direct/test_speclock_security.py::test_resubmission_budget_enforced PASSED

============================= 32 passed in 7.45s ==============================
```

32/32 passed, 0 skipped, 0 failed. Order-independence was not separately verified with `-p no:randomly` (no such plugin installed) but tests do not share module-level mutable state — each test calls `direct_deploy` for a fresh contract instance.

Three real bugs were caught and fixed by this test suite during development (not merely passed on the first attempt):
1. `gl.message.sender_account` does not exist (`AttributeError`) — corrected to `gl.message.sender_address` throughout.
2. `recover_inconclusive` originally retained the already-retained amount again instead of refunding it (conservation math was self-consistent but the refund was silently zero) — caught by `test_unverifiable_overall_recovers_funds_without_awarding_either_party`.
3. Address-typed parameters arriving as raw `bytes` after the Direct Mode calldata round-trip — fixed with `_as_address()` coercion.

## Gate C — GenVM linter (reproducible: `genvm-lint check contracts/speclock.py` and `genvm-lint validate contracts/speclock.py`)

```
✓ Lint passed (3 checks)
✓ Validation passed
  Contract: SpecLock
  Methods: 26 (13 view, 13 write)
  ℹ py-genlayer: a newer runner is available (babwp9t37jw9g4j2bccgn14g6x7x9s1f7dsmh7emvz735pz4zxa0). See https://github.com/genlayerlabs/genvm-manager/releases for changes.
```

0 errors, 0 warnings. (The "newer runner available" line is informational, not an error; the contract intentionally pins the hash given in the `genlayer-dev:write-contract` skill rather than tracking `latest`, per that skill's explicit instruction never to use unpinned/`latest` runner aliases.)

## Gate D — Clean clone

**Not run in this session.** A clean-clone check (clone to a fresh path, install only committed dependencies, rerun the two commands above) was not performed because doing so would require pushing first and re-cloning from GitHub, and this session prioritized getting Gates B/C fully green before spending the remaining time on documentation and the push itself. This is a real gap: run `git clone https://github.com/Chinny070/SpecLock /tmp/speclock-clean && cd /tmp/speclock-clean && pip install genlayer-test genvm-linter && genvm-lint check contracts/speclock.py && gltest tests/direct/ -v` to close it.

## Gate E — Studionet

**BLOCKED.** No GenLayer network RPC URL, signer, or funded account was available or supplied in this session. See `docs/DEPLOYMENT.md` for the exact state.

## Integration tests (`tests/integration/`)

Not written in this pass — they require Gate E connectivity to be meaningful (an integration test against glsim alone would just re-exercise what Direct Mode already covers, since glsim per its own description "executes contracts via the direct mode engine" rather than real multi-validator GenVM consensus). A placeholder is intentionally not committed as an empty file per the brief's "do not create empty placeholder files" instruction; this is recorded as a gap here instead.
