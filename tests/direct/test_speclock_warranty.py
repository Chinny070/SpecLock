import hashlib
import json

CONTRACT = "contracts/speclock.py"


def _funded_agreement(contract, direct_vm, buyer, provider, amount=1000):
    direct_vm.sender = buyer
    agreement_id = contract.create_agreement(
        provider, "api_delivery", "Deliver GET /health",
        [{"id": "c1", "description": "GET /health returns status ok", "priority": "required", "evidence_method": "http:c1"}],
        1,
    )
    direct_vm.sender = provider
    contract.accept_agreement(agreement_id)
    direct_vm.sender = buyer
    direct_vm.value = amount
    contract.fund_agreement(agreement_id, amount)
    direct_vm.value = 0
    return agreement_id


def test_warranty_pass_then_claim_upheld(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_agreement(contract, direct_vm, direct_alice, direct_bob, amount=1000)
    direct_vm.sender = direct_alice
    contract.enable_warranty(agreement_id, 2000)  # 20% holdback
    contract.freeze_agreement(agreement_id, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"status": "ok"})})
    contract.request_evaluation(agreement_id)

    direct_vm.sender = direct_alice
    assert contract.finalize_verdict(agreement_id) is False
    direct_vm.sender = direct_bob
    assert contract.finalize_verdict(agreement_id) is True
    contract.settle(agreement_id)

    agreement = contract.get_agreement(agreement_id)
    assert agreement["released_amount"] == 800
    assert agreement["warranty_held_amount"] == 200
    assert agreement["warranty_status"] == "HELD"

    direct_vm.sender = direct_alice
    direct_vm.value = 20  # bond = max(1, 200//10)
    claim_id = contract.file_warranty_claim(
        agreement_id, "endpoint broke after delivery",
        "https://api.example.com/health2", hashlib.sha256(b"error").hexdigest(), json.dumps({"criterion_id": "c1"}),
    )
    direct_vm.value = 0
    direct_vm.clear_mocks()
    direct_vm.mock_web(r".*api\.example\.com/health2.*", {"status": 200, "body": "error"})
    contract.resolve_warranty_claim(agreement_id)

    claim = contract.get_warranty_claim(claim_id)
    assert claim["resolution"] == "UPHELD"
    agreement = contract.get_agreement(agreement_id)
    assert agreement["warranty_status"] == "CLAIMED"
    assert agreement["warranty_held_amount"] == 0

    from genlayer.py.types import Address
    assert contract.get_claimable(str(Address(bytes(direct_alice)))) == 200 + 20  # holdback + bond
    assert contract.get_claimable(str(Address(bytes(direct_bob)))) == 800

    # A payable duplicate is rejected without reverting away the attached
    # value. The caller receives a pull refund, preventing the live-proven
    # GenVM behavior where `value_credited` can remain true after rollback.
    direct_vm.value = 20
    assert contract.file_warranty_claim(
        agreement_id, "duplicate", "https://api.example.com/health2", digest,
        json.dumps({"criterion_id": "c1"}),
    ) == ""
    direct_vm.value = 0
    assert contract.get_claimable(str(Address(bytes(direct_alice)))) == 200 + 20 + 20
    assert contract.get_agreement(agreement_id)["warranty_status"] == "CLAIMED"


def test_warranty_claim_rejected_releases_to_provider(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_agreement(contract, direct_vm, direct_alice, direct_bob, amount=1000)
    direct_vm.sender = direct_alice
    contract.enable_warranty(agreement_id, 2000)
    contract.freeze_agreement(agreement_id, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"status": "ok"})})
    contract.request_evaluation(agreement_id)
    direct_vm.sender = direct_alice
    contract.finalize_verdict(agreement_id)
    direct_vm.sender = direct_bob
    contract.finalize_verdict(agreement_id)
    contract.settle(agreement_id)

    direct_vm.sender = direct_alice
    direct_vm.value = 20
    valid_body = json.dumps({"status": "ok"})
    claim_id = contract.file_warranty_claim(
        agreement_id, "still broken", "https://api.example.com/health3", hashlib.sha256(valid_body.encode()).hexdigest(), json.dumps({"criterion_id": "c1"}),
    )
    direct_vm.value = 0
    direct_vm.clear_mocks()
    direct_vm.mock_web(r".*api\.example\.com/health3.*", {"status": 200, "body": valid_body})
    contract.resolve_warranty_claim(agreement_id)

    claim = contract.get_warranty_claim(claim_id)
    assert claim["resolution"] == "REJECTED"
    agreement = contract.get_agreement(agreement_id)
    assert agreement["warranty_status"] == "RELEASED"

    from genlayer.py.types import Address
    assert contract.get_claimable(str(Address(bytes(direct_bob)))) == 800 + 200 + 20  # release + holdback + bond
    assert contract.get_claimable(str(Address(bytes(direct_alice)))) == 0


def test_stale_warranty_evidence_digest_does_not_uphold_claim(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_agreement(contract, direct_vm, direct_alice, direct_bob, amount=1000)
    direct_vm.sender = direct_alice
    contract.enable_warranty(agreement_id, 2000)
    contract.freeze_agreement(agreement_id, False)
    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"initial").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"status": "ok"})})
    contract.request_evaluation(agreement_id)
    direct_vm.sender = direct_alice
    contract.finalize_verdict(agreement_id)
    direct_vm.sender = direct_bob
    contract.finalize_verdict(agreement_id)
    contract.settle(agreement_id)

    direct_vm.sender = direct_alice
    direct_vm.value = 20
    claim_id = contract.file_warranty_claim(
        agreement_id, "test a changed response", "https://api.example.com/changed",
        hashlib.sha256(b"old response").hexdigest(), json.dumps({"criterion_id": "c1"}),
    )
    direct_vm.value = 0
    direct_vm.clear_mocks()
    direct_vm.mock_web(r".*api\.example\.com/changed.*", {"status": 200, "body": "not json"})
    contract.resolve_warranty_claim(agreement_id)

    claim = contract.get_warranty_claim(claim_id)
    assert claim["resolution"] == "REJECTED"
    evaluation = contract.get_evaluation(claim["resolution_evaluation_id"])
    assert evaluation["overall_finding"] == "UNVERIFIABLE"
    from genlayer.py.types import Address
    assert contract.get_claimable(str(Address(bytes(direct_bob)))) == 800 + 200 + 20


def test_warranty_waive_releases_to_provider(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_agreement(contract, direct_vm, direct_alice, direct_bob, amount=1000)
    direct_vm.sender = direct_alice
    contract.enable_warranty(agreement_id, 2000)
    contract.freeze_agreement(agreement_id, False)

    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"status": "ok"})})
    contract.request_evaluation(agreement_id)
    direct_vm.sender = direct_alice
    contract.finalize_verdict(agreement_id)
    direct_vm.sender = direct_bob
    contract.finalize_verdict(agreement_id)
    contract.settle(agreement_id)

    direct_vm.sender = direct_alice
    contract.waive_warranty_claim(agreement_id)
    agreement = contract.get_agreement(agreement_id)
    assert agreement["warranty_status"] == "RELEASED"

    from genlayer.py.types import Address
    assert contract.get_claimable(str(Address(bytes(direct_bob)))) == 1000


def test_enable_warranty_bounds_and_authorization(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_agreement(contract, direct_vm, direct_alice, direct_bob)

    direct_vm.sender = direct_bob
    with direct_vm.expect_revert():
        contract.enable_warranty(agreement_id, 1000)  # not the buyer

    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.enable_warranty(agreement_id, 0)  # must be positive
    with direct_vm.expect_revert():
        contract.enable_warranty(agreement_id, 5001)  # exceeds MAX_WARRANTY_BPS

    contract.enable_warranty(agreement_id, 5000)
    with direct_vm.expect_revert():
        contract.enable_warranty(agreement_id, 1000)  # already configured


def test_file_warranty_claim_requires_held_status_and_exact_bond(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _funded_agreement(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.file_warranty_claim(agreement_id, "x", "https://a.example.com", hashlib.sha256(b"x").hexdigest(), "{}")

    contract.enable_warranty(agreement_id, 2000)
    contract.freeze_agreement(agreement_id, False)
    direct_vm.sender = direct_bob
    digest = hashlib.sha256(b"x").hexdigest()
    contract.submit_evidence(agreement_id, "https://api.example.com/health", digest, json.dumps({"criterion_id": "c1"}))
    direct_vm.mock_web(r".*api\.example\.com/health.*", {"status": 200, "body": json.dumps({"status": "ok"})})
    contract.request_evaluation(agreement_id)
    direct_vm.sender = direct_alice
    contract.finalize_verdict(agreement_id)
    direct_vm.sender = direct_bob
    contract.finalize_verdict(agreement_id)
    contract.settle(agreement_id)

    direct_vm.sender = direct_alice
    direct_vm.value = 1  # wrong bond, should be max(1, 200//10)=20
    assert contract.file_warranty_claim(agreement_id, "x", "https://a.example.com", digest, "{}") == ""
    direct_vm.value = 0
    from genlayer.py.types import Address
    assert contract.get_claimable(str(Address(bytes(direct_alice)))) == 1

    direct_vm.sender = direct_bob
    direct_vm.value = 20
    assert contract.file_warranty_claim(agreement_id, "x", "https://a.example.com", digest, "{}") == ""  # not the buyer
    direct_vm.value = 0
    assert contract.get_claimable(str(Address(bytes(direct_bob)))) == 800 + 20
