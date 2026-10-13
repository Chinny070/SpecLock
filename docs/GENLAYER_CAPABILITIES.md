# GenLayer capabilities actually confirmed in this environment

Status legend: **CONFIRMED** (observed directly, Direct Mode or SDK source), **UNVERIFIED** (never exercised from this environment), **UNSUPPORTED/ABSENT** (confirmed missing or broken).

| Capability | Status | Evidence |
|---|---|---|
| `gl.Contract` / `@gl.public.write` / `@gl.public.view` | CONFIRMED | `contracts/speclock.py` loads, lints, and 32 Direct Mode tests pass. |
| `gl.message.sender_address`, `.contract_address`, `.origin_address`, `.value`, `.chain_id` | CONFIRMED | `genlayer/gl/__init__.py` `MessageType`; exercised in every test. |
| `gl.message` timestamp/datetime field | **ABSENT** | `MessageType` has no time field in the installed `py-genlayer` runner (hash `1jb45...`). Confirmed by reading the cached SDK source and by a failing test when the contract first called a nonexistent `gl.message.timestamp`. See `DECISION.md` item 1. |
| `gl.vm.UserError` | CONFIRMED | Used throughout; required by `genvm-lint check` (bare `Exception` raises a warning). |
| `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)` | CONFIRMED present in SDK, **UNVERIFIED under real multi-validator consensus** | Imported and called in `_probe_api_criterion` / `_judge_agent_criterion`; Direct Mode only runs the leader path (`genlayer-dev:direct-tests` skill: "Direct mode runs leader function only — validator logic is not exercised"). No integration/consensus run was performed (no funded network — Gate E blocked). |
| `gl.nondet.web.get` | CONFIRMED (mocked) | `direct_vm.mock_web` intercepts it in tests; never called against a live network from this environment. |
| `gl.nondet.exec_prompt` | CONFIRMED (mocked) | `direct_vm.mock_llm` intercepts it in tests; never called against a live LLM backend from this environment. |
| `gl.eq_principle.strict_eq` / `prompt_comparative` | UNVERIFIED | Not used in the shipped contract — the custom-validator pattern (`run_nondet_unsafe`) was chosen deliberately per the `genlayer-dev:write-contract` skill's decision tree, since neither API reachability nor agent-task judgment can be safely reduced to `strict_eq` (nondeterministic) or treated as leader-output-only (`prompt_non_comparative` would let the leader decide alone). |
| Native value transfer / escrow (`gl.message.value`, payable methods, real balance movement) | **UNVERIFIED**, not exercised | `gl.message.value` field exists in the schema; no payable method was implemented and no transfer was executed against a funded account or live network. `fund_agreement` is explicitly bookkeeping-only — see module docstring in `contracts/speclock.py`. |
| Cross-contract calls (`gl.get_contract_at`, `gl.deploy_contract`) | UNVERIFIED | Not used; SpecLock is single-contract by design (per brief). |
| `genvm-lint check` / `validate` | CONFIRMED | Both run clean with 0 errors, 0 warnings against the final contract (see `docs/TESTING.md`). |
| GenLayer Studio / testnet RPC connectivity | **UNVERIFIED** | No RPC URL, signer, or funded account was available or supplied in this session. Gate E is `BLOCKED`, not green and not claimed green. |
| `gltest` Direct Mode harness (`direct_vm`, `direct_deploy`, mocks, cheatcodes) | CONFIRMED | 32/32 tests pass; see `docs/TESTING.md`. |

## Deadline / time-source conclusion

GenLayer's documented web-access and equivalence-principle pages were consulted conceptually, but the determining fact here is empirical: the installed runner's `gl.message` struct carries no timestamp. SpecLock's deadline and appeal-window logic is therefore driven by a caller-supplied `now` parameter checked against a contract-wide monotonic logical clock (`SpecLock.clock`, `_advance_clock`). This is a deliberate, inferior-to-ideal substitute for a verified on-chain time source, documented as a known trust boundary in `docs/THREAT_MODEL.md`, not represented as a verified oracle.
