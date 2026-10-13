# Protocol

## North star

Given a frozen agreement, admissible independently-verifiable evidence, and a versioned evaluation policy, which criteria of a digital deliverable were satisfied, and which pre-agreed deterministic remedy follows after bounded review and finality?

## Core pattern

Non-deterministic (validator-adjudicated) execution answers **"what evidence supports each frozen criterion?"** Deterministic contract code answers **"what transitions or payments does that finding authorize?"**. The nondeterministic path (`_probe_api_criterion`, `_judge_agent_criterion`) never picks a settlement recipient, invents an amount, sets a deadline, or bypasses an authorization check — see `_derive_overall` and `_settle` for where deterministic code alone converts findings into amounts.

## Three independent downstream consumers this interface supports

1. **Freelance/API escrow** — a buyer commissions an API integration; `create_agreement` with `profile="api_delivery"`, evidence = the live endpoint, settlement follows `overall_finding`.
2. **AI-agent task marketplaces** — a requester posts a bounded agent task; `profile="ai_agent_delivery"`, evidence = the agent's public/committed artifact and trace URLs.
3. **Grants / bounty programs with objective or semantically-checkable milestones** — the same `Agreement`/`Evidence`/`Evaluation`/`Appeal`/`Settlement` machinery, with the grantor as buyer and the grantee as provider; the `priority: "optional"` criterion field and `PARTIAL` settlement math already support partial-credit milestone-like payouts without a separate contract.

All three consume the same typed public API (Section 7 of the brief) — `create_agreement` → `accept_agreement` → `fund_agreement` → `freeze_agreement` → `submit_evidence`(*) → `request_evaluation` → (`file_appeal` → `resolve_appeal`)* → `finalize_verdict` → `settle`/`recover_inconclusive`.

## What is semantic vs. deterministic

- **Semantic (validator-adjudicated):** per-criterion finding/sufficiency/rationale for both profiles (`_probe_api_criterion`, `_judge_agent_criterion`).
- **Deterministic:** authorization (`_is_party`, `_require`), lifecycle transitions (every `phase` check), bounds (Section 6 constants), the specification compiler/ambiguity detector (`_compile_criteria` — rule-based, not LLM-based, so it is fully deterministic), overall-finding derivation (`_derive_overall`), settlement math (`_settle`, `settle`), appeal admissibility and round bounds, and the logical clock (`_advance_clock`).

## GenLayer load-bearing requirement

Every per-criterion judgment is wrapped in `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)`, where `validator_fn` independently re-executes the same observation/judgment task (re-fetch for API, re-prompt for agent) and compares only the decision-critical fields (`reachable`/`functional` for API; `finding`/`sufficiency` for agent), per the Equivalence Principle guidance in `docs/CONSENSUS.md`. No leader-output-only (schema-shape-only) validator is used anywhere in this contract.

See `docs/STATE_MACHINE.md` for the full transition table and `docs/EVALUATION_PROFILES.md`-equivalent material folded into `docs/CONSENSUS.md` and `contracts/speclock.py` docstrings for the two evaluation profiles.
