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
            {"id": "c1", "description": "GET /health returns status ok", "priority": "required", "evidence_method": "http:c1", "expected_json": {"status": "ok"}, "target_url": "https://api.example.com/health"},
            {"id": "c2", "description": "GET /version returns version string", "priority": "required", "evidence_method": "http:c2", "expected_json": {"version": "1.0"}, "target_url": "https://api.example.com/version"},
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
    assert contract.is_final(agreement_id) is True
    assert contract.is_consumable(agreement_id) is False
    assert contract.get_verdict(agreement_id) == "MILESTONE_BASED: see get_milestone_summary"
    assert contract.verify_settlement_replay(agreement_id)["matches_recorded_settlement"] is True

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


def test_warranty_then_milestones_is_rejected_without_changing_terms(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_two_criteria_agreement(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    contract.enable_warranty(agreement_id, 2000)
    before = contract.get_agreement(agreement_id)
    with direct_vm.expect_revert():
        contract.define_milestones(agreement_id, [
            {"criteria_ids": ["c1"], "amount": 500}, {"criteria_ids": ["c2"], "amount": 500},
        ])
    after = contract.get_agreement(agreement_id)
    assert after["warranty_bps"] == 2000
    assert after["milestones_defined"] is False
    assert after["buyer_economic_terms_hash"] == before["buyer_economic_terms_hash"]
    assert after["provider_economic_terms_hash"] == before["provider_economic_terms_hash"]


def test_milestones_then_warranty_is_rejected_without_changing_allocations(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_two_criteria_agreement(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    milestone_ids = contract.define_milestones(agreement_id, [
        {"criteria_ids": ["c1"], "amount": 500}, {"criteria_ids": ["c2"], "amount": 500},
    ])
    before = [contract.get_milestone(mid)["allocated_amount"] for mid in milestone_ids]
    agreement_before = contract.get_agreement(agreement_id)
    with direct_vm.expect_revert():
        contract.enable_warranty(agreement_id, 2000)
    after = contract.get_agreement(agreement_id)
    assert after["warranty_bps"] == 0
    assert after["buyer_economic_terms_hash"] == agreement_before["buyer_economic_terms_hash"]
    assert after["provider_economic_terms_hash"] == agreement_before["provider_economic_terms_hash"]
    assert [contract.get_milestone(mid)["allocated_amount"] for mid in milestone_ids] == before


def test_milestone_partial_settlement_excludes_pass_with_insufficient_evidence(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob, "ai_agent_delivery", "Milestone with sufficient and insufficient findings",
        [
            {"id": "c1", "description": "Required output is complete", "priority": "required", "evidence_method": "artifact"},
            {"id": "c2", "description": "Optional output is complete", "priority": "optional", "evidence_method": "artifact"},
        ], 0,
    )
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    direct_vm.value = 1000
    contract.fund_agreement(agreement_id, 1000)
    direct_vm.value = 0
    [milestone_id] = contract.define_milestones(agreement_id, [
        {"criteria_ids": ["c1", "c2"], "amount": 1000},
    ])
    direct_vm.sender = direct_bob
    contract.accept_economic_terms(agreement_id)
    direct_vm.sender = direct_alice
    contract.freeze_agreement(agreement_id, False)
    direct_vm.sender = direct_bob
    for cid in ("c1", "c2"):
        body = f"evidence-{cid}"
        url = f"https://files.example.com/{cid}"
        direct_vm.mock_web(url, {"status": 200, "body": body})
        contract.submit_evidence(agreement_id, url, hashlib.sha256(body.encode()).hexdigest(), json.dumps({"criterion_id": cid}))
    direct_vm.mock_llm(r".*Criterion: Required output.*", json.dumps({"finding": "PASS", "sufficiency": "SUFFICIENT", "rationale": "complete"}))
    direct_vm.mock_llm(r".*Criterion: Optional output.*", json.dumps({"finding": "PASS", "sufficiency": "INSUFFICIENT", "rationale": "weak"}))
    evaluation_id = contract.request_milestone_evaluation(agreement_id, milestone_id)
    evaluation = contract.get_evaluation(evaluation_id)
    assert evaluation["overall_finding"] == "PARTIAL"
    direct_vm.sender = direct_alice
    assert contract.finalize_milestone(agreement_id, milestone_id) is False
    direct_vm.sender = direct_bob
    assert contract.finalize_milestone(agreement_id, milestone_id) is True
    contract.settle_milestone(agreement_id, milestone_id)
    milestone = contract.get_milestone(milestone_id)
    assert milestone["released_amount"] == 500
    assert milestone["refunded_amount"] == 500


def test_milestone_expiry_evaluates_relevant_evidence_and_refunds_only_empty_milestone(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    from datetime import datetime, timezone

    direct_vm.warp("2026-01-01T00:00:00+00:00")
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_two_criteria_agreement(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    ms1, ms2 = contract.define_milestones(agreement_id, [
        {"criteria_ids": ["c1"], "amount": 600},
        {"criteria_ids": ["c2"], "amount": 400},
    ])
    direct_vm.sender = direct_bob
    contract.accept_economic_terms(agreement_id)
    direct_vm.sender = direct_alice
    contract.freeze_agreement(agreement_id, False)
    direct_vm.sender = direct_bob
    body = json.dumps({"version": "1.0"})
    contract.submit_evidence(agreement_id, "https://api.example.com/version", hashlib.sha256(body.encode()).hexdigest(), json.dumps({"criterion_id": "c2"}))
    deadline = contract.get_agreement(agreement_id)["delivery_deadline_at"]
    direct_vm.warp(datetime.fromtimestamp(deadline + 1, timezone.utc).isoformat())
    direct_vm.mock_web(".*api\\.example\\.com/version.*", {"status": 200, "body": body})
    direct_vm.sender = direct_charlie

    # c1 has no relevant evidence and only its 600 allocation is refunded.
    contract.expire_milestone(agreement_id, ms1)
    first = contract.get_milestone(ms1)
    assert first["phase"] == "MS_REFUNDED"
    assert first["refunded_amount"] == 600
    assert first["released_amount"] == 0

    # c2's timely evidence requires the normal evaluation process even though
    # expiry is permissionless and the overall delivery window has elapsed.
    evaluation_id = contract.expire_milestone(agreement_id, ms2)
    second = contract.get_milestone(ms2)
    assert second["phase"] == "MS_PROVISIONAL_VERDICT"
    assert second["latest_evaluation_id"] == evaluation_id
    assert contract.get_evaluation(evaluation_id)["overall_finding"] == "PASS"
    assert second["settlement_id"] == ""
    summary = contract.get_milestone_summary(agreement_id)
    assert summary["released_amount"] + summary["refunded_amount"] == 600
    assert summary["pending_count"] == 1


def test_milestone_overdue_evaluation_rejects_unrelated_caller_before_deadline(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_two_criteria_agreement(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    [milestone_id] = contract.define_milestones(agreement_id, [{"criteria_ids": ["c1", "c2"], "amount": 1000}])
    direct_vm.sender = direct_bob
    contract.accept_economic_terms(agreement_id)
    direct_vm.sender = direct_alice
    contract.freeze_agreement(agreement_id, False)
    direct_vm.sender = direct_bob
    body = json.dumps({"status": "ok"})
    contract.submit_evidence(agreement_id, "https://api.example.com/health", hashlib.sha256(body.encode()).hexdigest(), json.dumps({"criterion_id": "c1"}))
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert():
        contract.request_milestone_evaluation(agreement_id, milestone_id)
    assert contract.get_milestone(milestone_id)["phase"] == "MS_PENDING"
