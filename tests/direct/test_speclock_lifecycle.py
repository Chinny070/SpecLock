"""Lifecycle acceptance scenarios for SpecLock (Stage 1/2, Gate B).

Maps to docs/ACCEPTANCE_TEST_MATRIX.md rows: Agreement, Policy, State,
Finality, Settlement, Recovery.

No wall-clock time is used anywhere in this contract (see the time note in
contracts/speclock.py and docs/THREAT_MODEL.md "clock redesign"): deadlines
are replaced by mutual two-party consent gates, and appeal filing is never
time-boxed. These tests exercise that design directly.
"""

CONTRACT = "contracts/speclock.py"


def _create(contract, direct_vm, buyer, provider, max_resub=1):
    direct_vm.sender = buyer
    return contract.create_agreement(
        provider,
        "api_delivery",
        "Deliver a GET /health endpoint returning {\"status\": \"ok\"}",
        [{"id": "c1", "description": "GET /health returns status ok", "priority": "required", "evidence_method": "http:c1"}],
        max_resub,
    )


def test_create_accept_freeze_flow(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _create(contract, direct_vm, direct_alice, direct_bob)

    from genlayer.py.types import Address
    agreement = contract.get_agreement(agreement_id)
    assert agreement["phase"] == "DRAFT"
    assert agreement["buyer"] == str(Address(bytes(direct_alice)))
    assert agreement["provider"] == str(Address(bytes(direct_bob)))

    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    assert contract.get_agreement(agreement_id)["phase"] == "ACCEPTED"

    direct_vm.sender = direct_alice
    contract.fund_agreement(agreement_id, 1000)
    assert contract.get_agreement(agreement_id)["funded_amount"] == 1000
    assert contract.get_agreement(agreement_id)["phase"] == "FUNDED"

    contract.freeze_agreement(agreement_id, False)
    frozen = contract.get_agreement(agreement_id)
    assert frozen["phase"] == "FROZEN"
    fp_before = frozen["spec_fingerprint"]

    # Capability: Policy — pinned fingerprint does not change after freeze.
    assert contract.get_policy_fingerprint(agreement_id) == fp_before


def test_wrong_actor_cannot_accept(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = direct_deploy(CONTRACT)
    agreement_id = _create(contract, direct_vm, direct_alice, direct_bob)

    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert():
        contract.accept_agreement(agreement_id)


def test_only_buyer_can_create_mismatched_provider_rejected(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.create_agreement(
            direct_alice,  # provider == buyer, invalid
            "api_delivery",
            "spec",
            [{"id": "c1", "description": "x", "priority": "required", "evidence_method": "http"}],
            1,
        )


def test_ambiguity_detected_before_freeze_and_blocks_without_ack(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob,
        "api_delivery",
        "Deliver a nice fast API",
        [{"id": "c1", "description": "Response should be good quality", "priority": "required", "evidence_method": "http"}],
        1,
    )
    agreement = contract.get_agreement(agreement_id)
    assert "vague term" in agreement["ambiguity_report"]

    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    contract.fund_agreement(agreement_id, 100)

    with direct_vm.expect_revert():
        contract.freeze_agreement(agreement_id, False)

    contract.freeze_agreement(agreement_id, True)
    assert contract.get_agreement(agreement_id)["phase"] == "FROZEN"


def test_duplicate_criterion_ids_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.create_agreement(
            direct_bob,
            "api_delivery",
            "spec",
            [
                {"id": "c1", "description": "a", "priority": "required", "evidence_method": "http"},
                {"id": "c1", "description": "b", "priority": "required", "evidence_method": "http"},
            ],
            1,
        )


def test_unauthorized_or_out_of_order_transition_does_not_mutate_state(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _create(contract, direct_vm, direct_alice, direct_bob)

    # freeze before fund/accept must be rejected and must not mutate phase.
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.freeze_agreement(agreement_id, False)
    assert contract.get_agreement(agreement_id)["phase"] == "DRAFT"


def test_cancel_before_funding_by_party(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _create(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    contract.cancel_or_expire(agreement_id)
    assert contract.get_agreement(agreement_id)["phase"] == "CANCELLED"
    assert contract.is_consumable(agreement_id) is False


def test_frozen_wind_down_requires_both_parties_consent(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Replaces the old wall-clock 'expired after deadline' scenario: a
    single party can no longer unilaterally force expiry/refund of a
    FROZEN-but-stalled agreement. Both buyer and provider must separately
    call cancel_or_expire."""
    contract = direct_deploy(CONTRACT)
    agreement_id = _create(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    contract.fund_agreement(agreement_id, 500)
    contract.freeze_agreement(agreement_id, False)

    # Buyer alone cannot force expiry.
    contract.cancel_or_expire(agreement_id)
    assert contract.get_agreement(agreement_id)["phase"] == "FROZEN"
    assert contract.get_agreement(agreement_id)["buyer_consents_expire"] is True

    # Calling twice as the same party is rejected (no double-consent).
    with direct_vm.expect_revert():
        contract.cancel_or_expire(agreement_id)

    # Once the provider also consents, it actually expires and refunds.
    direct_vm.sender = direct_bob
    contract.cancel_or_expire(agreement_id)

    agreement = contract.get_agreement(agreement_id)
    assert agreement["phase"] == "EXPIRED"
    settlement = contract.get_settlement(agreement_id)
    assert settlement["refunded_to_buyer"] == 500
    assert settlement["released_to_provider"] == 0
    # Fund-conservation invariant.
    assert settlement["released_to_provider"] + settlement["refunded_to_buyer"] + settlement["retained"] == 500


def test_unrelated_party_cannot_consent_to_wind_down(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = direct_deploy(CONTRACT)
    agreement_id = _create(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    contract.fund_agreement(agreement_id, 100)
    contract.freeze_agreement(agreement_id, False)

    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert():
        contract.cancel_or_expire(agreement_id)
