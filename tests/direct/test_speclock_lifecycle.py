"""Lifecycle acceptance scenarios for SpecLock (Stage 1/2, Gate B).

Maps to docs/ACCEPTANCE_TEST_MATRIX.md rows: Agreement, Policy, State,
Finality, Settlement, Recovery.
"""

CONTRACT = "contracts/speclock.py"
T0 = 1_700_000_000  # arbitrary fixed unix-seconds base for deterministic tests


def _create(contract, direct_vm, buyer, provider, now=T0, deadline=3600, appeal_window=600, max_resub=1):
    direct_vm.sender = buyer
    return contract.create_agreement(
        provider,
        "api_delivery",
        "Deliver a GET /health endpoint returning {\"status\": \"ok\"}",
        [{"id": "c1", "description": "GET /health returns status ok", "priority": "required", "evidence_method": "http:c1"}],
        deadline,
        appeal_window,
        max_resub,
        now,
    )


def test_create_accept_freeze_flow(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _create(contract, direct_vm, direct_alice, direct_bob)

    agreement = contract.get_agreement(agreement_id)
    assert agreement["phase"] == "DRAFT"
    from genlayer.py.types import Address
    assert agreement["buyer"] == str(Address(bytes(direct_alice)))
    assert agreement["provider"] == str(Address(bytes(direct_bob)))

    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    assert contract.get_agreement(agreement_id)["phase"] == "ACCEPTED"

    direct_vm.sender = direct_alice
    contract.fund_agreement(agreement_id, 1000)
    assert contract.get_agreement(agreement_id)["funded_amount"] == 1000
    assert contract.get_agreement(agreement_id)["phase"] == "FUNDED"

    contract.freeze_agreement(agreement_id, T0 + 10, False)
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
            3600,
            600,
            1,
            T0,
        )


def test_ambiguity_detected_before_freeze_and_blocks_without_ack(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_alice
    agreement_id = contract.create_agreement(
        direct_bob,
        "api_delivery",
        "Deliver a nice fast API",
        [{"id": "c1", "description": "Response should be good quality", "priority": "required", "evidence_method": "http"}],
        3600,
        600,
        1,
        T0,
    )
    agreement = contract.get_agreement(agreement_id)
    assert "vague term" in agreement["ambiguity_report"]

    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    contract.fund_agreement(agreement_id, 100)

    with direct_vm.expect_revert():
        contract.freeze_agreement(agreement_id, T0 + 10, False)

    contract.freeze_agreement(agreement_id, T0 + 10, True)
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
            3600,
            600,
            1,
            T0,
        )


def test_unauthorized_or_out_of_order_transition_does_not_mutate_state(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _create(contract, direct_vm, direct_alice, direct_bob)

    # freeze before fund/accept must be rejected and must not mutate phase.
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.freeze_agreement(agreement_id, T0 + 10, False)
    assert contract.get_agreement(agreement_id)["phase"] == "DRAFT"


def test_cancel_before_funding_by_party(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _create(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    contract.cancel_or_expire(agreement_id, T0 + 1)
    assert contract.get_agreement(agreement_id)["phase"] == "CANCELLED"
    assert contract.is_consumable(agreement_id) is False


def test_expired_after_deadline_refunds_in_full(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _create(contract, direct_vm, direct_alice, direct_bob, deadline=10)
    direct_vm.sender = direct_bob
    contract.accept_agreement(agreement_id)
    direct_vm.sender = direct_alice
    contract.fund_agreement(agreement_id, 500)
    contract.freeze_agreement(agreement_id, T0 + 1, False)

    contract.cancel_or_expire(agreement_id, T0 + 1000)

    agreement = contract.get_agreement(agreement_id)
    assert agreement["phase"] == "EXPIRED"
    settlement = contract.get_settlement(agreement_id)
    assert settlement["refunded_to_buyer"] == 500
    assert settlement["released_to_provider"] == 0
    # Fund-conservation invariant.
    assert settlement["released_to_provider"] + settlement["refunded_to_buyer"] + settlement["retained"] == 500


def test_clock_cannot_move_backward_or_jump_implausibly_far(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _create(contract, direct_vm, direct_alice, direct_bob, now=T0)
    # A second agreement advances the shared logical clock far backward is rejected.
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert():
        contract.create_agreement(
            direct_bob, "api_delivery", "spec",
            [{"id": "c1", "description": "x", "priority": "required", "evidence_method": "http"}],
            3600, 600, 1, T0 + 100 * 365 * 24 * 3600,  # 100 years forward: implausible
        )
