"""Capability 30: milestone decomposition and lifecycle.

Covers: milestone creation (define_milestones) with its two core safety
invariants (criteria partition exactly, amounts sum exactly to the funded
amount), independent per-milestone evaluation/finalization/settlement,
fund conservation across milestones, isolation (settling one milestone
cannot affect another), milestone-inconclusive recovery, and rejection of
the ordinary single-evaluation methods (request_evaluation/settle/
file_appeal/request_resubmission/cancel_or_expire) for a milestone-using
agreement.
"""

import hashlib
import json

CONTRACT = "contracts/speclock.py"


def _funded_two_criteria_agreement(contract, direct_vm, buyer, provider, amount=1000):
    direct_vm.sender = buyer
    agreement_id = contract.create_agreement(
        provider, "api_delivery", "Deliver two independent endpoints",
        [
            {"id": "c1", "description": "GET /health returns status ok", "priority": "required", "evidence_method": "http:c1", "expected_json": {"status": "ok"}},
            {"id": "c2", "description": "GET /version returns version string", "priority": "required", "evidence_method": "http:c2", "expected_json": {"version": "1.0"}},
        ],
        1,
    )
    direct_vm.sender = provider
    contract.accept_agreement(agreement_id)
    direct_vm.sender = buyer
    direct_vm.value = amount
    contract.fund_agreement(agreement_id, amount)
    direct_vm.value = 0
    return agreement_id


def test_define_milestones_rejects_overlapping_criteria(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_two_criteria_agreement(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.define_milestones(agreement_id, [
            {"criteria_ids": ["c1", "c2"], "amount": 600},
            {"criteria_ids": ["c2"], "amount": 400},  # c2 assigned twice
        ])


def test_define_milestones_rejects_omitted_criteria(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_two_criteria_agreement(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.define_milestones(agreement_id, [
            {"criteria_ids": ["c1"], "amount": 1000},  # c2 never assigned to any milestone
        ])


def test_define_milestones_rejects_amount_mismatch(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_two_criteria_agreement(contract, direct_vm, direct_alice, direct_bob, amount=1000)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.define_milestones(agreement_id, [
            {"criteria_ids": ["c1"], "amount": 600},
            {"criteria_ids": ["c2"], "amount": 500},  # sums to 1100, not 1000
        ])


def test_define_milestones_only_buyer_and_only_once(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_two_criteria_agreement(contract, direct_vm, direct_alice, direct_bob)

    direct_vm.sender = direct_bob
    with direct_vm.expect_revert():
        contract.define_milestones(agreement_id, [{"criteria_ids": ["c1", "c2"], "amount": 1000}])
    direct_vm.sender = direct_alice
    contract.define_milestones(agreement_id, [{"criteria_ids": ["c1", "c2"], "amount": 1000}])
    with direct_vm.expect_revert():
        contract.define_milestones(agreement_id, [{"criteria_ids": ["c1", "c2"], "amount": 1000}])


def test_milestone_economic_terms_require_bilateral_acceptance(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_two_criteria_agreement(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    contract.define_milestones(agreement_id, [{"criteria_ids": ["c1", "c2"], "amount": 1000}])
    with direct_vm.expect_revert():
        contract.freeze_agreement(agreement_id, False)
    direct_vm.sender = direct_bob
    assert contract.accept_economic_terms(agreement_id) is True
    direct_vm.sender = direct_alice
    contract.freeze_agreement(agreement_id, False)


def test_milestones_independent_evaluation_and_settlement_fund_conservation(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Positive end-to-end proof: two milestones, one PASS one FAIL,
    settled independently, and settling one does not touch the other."""
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_two_criteria_agreement(contract, direct_vm, direct_alice, direct_bob, amount=1000)
    direct_vm.sender = direct_alice
    ms1, ms2 = contract.define_milestones(agreement_id, [
        {"criteria_ids": ["c1"], "amount": 600},
        {"criteria_ids": ["c2"], "amount": 400},
    ])
    assert contract.get_milestone_summary(agreement_id)["all_complete"] is False
    with direct_vm.expect_revert():
        contract.request_milestone_evaluation(agreement_id, ms1)
    direct_vm.sender = direct_bob
    assert contract.accept_economic_terms(agreement_id) is True
    direct_vm.sender = direct_alice
    contract.freeze_agreement(agreement_id, False)

    direct_vm.sender = direct_bob
    body1 = json.dumps({"status": "ok"})
    digest = hashlib.sha256(body1.encode()).hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example.com/health.*", {"status": 200, "body": body1})

    contract.request_milestone_evaluation(agreement_id, ms1)
    assert contract.get_milestone(ms1)["phase"] == "MS_PROVISIONAL_VERDICT"
    assert contract.get_milestone(ms2)["phase"] == "MS_PENDING"  # untouched

    direct_vm.sender = direct_alice
    assert contract.finalize_milestone(agreement_id, ms1) is False
    direct_vm.sender = direct_bob
    assert contract.finalize_milestone(agreement_id, ms1) is True
    contract.settle_milestone(agreement_id, ms1)

    ms1_state = contract.get_milestone(ms1)
    assert ms1_state["phase"] == "MS_SETTLED"
    assert ms1_state["released_amount"] == 600
    assert ms1_state["refunded_amount"] == 0

    # ms2 is completely unaffected by ms1's settlement.
    ms2_state = contract.get_milestone(ms2)
    assert ms2_state["phase"] == "MS_PENDING"
    assert ms2_state["settlement_id"] == ""

    with direct_vm.expect_revert():
        contract.settle_milestone(agreement_id, ms1)  # double-settle rejected

    direct_vm.sender = direct_bob
    body2 = "not json"
    contract.submit_evidence(agreement_id, "https://api.example.com/version", hashlib.sha256(body2.encode()).hexdigest(), json.dumps({"criterion_id": "c2"}))
    direct_vm.mock_web(r".*api\.example\.com/version.*", {"status": 200, "body": "not json"})
    contract.request_milestone_evaluation(agreement_id, ms2)
    direct_vm.sender = direct_alice
    assert contract.finalize_milestone(agreement_id, ms2) is False
    direct_vm.sender = direct_bob
    assert contract.finalize_milestone(agreement_id, ms2) is True
    contract.settle_milestone(agreement_id, ms2)

    ms2_state = contract.get_milestone(ms2)
    assert ms2_state["phase"] == "MS_SETTLED"
    assert ms2_state["released_amount"] == 0
    assert ms2_state["refunded_amount"] == 400

    # Fund conservation across the whole agreement: released + refunded
    # across both milestones equals exactly the total funded amount.
    total_released = ms1_state["released_amount"] + ms2_state["released_amount"]
    total_refunded = ms1_state["refunded_amount"] + ms2_state["refunded_amount"]
    assert total_released + total_refunded == 1000
    summary = contract.get_milestone_summary(agreement_id)
    assert summary["all_complete"] is True
    assert summary["completed_count"] == 2
    assert summary["released_amount"] + summary["refunded_amount"] == 1000

    from genlayer.py.types import Address
    assert contract.get_claimable(str(Address(bytes(direct_bob)))) == 600  # provider got ms1's release
    assert contract.get_claimable(str(Address(bytes(direct_alice)))) == 400  # buyer got ms2's refund


def test_milestone_unverifiable_recovers_via_recover_milestone_inconclusive(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_two_criteria_agreement(contract, direct_vm, direct_alice, direct_bob, amount=1000)
    direct_vm.sender = direct_alice
    ms1, ms2 = contract.define_milestones(agreement_id, [
        {"criteria_ids": ["c1"], "amount": 600},
        {"criteria_ids": ["c2"], "amount": 400},
    ])
    direct_vm.sender = direct_bob
    contract.accept_economic_terms(agreement_id)
    direct_vm.sender = direct_alice
    contract.freeze_agreement(agreement_id, False)

    # No evidence submitted for c1 at all -> milestone evaluation derives UNVERIFIABLE.
    contract.request_milestone_evaluation(agreement_id, ms1)
    evaluation = contract.get_evaluation(contract.get_milestone(ms1)["latest_evaluation_id"])
    assert evaluation["overall_finding"] == "UNVERIFIABLE"

    direct_vm.sender = direct_alice
    assert contract.finalize_milestone(agreement_id, ms1) is False
    direct_vm.sender = direct_bob
    assert contract.finalize_milestone(agreement_id, ms1) is True
    contract.settle_milestone(agreement_id, ms1)
    assert contract.get_milestone(ms1)["phase"] == "MS_RECOVERY_PENDING"

    contract.recover_milestone_inconclusive(agreement_id, ms1)
    ms1_state = contract.get_milestone(ms1)
    assert ms1_state["phase"] == "MS_REFUNDED"
    assert ms1_state["refunded_amount"] == 600

    # ms2 is still untouched throughout.
    assert contract.get_milestone(ms2)["phase"] == "MS_PENDING"


def test_milestone_agreement_rejects_top_level_single_evaluation_methods(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Capability 30 safety boundary: once an agreement opts into
    milestones, the ordinary single-evaluation methods must all be
    rejected, not silently misbehave."""
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_two_criteria_agreement(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    contract.define_milestones(agreement_id, [{"criteria_ids": ["c1", "c2"], "amount": 1000}])
    direct_vm.sender = direct_bob
    contract.accept_economic_terms(agreement_id)
    direct_vm.sender = direct_alice
    contract.freeze_agreement(agreement_id, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))

    with direct_vm.expect_revert():
        contract.request_evaluation(agreement_id)
    with direct_vm.expect_revert():
        contract.settle(agreement_id)
    with direct_vm.expect_revert():
        contract.request_resubmission(agreement_id)
    with direct_vm.expect_revert():
        contract.cancel_or_expire(agreement_id)

    [ms] = contract.get_milestones(agreement_id)
    contract.request_milestone_evaluation(agreement_id, ms["milestone_id"])
    direct_vm.value = 100
    assert contract.file_appeal(agreement_id, ["c1"], "disagree") == ""
    direct_vm.value = 0


def test_define_milestones_rejects_wrong_phase_and_bad_criterion_id(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "api_delivery", "spec",
        [{"id": "c1", "description": "x", "priority": "required", "evidence_method": "http:c1"}],
        1,
    )
    # Not even accepted/funded yet.
    with direct_vm.expect_revert():
        contract.define_milestones(agreement_id, [{"criteria_ids": ["c1"], "amount": 100}])

    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    direct_vm.value = 100
    contract.fund_agreement(agreement_id, 100)
    direct_vm.value = 0

    with direct_vm.expect_revert():
        contract.define_milestones(agreement_id, [{"criteria_ids": ["unknown_id"], "amount": 100}])

    with direct_vm.expect_revert():
        contract.define_milestones(agreement_id, [])  # zero milestones

    with direct_vm.expect_revert():
        contract.define_milestones(agreement_id, [{"criteria_ids": [], "amount": 100}])  # empty criteria list
