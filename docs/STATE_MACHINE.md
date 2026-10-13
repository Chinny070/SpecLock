# State machine

## Phases (as implemented, `contracts/speclock.py`)

`DRAFT → ACCEPTED → FUNDED → FROZEN → SUBMITTED → EVALUATING(implicit) → PROVISIONAL_VERDICT → (APPEALED → RE_EVALUATING → PROVISIONAL_VERDICT)* → FINALIZED → SETTLED | RECOVERY_PENDING → REFUNDED`

Side branches: `CANCELLED` (from `DRAFT`/`ACCEPTED`), `EXPIRED` (from `FROZEN` past `submission_deadline`, auto-settles as a full refund), `RESUBMISSION_REQUESTED` (from `PROVISIONAL_VERDICT`, bounded by `max_resubmissions`).

Note: there is no separate stored `EVALUATING` phase — `request_evaluation` runs the (nondeterministic) evaluation synchronously within the same call that transitions `SUBMITTED`/`RE_EVALUATING` → `PROVISIONAL_VERDICT`; this is a simplification versus the brief's illustrative phase list, made because GenVM's nondeterministic execution model does not require (or cleanly support, in Direct Mode) a separate pending-evaluation phase with asynchronous completion.

## Transition table

| From | Action | Actor | Guard | Effect | Next |
|---|---|---|---|---|---|
| (none) | `create_agreement` | buyer (caller) | profile valid, spec/criteria bounds, provider≠buyer, criteria compiled w/o duplicate ids | spec fingerprint computed, ambiguity report computed | DRAFT |
| DRAFT | `accept_agreement` | provider | phase==DRAFT | — | ACCEPTED |
| DRAFT/ACCEPTED | `cancel_or_expire` | either party | phase in {DRAFT,ACCEPTED} | — | CANCELLED |
| ACCEPTED | `fund_agreement` | buyer | phase==ACCEPTED, amount>0 | `funded_amount` set (bookkeeping, not verified escrow) | FUNDED |
| FUNDED | `freeze_agreement` | either party | phase==FUNDED; if ambiguity report non-empty, `acknowledge_ambiguity=True` required | `spec_fingerprint`/`criteria_json` now immutable for this agreement | FROZEN |
| FROZEN | `cancel_or_expire` | either party | `now > submission_deadline` | auto full refund via `_settle` | EXPIRED |
| FROZEN/SUBMITTED/RESUBMISSION_REQUESTED | `submit_evidence` | either party | evidence bounds, URL validated | receipt created (`SUBMITTED`); first submission moves FROZEN→SUBMITTED | SUBMITTED |
| SUBMITTED/RE_EVALUATING | `request_evaluation` | either party | — | evidence frozen, snapshot computed, per-criterion findings derived via consensus, `appeal_window_ends_at` set | PROVISIONAL_VERDICT |
| PROVISIONAL_VERDICT | `request_resubmission` | either party | `resubmissions_used < max_resubmissions` | — | RESUBMISSION_REQUESTED |
| PROVISIONAL_VERDICT | `file_appeal` | either party | within appeal window, `appeal_rounds_used < max_appeal_rounds` | appeal filed as `FILED_UNADJUDICATED` | APPEALED |
| APPEALED | `resolve_appeal` | either party | appeal `FILED_UNADJUDICATED` | triggers `request_evaluation` again, appeal resolved `UPHELD`/`REJECTED` | RE_EVALUATING → PROVISIONAL_VERDICT |
| PROVISIONAL_VERDICT | `finalize_verdict` | either party | appeal window closed | evaluation marked FINAL, reputation updated | FINALIZED |
| APPEALED | `finalize_verdict` | either party | appeal resolved | evaluation marked FINAL, reputation updated | FINALIZED |
| FINALIZED | `settle` | either party | `settlement_id==""` | deterministic payout split from `overall_finding`; `UNVERIFIABLE` retains funds instead of awarding either party | SETTLED or RECOVERY_PENDING |
| RECOVERY_PENDING | `recover_inconclusive` | either party | — | full refund to buyer | REFUNDED |

`TERMINAL_PHASES = {SETTLED, CANCELLED, EXPIRED, REFUNDED}`; `is_consumable()` returns False for all of these. `is_final()` additionally includes `FINALIZED`.

## Terminal fund-allocation matrix

| Terminal phase | released_to_provider | refunded_to_buyer | retained |
|---|---|---|---|
| SETTLED (overall PASS) | full `funded_amount` | 0 | 0 |
| SETTLED (overall FAIL) | 0 | full `funded_amount` | 0 |
| SETTLED (overall PARTIAL) | `funded_amount * passed/total` (integer division) | remainder | 0 |
| RECOVERY_PENDING (overall UNVERIFIABLE) | 0 | 0 | full `funded_amount` (temporary — awaiting `recover_inconclusive`) |
| REFUNDED (after recovery) | 0 | full `funded_amount` | 0 |
| CANCELLED | n/a — never funded at this phase | n/a | n/a |
| EXPIRED | 0 | full `funded_amount` | 0 |

Invariant enforced in `_settle`: `released + refunded + retained == funded_amount` exactly, checked with an assertion that reverts the whole call if violated (`test_settlement_conservation_on_pass`, `test_expired_after_deadline_refunds_in_full`, `test_unverifiable_overall_recovers_funds_without_awarding_either_party`).

## Protocol finality vs. SpecLock verdict finality

A GenVM transaction's own consensus status (`ACCEPTED`, `UNDETERMINED`, etc.) is a property of the underlying blockchain transaction and is distinct from `Agreement.phase == FINALIZED`, which is an application-level state SpecLock itself sets only after its own appeal-window/appeal-resolution guards pass. This distinction could not be exercised end-to-end against a live network from this environment (see `docs/DEPLOYMENT.md`); the guard logic itself is implemented and unit-tested, but the "protocol `UNDETERMINED` transaction must not be read as a SpecLock finalized verdict" claim rests on the fact that `finalize_verdict` never executes in such a transaction, not on a live demonstration.
