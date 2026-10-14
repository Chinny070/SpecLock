"""API-delivery profile acceptance scenarios (Gate B).

Maps to docs/ACCEPTANCE_TEST_MATRIX.md rows: API positive, API negative,
API uncertain, Evidence, Settlement, Appeal.

No wall-clock time is used: finalize_verdict from a provisional verdict
(no appeal filed) requires BOTH buyer and provider to separately call it;
file_appeal is never time-boxed (see contracts/speclock.py time note and
docs/THREAT_MODEL.md "clock redesign").
"""

import hashlib
import json

CONTRACT = "contracts/speclock.py"


def _setup_frozen_agreement(contract, direct_vm, buyer, provider, url_bound_criterion="c1"):
    direct_vm.sender = buyer
    agreement_id = contract.create_agreement(
        provider,
        "api_delivery",
        "Deliver GET https://api.example.com/health returning JSON body",
        [{"id": url_bound_criterion, "description": "endpoint responds with a JSON object", "priority": "required", "evidence_method": "http:c1"}],
        1,
    )
    direct_vm.sender = provider
    contract.accept_agreement(agreement_id)
    direct_vm.sender = buyer
    contract.fund_agreement(agreement_id, 1000)
    contract.freeze_agreement(agreement_id, False)
    return agreement_id


def _submit_evidence(contract, direct_vm, submitter, agreement_id, url):
    direct_vm.sender = submitter
    digest = hashlib.sha256(url.encode()).hexdigest()
    return contract.submit_evidence(agreement_id, url, digest, json.dumps({"criterion_id": "c1"}))


def _mutual_finalize(contract, direct_vm, buyer, provider, agreement_id):
    direct_vm.sender = buyer
    first = contract.finalize_verdict(agreement_id)
    assert first is False
    direct_vm.sender = provider
    second = contract.finalize_verdict(agreement_id)
    assert second is True


def test_api_positive_schema_consistent_response_passes(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agreement(contract, direct_vm, direct_alice, direct_bob)
    _submit_evidence(contract, direct_vm, direct_bob, agreement_id, "https://api.example.com/health")

    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"status": "ok"})})

    direct_vm.sender = direct_bob
    evaluation_id = contract.request_evaluation(agreement_id)
    evaluation = contract.get_evaluation(evaluation_id)
    assert evaluation["overall_finding"] == "PASS"
    findings = evaluation["findings"]
    assert findings[0]["finding"] == "PASS"
    assert findings[0]["sufficiency"] == "SUFFICIENT"


def test_api_negative_200_with_wrong_payload_does_not_pass(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agreement(contract, direct_vm, direct_alice, direct_bob)
    _submit_evidence(contract, direct_vm, direct_bob, agreement_id, "https://api.example.com/health")

    # 200 OK but an empty/non-JSON body: reachable but not functionally correct.
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": "not json"})

    direct_vm.sender = direct_bob
    evaluation_id = contract.request_evaluation(agreement_id)
    evaluation = contract.get_evaluation(evaluation_id)
    assert evaluation["overall_finding"] == "FAIL"
    assert evaluation["findings"][0]["finding"] == "FAIL"
    assert evaluation["failure_attribution"] == "DELIVERY"


def test_api_uncertain_unreachable_host_is_unverifiable(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agreement(contract, direct_vm, direct_alice, direct_bob)
    _submit_evidence(contract, direct_vm, direct_bob, agreement_id, "https://api.example.com/health")

    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 503, "body": ""})

    direct_vm.sender = direct_bob
    evaluation_id = contract.request_evaluation(agreement_id)
    evaluation = contract.get_evaluation(evaluation_id)
    assert evaluation["overall_finding"] == "UNVERIFIABLE"
    assert evaluation["findings"][0]["finding"] == "UNVERIFIABLE"


def test_missing_evidence_for_criterion_is_unverifiable_not_fail(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agreement(contract, direct_vm, direct_alice, direct_bob)
    # No evidence submitted at all; request_evaluation requires SUBMITTED phase,
    # so submit an unrelated evidence item (different criterion tag) to reach it.
    direct_vm.sender = direct_bob
    contract.submit_evidence(agreement_id, "https://api.example.com/other", hashlib.sha256(b"x").hexdigest(), json.dumps({"criterion_id": "unused"}))

    evaluation_id = contract.request_evaluation(agreement_id)
    evaluation = contract.get_evaluation(evaluation_id)
    assert evaluation["overall_finding"] == "UNVERIFIABLE"
    assert evaluation["findings"][0]["sufficiency"] == "INSUFFICIENT"


def test_evidence_url_blocked_schemes_and_hosts_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agreement(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()

    with direct_vm.expect_revert():
        contract.submit_evidence(agreement_id, "http://api.example.com/health", digest, "{}")  # non-https
    with direct_vm.expect_revert():
        contract.submit_evidence(agreement_id, "https://localhost/health", digest, "{}")  # blocked host
    with direct_vm.expect_revert():
        contract.submit_evidence(agreement_id, "https://user:pass@api.example.com/health", digest, "{}")  # embedded creds


def test_evidence_freezes_and_snapshot_is_immutable_after_evaluation(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agreement(contract, direct_vm, direct_alice, direct_bob)
    _submit_evidence(contract, direct_vm, direct_bob, agreement_id, "https://api.example.com/health")
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"status": "ok"})})

    direct_vm.sender = direct_bob
    evaluation_id = contract.request_evaluation(agreement_id)
    evaluation = contract.get_evaluation(evaluation_id)
    snapshot_before = evaluation["evidence_snapshot_commitment"]

    receipts = contract.list_evidence(agreement_id, 0, 10)
    assert all(r["status"] == "FROZEN" for r in receipts)
    assert snapshot_before != ""


def test_settlement_conservation_on_pass(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agreement(contract, direct_vm, direct_alice, direct_bob)
    _submit_evidence(contract, direct_vm, direct_bob, agreement_id, "https://api.example.com/health")
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"status": "ok"})})

    direct_vm.sender = direct_bob
    contract.request_evaluation(agreement_id)

    _mutual_finalize(contract, direct_vm, direct_alice, direct_bob, agreement_id)

    direct_vm.sender = direct_alice
    settlement_id = contract.settle(agreement_id)
    settlement = contract.get_settlement(agreement_id)
    assert settlement["released_to_provider"] == 1000
    assert settlement["refunded_to_buyer"] == 0
    assert settlement["retained"] == 0
    total = settlement["released_to_provider"] + settlement["refunded_to_buyer"] + settlement["retained"]
    assert total == 1000

    # Double settlement / replay must be rejected.
    with direct_vm.expect_revert():
        contract.settle(agreement_id)


def test_finalize_requires_both_distinct_parties_not_one_caller_twice(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agreement(contract, direct_vm, direct_alice, direct_bob)
    _submit_evidence(contract, direct_vm, direct_bob, agreement_id, "https://api.example.com/health")
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"status": "ok"})})
    direct_vm.sender = direct_bob
    contract.request_evaluation(agreement_id)

    direct_vm.sender = direct_alice
    assert contract.finalize_verdict(agreement_id) is False
    # Same party calling again cannot unilaterally force finalization.
    with direct_vm.expect_revert():
        contract.finalize_verdict(agreement_id)
    assert contract.get_agreement(agreement_id)["phase"] == "PROVISIONAL_VERDICT"


def test_filing_appeal_is_never_time_boxed(direct_vm, direct_deploy, direct_alice, direct_bob):
    """An appeal may always be filed while a provisional verdict stands,
    with no deadline to race against (replaces the old wall-clock appeal
    window test)."""
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agreement(contract, direct_vm, direct_alice, direct_bob)
    _submit_evidence(contract, direct_vm, direct_bob, agreement_id, "https://api.example.com/health")
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": "bad"})

    direct_vm.sender = direct_bob
    contract.request_evaluation(agreement_id)

    # Provider is ready to finalize, but buyer instead appeals -- appeal
    # always takes precedence over a lone party's finalize consent.
    direct_vm.sender = direct_bob
    assert contract.finalize_verdict(agreement_id) is False

    direct_vm.sender = direct_alice
    contract.file_appeal(agreement_id, ["c1"], "the endpoint actually returns valid JSON")
    assert contract.get_agreement(agreement_id)["phase"] == "APPEALED"

    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"status": "ok"})})
    contract.resolve_appeal(agreement_id)
    appeal = contract.get_appeal(contract.get_agreement(agreement_id)["latest_appeal_id"])
    assert appeal["resolution"] in ("UPHELD", "REJECTED")

    # Prior round's finalize consent must not leak into the new round --
    # the fresh verdict produced by resolve_appeal still needs its own
    # mutual consent (or a further appeal) before it can finalize.
    agreement = contract.get_agreement(agreement_id)
    assert agreement["buyer_ready_to_finalize"] is False
    assert agreement["provider_ready_to_finalize"] is False

    _mutual_finalize(contract, direct_vm, direct_alice, direct_bob, agreement_id)
    assert contract.get_agreement(agreement_id)["phase"] == "FINALIZED"


def test_appeal_replay_after_resolution_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agreement(contract, direct_vm, direct_alice, direct_bob)
    _submit_evidence(contract, direct_vm, direct_bob, agreement_id, "https://api.example.com/health")
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": "bad"})

    direct_vm.sender = direct_bob
    contract.request_evaluation(agreement_id)

    direct_vm.sender = direct_alice
    contract.file_appeal(agreement_id, ["c1"], "disagree")
    contract.resolve_appeal(agreement_id)

    # Agreement is now back in PROVISIONAL_VERDICT; a second appeal round
    # (max_appeal_rounds default = 2, used = 1) is still allowed once, but a
    # third round must fail.
    contract.file_appeal(agreement_id, ["c1"], "still disagree")
    contract.resolve_appeal(agreement_id)
    with direct_vm.expect_revert():
        contract.file_appeal(agreement_id, ["c1"], "one too many")
