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
    contract.fund_agreement(agreement_id)
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
    contract.fund_agreement(agreement_id)
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
    contract.fund_agreement(agreement_id)
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
    contract.fund_agreement(agreement_id)
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
    contract.fund_agreement(agreement_id)
    direct_vm.value = 0
    contract.freeze_agreement(agreement_id, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": "bad"})
    contract.request_evaluation(agreement_id)

    with direct_vm.expect_revert():
        contract.request_resubmission(agreement_id)


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
    contract.fund_agreement(agreement_id)
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


def test_fund_agreement_requires_real_value_not_a_claimed_amount(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Capability 3 (native escrow): fund_agreement is payable and derives
    its recorded amount from gl.message.value, not from a caller-supplied
    integer parameter that could claim an unbacked figure -- the old design
    this replaces. Sending zero value must be rejected."""
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

    direct_vm.value = 0
    with direct_vm.expect_revert():
        contract.fund_agreement(agreement_id)

    direct_vm.value = 250
    contract.fund_agreement(agreement_id)
    direct_vm.value = 0
    assert contract.get_agreement(agreement_id)["funded_amount"] == 250
    assert contract.get_agreement(agreement_id)["phase"] == "FUNDED"


def test_only_buyer_can_fund_even_with_real_value_sent(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "x", "priority": "required", "evidence_method": "http"}],
        1,
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.value = 100
    with direct_vm.expect_revert():
        contract.fund_agreement(agreement_id)  # bob is provider, not buyer
    direct_vm.value = 0


def test_appeal_requires_exact_bond_value(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Capability 29: the appeal bond is a real-value deterrent, not a
    counter. It must be exactly funded_amount // 10 (minimum 1) -- too
    little, too much, or zero are all rejected."""
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
    contract.fund_agreement(agreement_id)
    direct_vm.value = 0
    contract.freeze_agreement(agreement_id, False)
    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": "bad"})
    contract.request_evaluation(agreement_id)

    direct_vm.sender = direct_alice
    # Required bond is 1000 // 10 = 100.
    direct_vm.value = 50
    with direct_vm.expect_revert():
        contract.file_appeal(agreement_id, ["c1"], "too little bond")
    direct_vm.value = 0
    with direct_vm.expect_revert():
        contract.file_appeal(agreement_id, ["c1"], "no bond at all")
    direct_vm.value = 100
    contract.file_appeal(agreement_id, ["c1"], "exact bond")
    direct_vm.value = 0
    appeal = contract.get_appeal(contract.get_agreement(agreement_id)["latest_appeal_id"])
    assert appeal["resolution"] == "FILED_UNADJUDICATED"


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
    contract.fund_agreement(agreement_id)
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
