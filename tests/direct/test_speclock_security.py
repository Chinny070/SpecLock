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
    contract.fund_agreement(agreement_id, 10)
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
    contract.fund_agreement(agreement_id, 10)
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
    contract.fund_agreement(agreement_id, 777)
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
    contract.fund_agreement(agreement_id, 100)
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
    contract.fund_agreement(agreement_id, 100)
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
    contract.fund_agreement(agreement_id, 100)
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
