# Candidate release Studionet verification — 2026-10-18

## Release identity

- Network: GenLayer Studio Network, chain ID `61999`.
- Contract: `0x142A372b4cA7cf3784327DFA2e2B0eCF45D4eA14`.
- Deployment: `0x34ee57640f53c1826dc77e5900d66a81bb05f2c59fb899d4f19168b00143329e` — `FINALIZED`, `MAJORITY_AGREE`, leader `execution_result: SUCCESS`.
- Source SHA-256 at deployment: `0E7A7723C259DCF1CFAAEC8AFE62F873D6746335D63E9D8A1C2C7B25DFC4A1FE` (matches committed `contracts/speclock.py` at `b6fdb8a6e02b93acaa6d2dc942bf04b9edff96df`).
- Callable schema readback succeeded with 45 methods (20 views, 25 writes).

Every recorded main-case lifecycle write reached `FINALIZED` with leader `SUCCESS` and `MAJORITY_AGREE`. Evaluation, settlement, and claim readbacks below came from `get_evaluation`, `get_settlement`, `get_warranty_claim`, `get_milestone_summary`, and `verify_settlement_replay`. EVM withdrawal children showed `value_credited: true`; the child's `NO_MAJORITY` label is retained as returned by this runtime.

## Candidate-source positive and partial cases

| Agreement | Profile and on-chain result | Settlement/readback | Key transaction hashes |
|---|---|---|---|
| `2` | API `PASS` / `SUFFICIENT`; evidence binding `2-ev1`; expected `/json` fields matched | `100,000,000,000,000` atto released to provider; provider balance increased by exactly that amount | Evaluate `0xfc369882ad3e9ab6624b5e59c6867cea51f8833a7c9d150648ee95c380611476`; settle `0x85e4ededdaf6c1221636b2406af103b7e431e8f4fdc0733134fecad53e76fe01`; withdraw `0x9b1bf049fc9e8abacf55265c121001515b62eb9b5adb279e6fb9a6fcca8256e7`; child `0xc7d3512cbd36a25acc70a20868c710b8e7d0b31b12b55b349955c201c50fa66d` |
| `3` | API `PARTIAL`: required criterion `PASS`/`SUFFICIENT`; optional criterion `UNVERIFIABLE`/`INSUFFICIENT` because it had no JSON assertions | `50,000,000,000,000` atto released and `50,000,000,000,000` refunded; each beneficiary's wallet rose by exactly its half; replay matched | Evaluate `0x1b715472efa308cf14820b2820453c795520939d931b9eadf25b755dcd484391`; settle `0x5dc4c281507bba3e51265e3619473fc8413fc234df56e7bd3e2df3aa3a7458e4`; provider withdrawal `0x31b39744b7934d9eebd55c264dd149dbff142cfb42dec363f5103c4233d3b9b8`; buyer withdrawal `0x29e10ac4d35b83321ae29e09289faf50e291720d236f37cc412f4070a91b4532` |
| `4` | API `PASS`/`SUFFICIENT`; a correctly hashed `/status/500` receipt was submitted before the frozen `/json` receipt; the evaluation bound only `4-ev5` at `/json` | 20% (`20,000,000,000,000` atto) held back; unrelated-URL warranty claim rejected with empty claim ID and exact bond refund; valid claim against the original `/json` subject resolved `REJECTED`; provider withdrew `102,000,000,000,000` atto and buyer withdrew the refunded `2,000,000,000,000`-atto hostile-claim bond | Evaluate `0xfde3624367e1ee2ef2a28a3280a379d7c4e07f0a83722c03742853bd148536d2`; settle `0x987364547f7630278c3512c6856e1ae194b71a87c24137c22ae2b6249d615536`; hostile claim `0xed6811afc414ed6ab750d12eb14f3302b0c8b27a25b0f9386466563ff830e8f9`; valid claim `0x38a785c875aed395b3bcb8f5f0e0b1b7ae25c728873f84118fb26e6429c3a381`; resolve `0x5844530d79451a48d8214da3ea4bc28b06016c294267c4c756d03491fe367b51` |
| `5` | Milestone `5-ms1` evaluated `PASS`/`SUFFICIENT`; both parties accepted the milestone economics and separately finalized it | Aggregate summary: one of one complete; `is_final:true`; replay `matches_recorded_settlement:true`; provider received exact `100,000,000,000,000` atto | Evaluation `0x3b60987746bf349db9b7e3e6ce68b458fb7bfaa76e1419f6962527864f42b3e0`; settle `0x3575a020b9271e3b8035daf7ade0524b561d211229db90dced0f47f86224efe1`; withdrawal `0x096c0ec1be94e660bfaa350d7631d649e7a645e42e87bb0c130204b43de894fc` |
| `6` | AI-agent profile `PASS`/`SUFFICIENT`; fetched `/json` body contained the slideshow title and slides array | `100,000,000,000,000` atto released; provider balance increased by that exact amount | Evaluate `0xe8baba60fe22f9dbb4f563779ed7f3420cc14b94221cbb06992ce1f236ce14a4`; settle `0x42951a2660397bf467fa96839d05534bf88effb5ff8bfc24a6877872651947aa`; withdraw `0x3f892449bdde86e7436f4567293baa3eb99aa6aa18bfec00d90922c1dde96647` |

Additional negative calls finalized with `MAJORITY_AGREE`/`ERROR` and did not mutate their protected state: configuring milestones after warranty, and configuring warranty after milestones. The provider's economic acceptance preceded freeze in the warranty and milestone cases. Direct Mode tests cover pre-freeze milestone-evaluation rejection and both economic-configuration orders.

## Candidate-source negative cases and complete transaction log

Agreements `8` and `9` provide a complete per-transaction record in [`studionet-negative-regressions-2026-10-18.json`](studionet-negative-regressions-2026-10-18.json). The log records transaction hashes, finality, validator outcomes, readbacks, child-transfer credits, and wallet deltas.

- Agreement `8` (API): the live `/json` body was HTTP 200 but failed a deliberately incorrect expected-title assertion. On-chain result was `FAIL`/`SUFFICIENT`; the finalized settlement refunded the full `100,000,000,000,000` atto and the buyer's exact balance delta matched.
- Agreement `9` (AI-agent): the contract fetched the live plain-text `/robots.txt` artifact; the model's rationale identified the actual body and its absence of the required JSON slideshow. On-chain result was `FAIL`/`SUFFICIENT`; settlement refunded the full `100,000,000,000,000` atto and the buyer's exact balance delta matched.

## Incomplete probes and accounting

- Agreement `1` is a DRAFT created by an earlier runner; agreement `7` is ACCEPTED but unfunded. Both have zero funded amount and do not lock contract funds.
- A Studio Network RPC transport timeout interrupted agreement `7` after acceptance. A readback confirmed `funded_amount:0`; the candidate contract balance is `0`. No write was resubmitted when the status was uncertain.
- The signing material for generated test actors was held only in process memory and was lost when two runners exited. Their residual balances were read back: first pair `0.001` GEN each; core lifecycle pair `0.000548` and `0.001452` GEN; negative-regression pair `0.001` GEN each. No signer secrets were written to disk or chat; these residual testnet amounts are not represented as recovered.
- Historical tracked transfer principal before this candidate was `0.00963` GEN. The candidate pass moved `0.007408` GEN in gross native transfer volume (top-ups, deposits/bonds, and settlement withdrawals), for `0.017038` GEN recorded cumulative volume. The configured sponsor wallet's observed balance fell by exactly `0.006` GEN for the six test-account top-ups. Studio Network reported `gasPrice: 0` on those transfers and no fee deduction was observed; older transaction fees were not itemized. The remaining `0.002962` GEN is a nominal margin before any unrecorded fees, so this is not certified as exact fee-inclusive accounting.

## Scope of the result

This source-specific run verifies API success/failure, sufficiency-aware PARTIAL settlement, agent success/failure, real escrow funding and withdrawals, warranty anti-redirection and claim resolution, and a successful milestone lifecycle/replay. The latest change's bilateral ambiguity acknowledgement was not separately exercised on-chain; it remains local-test verified. Exact runtime-clock deadlines remain unavailable, source-ownership independence remains heuristic, malicious-validator rejection is not externally forceable, and a failed EVM child payout has no callback to restore claimable state. Earlier deployment evidence remains historical and is not presented as a transaction against this candidate.
