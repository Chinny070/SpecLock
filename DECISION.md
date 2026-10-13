# DECISION.md

## Repository state at start

- `origin` = `https://github.com/Chinny070/SpecLock.git`, confirmed via `git remote -v`.
- Starting HEAD: `be10f8b` ("Initial commit"), branch `main`, single file `README.md` (10 bytes). No prior contract, tests, or docs existed — this is a from-scratch build, not a continuation.
- Backup branch `backup/pre-finalisation-be10f8b` created from `be10f8b` and pushed to `origin` before any other change.

## Product decision (fixed by the brief, recorded here for traceability)

SpecLock is one canonical GenLayer Intelligent Contract (`contracts/speclock.py`) implementing a universal digital-delivery agreement/adjudication primitive, with two fully-implemented evaluation profiles: **API delivery** and **AI-agent delivery**. No marketplace frontend, database, or off-chain adjudicator was added — only the contract, Direct Mode tests, fixtures, and docs.

## Toolchain actually present in this environment

- Python 3.12.10, `genlayer-test` 0.29.2 (`gltest`/`glsim`), `genvm-linter` 0.11.1rc2, `genlayer-py` 0.16.3, `gh` 2.95.0, git 2.53.0.
- No standalone `genlayer` SDK package is installed by pip (the name is squatted on PyPI as an unrelated 1.3KB placeholder — confirmed by installing and inspecting it, then removing it). The real contract-authoring SDK (`genlayer.gl`, `genlayer.py`) is fetched on demand by `genvm-linter` and `gltest` from `https://github.com/genlayerlabs/genvm` releases and cached under `~/.cache/genvm-linter` and `~/.cache/gltest-direct`. This download succeeded in this environment (network access to github.com was available), landing runner `py-lib-genlayer-std` versions including the one matching the pinned `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6` dependency header used in the contract.
- No GenLayer network RPC credentials, funded signer, or Studio/testnet access were available or requested in this session. Gate E (Studionet) is therefore `BLOCKED` — see `docs/DEPLOYMENT.md`.

## Material findings that shaped the design (discovered empirically, not assumed)

1. **No block timestamp is exposed to contract code.** `gl.message` (via `genlayer.gl.MessageType`) exposes only `contract_address`, `sender_address`, `origin_address`, `value`, `chain_id` — there is no `timestamp`/`datetime` field reachable from inside a contract in the installed runner. This was discovered by tracing `genlayer/gl/__init__.py` and `genlayer/_internal/msg.py` in the downloaded SDK, and confirmed by a failing Direct Mode test. Consequence: deadlines/appeal-window logic cannot use a native wall clock. SpecLock instead takes a caller-supplied `now: int` (unix seconds) on every time-gated write call, which the contract advances through a strictly monotonic, bounded-forward-jump logical clock (`SpecLock._advance_clock`). This is **not** a verified trusted oracle — see `docs/GENLAYER_CAPABILITIES.md` and `docs/THREAT_MODEL.md` for the exact trust boundary this accepts.
2. **`gl.message.sender_account` does not exist** — the correct field is `sender_address`. This was caught by a failing Direct Mode test, not by inspection alone.
3. **Address-typed public method parameters can arrive as raw `bytes`** after the Direct Mode harness's calldata round-trip in this installed version, rather than a reconstructed `Address`. The contract defensively coerces with `_as_address()` at every public-method Address parameter boundary rather than assuming the SDK always hands back a typed object.
4. **`DynArray`/nested `TreeMap` values cannot be constructed directly** (`DynArray[str]()` raises `TypeError: this class can't be instantiated by user`), and a `TreeMap.__getitem__` on a missing key raises `KeyError` rather than auto-vivifying. The working pattern is `TreeMap.get_or_insert_default(key)`.
5. **`from __future__ import annotations` breaks ABI schema extraction.** With it active, all type hints become strings at runtime, and GenLayer's `get_schema()` (which reads `inspect.signature(...).annotation` directly, not via `typing.get_type_hints`) cannot resolve them — `genvm-lint validate` fails with "couldn't get schema" pointing at the first public method alphabetically, which is misleading about the real cause. The contract does not use that import.

These are recorded here because they are not obvious from the public docs pages and materially changed both the contract's time-handling design and its defensive coding style.

## What this build does NOT claim

- No verified native-value escrow. `fund_agreement` records a bookkeeping `funded_amount`; see the module docstring in `contracts/speclock.py` and `docs/GENLAYER_CAPABILITIES.md`. Settlement is explicitly `NON_CUSTODIAL / NOT VERIFIED`.
- No live network deployment, no consensus/validator-disagreement test has been run against real multi-validator infrastructure (Direct Mode only exercises the leader path). See `docs/DEPLOYMENT.md` for the exact blocked gates.
- Not all 38 numbered capabilities are `IMPLEMENTED_VERIFIED`. See `docs/FEATURE_MATRIX.md` for the per-capability status; several Tier 2/3 capabilities are `PARTIAL` or `NOT_IMPLEMENTED` and are described honestly rather than padded to a "38/38" claim.
