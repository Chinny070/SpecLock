"""Security / resource-safety acceptance scenarios (Gate B).

Maps to docs/ACCEPTANCE_TEST_MATRIX.md rows: Parser, Resource safety,
Recovery, Reputation, Remediation.

No wall-clock time is used anywhere in this contract.
"""

import hashlib
import json

CONTRACT = "contracts/speclock.py"


def test_too_many_criteria_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    criteria = [{"id": f"c{i}", "description": "x", "priority": "required", "evidence_method": "http"} for i in range(40)]
    with direct_vm.expect_revert():
        contract.create_agreement(direct_bob, "api_delivery", "spec", criteria, 1)


def test_oversized_spec_text_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.create_agreement(
            direct_bob, "api_delivery", "x" * 30_000,
            [{"id": "c1", "description": "x", "priority": "required", "evidence_method": "http"}],
            1,
        )


def test_malformed_metadata_json_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "x", "priority": "required", "evidence_method": "http"}],
        1,
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    direct_vm.value = 10
    contract.fund_agreement(agreement_id, 10)
    direct_vm.value = 0
    contract.freeze_agreement(agreement_id, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    with direct_vm.expect_revert():
        contract.submit_evidence(agreement_id, "https://api.example.com/x", digest, "{not json")


def test_invalid_priority_enum_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.create_agreement(
            direct_bob, "api_delivery", "spec",
            [{"id": "c1", "description": "x", "priority": "urgent", "evidence_method": "http"}],
            1,
        )


def test_unsupported_profile_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.create_agreement(
            direct_bob, "website_delivery", "spec",
            [{"id": "c1", "description": "x", "priority": "required", "evidence_method": "http"}],
            1,
        )


def test_evidence_cap_enforced(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "x", "priority": "required", "evidence_method": "http"}],
        1,
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    direct_vm.value = 10
    contract.fund_agreement(agreement_id, 10)
    direct_vm.value = 0
    contract.freeze_agreement(agreement_id, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    for i in range(64):
        contract.submit_evidence(agreement_id, f"https://api.example.com/{i}", digest, "{}")
    with direct_vm.expect_revert():
        contract.submit_evidence(agreement_id, "https://api.example.com/overflow", digest, "{}")


def test_unverifiable_overall_recovers_funds_without_awarding_either_party(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "endpoint responds", "priority": "required", "evidence_method": "http:c1"}],
        1,
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    direct_vm.value = 777
    contract.fund_agreement(agreement_id, 777)
    direct_vm.value = 0
    contract.freeze_agreement(agreement_id, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 503, "body": ""})
    contract.request_evaluation(agreement_id)

    direct_vm.sender = direct_alice
    assert contract.finalize_verdict(agreement_id) is False
    direct_vm.sender = direct_bob
    assert contract.finalize_verdict(agreement_id) is True

    direct_vm.sender = direct_alice
    contract.settle(agreement_id)

    agreement = contract.get_agreement(agreement_id)
    assert agreement["phase"] == "RECOVERY_PENDING"
    settlement = contract.get_settlement(agreement_id)
    assert settlement["released_to_provider"] == 0
    assert settlement["refunded_to_buyer"] == 0
    assert settlement["retained"] == 777

    contract.recover_inconclusive(agreement_id)
    final_agreement = contract.get_agreement(agreement_id)
    assert final_agreement["phase"] == "REFUNDED"
    assert final_agreement["refunded_amount"] == 777


def test_reputation_only_updates_on_finalized_outcome(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    before = contract.get_reputation(direct_bob)
    assert before["finalized_outcomes"] == 0

    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "endpoint responds", "priority": "required", "evidence_method": "http:c1"}],
        1,
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    direct_vm.value = 100
    contract.fund_agreement(agreement_id, 100)
    direct_vm.value = 0
    contract.freeze_agreement(agreement_id, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"ok": True})})
    contract.request_evaluation(agreement_id)

    # Still provisional: reputation must not move yet.
    mid = contract.get_reputation(direct_bob)
    assert mid["finalized_outcomes"] == 0

    direct_vm.sender = direct_alice
    assert contract.finalize_verdict(agreement_id) is False
    mid2 = contract.get_reputation(direct_bob)
    assert mid2["finalized_outcomes"] == 0  # one-sided consent still must not finalize

    direct_vm.sender = direct_bob
    assert contract.finalize_verdict(agreement_id) is True
    after = contract.get_reputation(direct_bob)
    assert after["finalized_outcomes"] == 1
    assert after["pass_outcomes"] == 1


def test_resubmission_budget_enforced(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "endpoint responds", "priority": "required", "evidence_method": "http:c1"}],
        0,  # max_resubmissions = 0
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    direct_vm.value = 100
    contract.fund_agreement(agreement_id, 100)
    direct_vm.value = 0
    contract.freeze_agreement(agreement_id, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": "bad"})
    contract.request_evaluation(agreement_id)

    with direct_vm.expect_revert():
        contract.request_resubmission(agreement_id)


def test_resubmission_full_cycle_reaches_a_new_evaluation(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Regression test for a real defect found during a security audit:
    submit_evidence only advanced the phase FROZEN -> SUBMITTED, never
    RESUBMISSION_REQUESTED -> SUBMITTED, so after request_resubmission() the
    agreement (and its funded amount) was permanently stuck -- no further
    submit_evidence call could ever unblock request_evaluation again, which
    only accepts SUBMITTED/RE_EVALUATING. Fixed by also advancing the phase
    from RESUBMISSION_REQUESTED."""
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "endpoint responds", "priority": "required", "evidence_method": "http:c1"}],
        1,  # max_resubmissions = 1
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    direct_vm.value = 100
    contract.fund_agreement(agreement_id, 100)
    direct_vm.value = 0
    contract.freeze_agreement(agreement_id, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": "bad"})
    contract.request_evaluation(agreement_id)

    direct_vm.sender = direct_alice
    contract.request_resubmission(agreement_id)
    assert contract.get_agreement(agreement_id)["phase"] == "RESUBMISSION_REQUESTED"

    direct_vm.sender = direct_bob
    contract.submit_evidence(agreement_id, "https://api.example.com/health2", digest, json.dumps({"criterion_id": "c1"}))
    assert contract.get_agreement(agreement_id)["phase"] == "SUBMITTED"

    # Mocks match in first-registered order, and ".*health.*" would also
    # match "health2" -- clear and re-register rather than relying on the
    # new mock shadowing the old one (same pattern as elsewhere in this file).
    direct_vm.clear_mocks()
    direct_vm.mock_web(r".*api\.example\.com/health2.*", {"status": 200, "body": json.dumps({"ok": True})})
    evaluation_id2 = contract.request_evaluation(agreement_id)
    evaluation2 = contract.get_evaluation(evaluation_id2)
    assert evaluation2["overall_finding"] == "PASS"


def test_resubmission_requested_without_a_follow_up_can_still_be_wound_down(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Companion regression test: if request_resubmission is called but
    neither party ever submits new evidence, the agreement must still be
    recoverable via the same mutual-consent wind-down as a stalled FROZEN
    agreement -- not a second, narrower fund-lock trap."""
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "endpoint responds", "priority": "required", "evidence_method": "http:c1"}],
        1,
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    direct_vm.value = 100
    contract.fund_agreement(agreement_id, 100)
    direct_vm.value = 0
    contract.freeze_agreement(agreement_id, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": "bad"})
    contract.request_evaluation(agreement_id)

    direct_vm.sender = direct_alice
    contract.request_resubmission(agreement_id)

    contract.cancel_or_expire(agreement_id)
    assert contract.get_agreement(agreement_id)["phase"] == "RESUBMISSION_REQUESTED"
    direct_vm.sender = direct_bob
    contract.cancel_or_expire(agreement_id)

    agreement = contract.get_agreement(agreement_id)
    assert agreement["phase"] == "EXPIRED"
    settlement = contract.get_settlement(agreement_id)
    assert settlement["refunded_to_buyer"] == 100


def test_finalize_consent_cannot_be_forced_by_a_single_malicious_party(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Core manipulation-resistance proof for the redesigned finalize gate:
    an interested single party (here, the buyer who wants to deny the
    provider's payout) cannot transition the agreement to FINALIZED alone,
    no matter what value they might have supplied under the old caller-time
    design. The only escalation path available to a lone party is
    file_appeal, which is itself unbounded by any unverifiable timestamp and
    capped purely by `max_appeal_rounds`."""
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "endpoint responds", "priority": "required", "evidence_method": "http:c1"}],
        1,
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    direct_vm.value = 100
    contract.fund_agreement(agreement_id, 100)
    direct_vm.value = 0
    contract.freeze_agreement(agreement_id, False)
    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"ok": True})})
    contract.request_evaluation(agreement_id)

    direct_vm.sender = direct_alice
    contract.finalize_verdict(agreement_id)
    for _ in range(5):
        with direct_vm.expect_revert():
            contract.finalize_verdict(agreement_id)
    assert contract.get_agreement(agreement_id)["phase"] == "PROVISIONAL_VERDICT"
    with direct_vm.expect_revert():
        contract.settle(agreement_id)


def test_check_verdict_consistency_reports_changed_criteria_across_rounds(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Capability 28: a standalone, caller-facing consistency auditor
    scanning every evaluation round, not just the two rounds either side of
    one appeal."""
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "endpoint responds", "priority": "required", "evidence_method": "http:c1"}],
        1,
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    direct_vm.value = 1000
    contract.fund_agreement(agreement_id, 1000)
    direct_vm.value = 0
    contract.freeze_agreement(agreement_id, False)
    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": "bad"})
    contract.request_evaluation(agreement_id)

    before = contract.check_verdict_consistency(agreement_id)
    assert before["total_rounds"] == 1
    assert before["any_contradiction_detected"] is False

    direct_vm.sender = direct_alice
    direct_vm.value = 100
    contract.file_appeal(agreement_id, ["c1"], "disagree")
    direct_vm.value = 0
    direct_vm.clear_mocks()
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"ok": True})})
    contract.resolve_appeal(agreement_id)

    after = contract.check_verdict_consistency(agreement_id)
    assert after["total_rounds"] == 2
    assert after["any_contradiction_detected"] is True
    assert "c1" in after["changed_criteria"]
    assert [entry["finding"] for entry in after["findings_by_criterion"]["c1"]] == ["FAIL", "PASS"]


# ---------------------------------------------------------------------------
# Native-value escrow: fund_agreement is payable, settle()/recover_inconclusive
# credit a pull-payment `claimable` balance, and withdraw() pays it out via
# the EVM-layer `_EthAccount` proxy. Direct Mode cannot move real GEN
# (emit_transfer is a protocol no-op here), so these tests assert the
# deterministic accounting and call-path behavior exactly as agentcourt's
# `tests/direct/test_native_escrow.py` does for the identical pattern; real
# end-to-end value movement is a Studionet concern (see docs/DEPLOYMENT.md).
# ---------------------------------------------------------------------------

def _setup_funded_api_agreement(contract, direct_vm, buyer, provider, amount=1000):
    direct_vm.sender = buyer
    agreement_id = contract.create_agreement(
        provider, "api_delivery", "spec",
        [{"id": "c1", "description": "endpoint responds", "priority": "required", "evidence_method": "http:c1"}],
        1,
    )
    direct_vm.sender = provider
    contract.accept_agreement(agreement_id)
    direct_vm.sender = buyer
    direct_vm.value = amount
    contract.fund_agreement(agreement_id, amount)
    direct_vm.value = 0
    contract.freeze_agreement(agreement_id, False)
    return agreement_id


def test_fund_agreement_requires_sent_value_to_match_declared_amount(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "endpoint responds", "priority": "required", "evidence_method": "http:c1"}],
        1,
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    direct_vm.value = 1  # claims 1000 but sends only 1
    with direct_vm.expect_revert():
        contract.fund_agreement(agreement_id, 1000)
    direct_vm.value = 0
    assert contract.get_agreement(agreement_id)["phase"] == "ACCEPTED"


def test_settle_on_pass_credits_provider_claimable_not_buyer(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    from genlayer.py.types import Address
    agreement_id = _setup_funded_api_agreement(contract, direct_vm, direct_alice, direct_bob, amount=1000)
    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"ok": True})})
    contract.request_evaluation(agreement_id)
    direct_vm.sender = direct_alice
    assert contract.finalize_verdict(agreement_id) is False
    direct_vm.sender = direct_bob
    assert contract.finalize_verdict(agreement_id) is True
    contract.settle(agreement_id)

    assert contract.get_claimable(str(Address(bytes(direct_bob)))) == 1000
    assert contract.get_claimable(str(Address(bytes(direct_alice)))) == 0


def test_withdraw_zeroes_claimable_and_returns_amount(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    from genlayer.py.types import Address
    agreement_id = _setup_funded_api_agreement(contract, direct_vm, direct_alice, direct_bob, amount=1000)
    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"ok": True})})
    contract.request_evaluation(agreement_id)
    direct_vm.sender = direct_alice
    assert contract.finalize_verdict(agreement_id) is False
    direct_vm.sender = direct_bob
    assert contract.finalize_verdict(agreement_id) is True
    contract.settle(agreement_id)

    withdrawn = contract.withdraw()
    assert withdrawn == 1000
    assert contract.get_claimable(str(Address(bytes(direct_bob)))) == 0

    with direct_vm.expect_revert():
        contract.withdraw()


def test_withdraw_with_nothing_claimable_reverts(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.withdraw()


def test_recover_inconclusive_credits_buyer_claimable(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    from genlayer.py.types import Address
    agreement_id = _setup_funded_api_agreement(contract, direct_vm, direct_alice, direct_bob, amount=500)
    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 503, "body": ""})
    contract.request_evaluation(agreement_id)
    direct_vm.sender = direct_alice
    assert contract.finalize_verdict(agreement_id) is False
    direct_vm.sender = direct_bob
    assert contract.finalize_verdict(agreement_id) is True
    contract.settle(agreement_id)
    assert contract.get_agreement(agreement_id)["phase"] == "RECOVERY_PENDING"
    assert contract.get_claimable(str(Address(bytes(direct_alice)))) == 0

    contract.recover_inconclusive(agreement_id)
    assert contract.get_agreement(agreement_id)["phase"] == "REFUNDED"
    assert contract.get_claimable(str(Address(bytes(direct_alice)))) == 500


def test_appeal_requires_exact_bond_value(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_funded_api_agreement(contract, direct_vm, direct_alice, direct_bob, amount=1000)
    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": "bad"})
    contract.request_evaluation(agreement_id)

    direct_vm.sender = direct_alice
    direct_vm.value = 1  # required bond is 100 (1000 // 10)
    with direct_vm.expect_revert():
        contract.file_appeal(agreement_id, ["c1"], "disagree")
    direct_vm.value = 0
    assert contract.get_agreement(agreement_id)["phase"] == "PROVISIONAL_VERDICT"


def test_appeal_bond_credited_to_appellant_on_upheld(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    from genlayer.py.types import Address
    agreement_id = _setup_funded_api_agreement(contract, direct_vm, direct_alice, direct_bob, amount=1000)
    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": "bad"})
    contract.request_evaluation(agreement_id)

    direct_vm.sender = direct_alice
    direct_vm.value = 100
    contract.file_appeal(agreement_id, ["c1"], "the endpoint actually returns valid JSON")
    direct_vm.value = 0
    direct_vm.clear_mocks()
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"ok": True})})
    contract.resolve_appeal(agreement_id)

    appeal = contract.get_appeal(contract.get_agreement(agreement_id)["latest_appeal_id"])
    assert appeal["resolution"] == "UPHELD"
    assert contract.get_claimable(str(Address(bytes(direct_alice)))) == 100


def test_appeal_bond_credited_to_other_party_on_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    from genlayer.py.types import Address
    agreement_id = _setup_funded_api_agreement(contract, direct_vm, direct_alice, direct_bob, amount=1000)
    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": "bad"})
    contract.request_evaluation(agreement_id)

    direct_vm.sender = direct_alice
    direct_vm.value = 100
    contract.file_appeal(agreement_id, ["c1"], "disagree")
    direct_vm.value = 0
    # Same mock, unchanged -- c1 will fail again on re-evaluation, so the
    # appeal is REJECTED and the bond goes to the other party (the provider).
    contract.resolve_appeal(agreement_id)

    appeal = contract.get_appeal(contract.get_agreement(agreement_id)["latest_appeal_id"])
    assert appeal["resolution"] == "REJECTED"
    assert contract.get_claimable(str(Address(bytes(direct_alice)))) == 0
    assert contract.get_claimable(str(Address(bytes(direct_bob)))) == 100
