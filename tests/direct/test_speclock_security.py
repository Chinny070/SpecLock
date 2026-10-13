"""Security / resource-safety acceptance scenarios (Gate B).

Maps to docs/ACCEPTANCE_TEST_MATRIX.md rows: Parser, Resource safety,
Recovery, Reputation, Remediation.
"""

import hashlib
import json

CONTRACT = "contracts/speclock.py"
T0 = 1_700_000_000


def test_too_many_criteria_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    criteria = [{"id": f"c{i}", "description": "x", "priority": "required", "evidence_method": "http"} for i in range(40)]
    with direct_vm.expect_revert():
        contract.create_agreement(direct_bob, "api_delivery", "spec", criteria, 3600, 600, 1, T0)


def test_oversized_spec_text_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.create_agreement(
            direct_bob, "api_delivery", "x" * 30_000,
            [{"id": "c1", "description": "x", "priority": "required", "evidence_method": "http"}],
            3600, 600, 1, T0,
        )


def test_malformed_metadata_json_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "x", "priority": "required", "evidence_method": "http"}],
        3600, 600, 1, T0,
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    contract.fund_agreement(agreement_id, 10)
    contract.freeze_agreement(agreement_id, T0 + 1, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    with direct_vm.expect_revert():
        contract.submit_evidence(agreement_id, "https://api.example.com/x", digest, "{not json", T0 + 2)


def test_invalid_priority_enum_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.create_agreement(
            direct_bob, "api_delivery", "spec",
            [{"id": "c1", "description": "x", "priority": "urgent", "evidence_method": "http"}],
            3600, 600, 1, T0,
        )


def test_unsupported_profile_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.create_agreement(
            direct_bob, "website_delivery", "spec",
            [{"id": "c1", "description": "x", "priority": "required", "evidence_method": "http"}],
            3600, 600, 1, T0,
        )


def test_evidence_cap_enforced(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "x", "priority": "required", "evidence_method": "http"}],
        3600, 600, 1, T0,
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    contract.fund_agreement(agreement_id, 10)
    contract.freeze_agreement(agreement_id, T0 + 1, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    for i in range(64):
        contract.submit_evidence(agreement_id, f"https://api.example.com/{i}", digest, "{}", T0 + 2 + i)
    with direct_vm.expect_revert():
        contract.submit_evidence(agreement_id, "https://api.example.com/overflow", digest, "{}", T0 + 200)


def test_unverifiable_overall_recovers_funds_without_awarding_either_party(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "endpoint responds", "priority": "required", "evidence_method": "http:c1"}],
        3600, 600, 1, T0,
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    contract.fund_agreement(agreement_id, 777)
    contract.freeze_agreement(agreement_id, T0 + 1, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}), T0 + 2)
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 503, "body": ""})
    contract.request_evaluation(agreement_id, T0 + 10)

    direct_vm.sender = direct_alice
    contract.finalize_verdict(agreement_id, T0 + 10_000)
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
        3600, 600, 1, T0,
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    contract.fund_agreement(agreement_id, 100)
    contract.freeze_agreement(agreement_id, T0 + 1, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}), T0 + 2)
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"ok": True})})
    contract.request_evaluation(agreement_id, T0 + 10)

    # Still provisional: reputation must not move yet.
    mid = contract.get_reputation(direct_bob)
    assert mid["finalized_outcomes"] == 0

    direct_vm.sender = direct_alice
    contract.finalize_verdict(agreement_id, T0 + 10_000)
    after = contract.get_reputation(direct_bob)
    assert after["finalized_outcomes"] == 1
    assert after["pass_outcomes"] == 1


def test_resubmission_budget_enforced(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "endpoint responds", "priority": "required", "evidence_method": "http:c1"}],
        3600, 600, 0, T0,  # max_resubmissions = 0
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    contract.fund_agreement(agreement_id, 100)
    contract.freeze_agreement(agreement_id, T0 + 1, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}), T0 + 2)
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": "bad"})
    contract.request_evaluation(agreement_id, T0 + 10)

    with direct_vm.expect_revert():
        contract.request_resubmission(agreement_id)
