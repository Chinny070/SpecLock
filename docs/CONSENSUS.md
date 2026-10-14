# Consensus design

Two nondeterministic rounds exist in SpecLock, one per evaluation profile, both using `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)` — a custom validator function, chosen per the `genlayer-dev:write-contract` decision tree because neither round's output can be canonicalized for `strict_eq` (both depend on a live HTTP fetch or an LLM call) nor safely delegated to `prompt_non_comparative` (that would let the leader decide alone — see Anti-Patterns table in that skill).

## Round 1 — API reachability/functional check (`_probe_api_criterion`)

1. **Exact observation:** fetch `evidence.url`, classify `reachable` (`status is not None and status < 500`) and `functional` (HTTP 200 with a JSON-parseable body).
2. **Inputs/evidence snapshot:** the evidence URL frozen at `request_evaluation` time.
3. **Independent validator work:** `validator_fn` calls the *same* `fetch_and_derive()` closure again (a true independent re-fetch, not a replay of the leader's result).
4. **Fields that must agree:** `reachable`, `functional` (booleans only — exact match required).
5. **Diagnostic fields allowed to differ:** none are returned from the nondet round itself; the human-readable `rationale` string is constructed deterministically afterward in `_probe_api_criterion`, outside consensus.
6. **Non-equivalent cases:** `reachable=True,functional=True` vs. any other combination is never treated as equivalent; a validator seeing a different `status` bucket (e.g. 500 vs. 200) disagrees and forces rotation/retry per GenVM's own `run_nondet_unsafe` semantics.
7. **On failure/disagreement/parsing error:** `run_nondet_unsafe` raising is caught and mapped to `FINDING_UNVERIFIABLE` / `SUFFICIENCY_UNVERIFIABLE`, never to a fabricated PASS or FAIL.

## Round 2 — AI-agent criterion judgment (`_judge_agent_criterion`)

1. **Exact observation:** given the frozen criterion description and the list of evidence `{url, digest}` pairs (data, explicitly marked untrusted in the prompt — not instructions), produce `{finding, sufficiency, rationale}`.
2. **Inputs/evidence snapshot:** same evidence list every validator receives (frozen before evaluation).
3. **Independent validator work:** `validator_fn` calls `judge()` again — a full independent re-prompt, not a check of the leader's JSON shape alone.
4. **Fields that must agree:** `finding` (one of `PASS|FAIL|PARTIAL|UNVERIFIABLE`) and `sufficiency` (one of `SUFFICIENT|INSUFFICIENT|CONTRADICTORY|UNVERIFIABLE`) — both enums, exact match required.
5. **Diagnostic fields allowed to differ:** `rationale` (free text) is taken from whichever the leader returned; it is not consensus-critical.
6. **Non-equivalent cases:** `PASS` vs. `FAIL` on the same criterion never passes; an invalid enum value from the LLM raises (`gl.vm.UserError` with `[LLM_ERROR]` prefix) rather than being coerced.
7. **On failure/disagreement/parsing error:** mapped to `UNVERIFIABLE`/`UNVERIFIABLE`, attribution `UNKNOWN` — never silently defaulted to PASS.

## Appeal resolution precision (fixed defect)

`resolve_appeal`'s UPHELD/REJECTED determination was originally a coarse comparison of the whole evaluation's `overall_finding` against a field (`appeal.resolution_evaluation_id`) that is never populated before the resolving call itself — meaning the comparison always ran against `None` and every first-round appeal was unconditionally `UPHELD`, regardless of whether anything had actually changed. This has been fixed: `resolve_appeal` now captures the challenged evaluation's id before re-evaluating, and compares only the *specifically challenged* criteria's findings between the old and new evaluation. See `tests/direct/test_speclock_consensus.py::test_appeal_rejected_when_challenged_finding_does_not_actually_change` and `::test_appeal_upheld_when_challenged_finding_genuinely_changes`.

## Error classification used throughout

`[EXPECTED]` (deterministic business-rule violations, from `_require`), `[EXTERNAL]` (reserved for 4xx-class external API errors — not currently raised since the API evaluator classifies by status bucket rather than raising), `[TRANSIENT]` (reserved for 5xx/timeout — currently absorbed into the `reachable=False` branch rather than raised, since the contract's own design treats "unreachable" as an `UNVERIFIABLE` finding rather than a retryable exception), `[LLM_ERROR]` (malformed/invalid-enum LLM output in `_judge_agent_criterion`/`_parse_json_strict`).

## What is NOT verified

Direct Mode (`gltest`) executes only the leader closure of `run_nondet_unsafe`/mocked web/LLM calls — it does not spin up multiple validators and does not exercise `validator_fn` actually being invoked by GenVM's real consensus machinery, nor a forged-leader-vs-honest-validators scenario end to end. This is a Gate C/E gap, explicitly documented in `docs/DEPLOYMENT.md`, not claimed as tested. The `validator_fn` closures themselves are ordinary Python functions reachable and directly callable from Direct Mode tests if a future integration-test harness is added (see `tests/integration/` scaffold and its `BLOCKED_BY_RUNTIME` note).
