"""AI-agent delivery profile acceptance scenarios (Gate B).

Maps to docs/ACCEPTANCE_TEST_MATRIX.md rows: Agent positive, Agent negative,
Agent uncertain, Independence.

Direct mode runs the leader function only (see docs/TESTING.md); it proves
parsing, bounds, and the deterministic settlement/lifecycle wiring around
the judgment. It does NOT exercise the validator disagreement path — that
requires the integration/consensus gate (tests/integration, Gate E), which
is documented as BLOCKED_BY_RUNTIME in docs/DEPLOYMENT.md for this
environment (no funded network access).

No wall-clock time is used anywhere (see contracts/speclock.py time note).
"""

import hashlib
import json

CONTRACT = "contracts/speclock.py"


def _setup_frozen_agent_agreement(contract, direct_vm, buyer, provider):
    direct_vm.sender = buyer
    agreement_id = contract.create_agreement(
        provider,
        "ai_agent_delivery",
        "Agent must summarize the attached document in under 200 words with no fabricated citations.",
        [{"id": "c1", "description": "Summary is under 200 words and cites only sources present in the source document", "priority": "required", "evidence_method": "artifact:c1"}],
        1,
    )
    direct_vm.sender = provider
    contract.accept_agreement(agreement_id)
    direct_vm.sender = buyer
    contract.fund_agreement(agreement_id, 800)
    contract.freeze_agreement(agreement_id, False)
    return agreement_id


def _submit(contract, direct_vm, submitter, agreement_id, url):
    direct_vm.sender = submitter
    digest = hashlib.sha256(url.encode()).hexdigest()
    return contract.submit_evidence(agreement_id, url, digest, json.dumps({"criterion_id": "c1"}))


def test_agent_positive_compliant_output_passes(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agent_agreement(contract, direct_vm, direct_alice, direct_bob)
    _submit(contract, direct_vm, direct_bob, agreement_id, "https://artifacts.example.com/summary.txt")

    direct_vm.mock_llm(
        r".*adjudicating.*",
        json.dumps({"finding": "PASS", "sufficiency": "SUFFICIENT", "rationale": "Summary is 150 words and all citations trace to the source document."}),
    )

    direct_vm.sender = direct_bob
    evaluation_id = contract.request_evaluation(agreement_id)
    evaluation = contract.get_evaluation(evaluation_id)
    assert evaluation["overall_finding"] == "PASS"


def test_agent_negative_hallucinated_citation_fails(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agent_agreement(contract, direct_vm, direct_alice, direct_bob)
    _submit(contract, direct_vm, direct_bob, agreement_id, "https://artifacts.example.com/summary.txt")

    direct_vm.mock_llm(
        r".*adjudicating.*",
        json.dumps({"finding": "FAIL", "sufficiency": "SUFFICIENT", "rationale": "Summary cites a source not present in the original document."}),
    )

    direct_vm.sender = direct_bob
    evaluation_id = contract.request_evaluation(agreement_id)
    evaluation = contract.get_evaluation(evaluation_id)
    assert evaluation["overall_finding"] == "FAIL"
    assert evaluation["failure_attribution"] == "DELIVERY"


def test_agent_uncertain_malformed_llm_output_is_unverifiable_not_fabricated(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agent_agreement(contract, direct_vm, direct_alice, direct_bob)
    _submit(contract, direct_vm, direct_bob, agreement_id, "https://artifacts.example.com/summary.txt")

    # LLM returns an invalid enum value -- must not be silently coerced to
    # PASS or FAIL; the contract must raise and the evaluation must land on
    # UNVERIFIABLE rather than fabricate a result.
    direct_vm.mock_llm(r".*adjudicating.*", json.dumps({"finding": "MAYBE", "sufficiency": "SUFFICIENT", "rationale": "unclear"}))

    direct_vm.sender = direct_bob
    evaluation_id = contract.request_evaluation(agreement_id)
    evaluation = contract.get_evaluation(evaluation_id)
    assert evaluation["overall_finding"] == "UNVERIFIABLE"


def test_agent_missing_artifact_without_independent_evidence_is_unverifiable(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agent_agreement(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_bob
    contract.submit_evidence(agreement_id, "https://artifacts.example.com/unrelated.txt", hashlib.sha256(b"x").hexdigest(), json.dumps({"criterion_id": "unused"}))

    evaluation_id = contract.request_evaluation(agreement_id)
    evaluation = contract.get_evaluation(evaluation_id)
    assert evaluation["overall_finding"] == "UNVERIFIABLE"
    assert evaluation["findings"][0]["attribution"] == "EVIDENCE"


def test_multiple_urls_same_control_not_auto_independent(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Capability 19 (independence/corroboration): the current implementation
    does not claim multi-source independence verification beyond requiring
    each criterion's judgment to be independently rerun by every validator
    against the same evidence list. Submitting two URLs under the same
    submitter/role is accepted as evidence but does NOT automatically
    upgrade sufficiency -- the judge call still receives both and must reason
    over them explicitly. This test documents that behaviour rather than
    asserting a corroboration feature that is not implemented (see
    docs/FEATURE_MATRIX.md, capability 19: PARTIAL)."""
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agent_agreement(contract, direct_vm, direct_alice, direct_bob)
    _submit(contract, direct_vm, direct_bob, agreement_id, "https://artifacts.example.com/summary.txt")
    _submit(contract, direct_vm, direct_bob, agreement_id, "https://artifacts.example.com/summary-mirror.txt")

    direct_vm.mock_llm(
        r".*adjudicating.*",
        json.dumps({"finding": "PARTIAL", "sufficiency": "INSUFFICIENT", "rationale": "Both sources share one submitter; cannot corroborate independently."}),
    )
    direct_vm.sender = direct_bob
    evaluation_id = contract.request_evaluation(agreement_id)
    evaluation = contract.get_evaluation(evaluation_id)
    assert evaluation["findings"][0]["sufficiency"] == "INSUFFICIENT"


def test_agent_judge_actually_fetches_and_includes_real_evidence_content(direct_vm, direct_deploy, direct_alice, direct_bob):
    """Regression test for a real gap found while preparing a live Studionet
    demo: an earlier revision of _judge_agent_criterion never fetched the
    evidence URL at all, passing only {url, digest} metadata to the LLM. The
    mock_llm prompt-pattern match only succeeds if the real fetched body
    text below appears in the prompt handed to gl.nondet.exec_prompt, so
    this fails against the old (metadata-only) implementation and passes
    against the fixed one."""
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agent_agreement(contract, direct_vm, direct_alice, direct_bob)
    _submit(contract, direct_vm, direct_bob, agreement_id, "https://artifacts.example.com/summary.txt")

    unique_marker = "UNIQUE-MARKER-57f3a9-this-text-must-reach-the-llm-prompt"
    direct_vm.mock_web(r".*artifacts\.example\.com/summary\.txt.*", {"status": 200, "body": f"Summary content. {unique_marker}"})
    direct_vm.mock_llm(
        rf".*{unique_marker}.*",
        json.dumps({"finding": "PASS", "sufficiency": "SUFFICIENT", "rationale": "Real fetched content was present and reviewed."}),
    )

    direct_vm.sender = direct_bob
    evaluation_id = contract.request_evaluation(agreement_id)
    evaluation = contract.get_evaluation(evaluation_id)
    assert evaluation["overall_finding"] == "PASS"


def test_agent_unreachable_evidence_fetch_does_not_crash_judgment(direct_vm, direct_deploy, direct_alice, direct_bob):
    """If an evidence URL can't be fetched, judge() must still run (the LLM
    sees reachable=False and an empty excerpt) rather than raising -- the
    contract should never crash a whole evaluation because one evidence URL
    went down."""
    contract = direct_deploy(CONTRACT)
    agreement_id = _setup_frozen_agent_agreement(contract, direct_vm, direct_alice, direct_bob)
    _submit(contract, direct_vm, direct_bob, agreement_id, "https://artifacts.example.com/summary.txt")

    direct_vm.mock_web(r".*artifacts\.example\.com/summary\.txt.*", {"status": 503, "body": ""})
    direct_vm.mock_llm(
        r".*adjudicating.*",
        json.dumps({"finding": "UNVERIFIABLE", "sufficiency": "UNVERIFIABLE", "rationale": "Evidence source was unreachable at evaluation time."}),
    )

    direct_vm.sender = direct_bob
    evaluation_id = contract.request_evaluation(agreement_id)
    evaluation = contract.get_evaluation(evaluation_id)
    assert evaluation["overall_finding"] == "UNVERIFIABLE"
