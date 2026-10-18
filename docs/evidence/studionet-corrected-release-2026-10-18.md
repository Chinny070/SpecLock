# Corrected-release Studionet evidence — 2026-10-18

This ledger covers the deployed source SHA-256 `AFCDF4D9841F5F170644586A564DB4740961280654E0545F6B6C2C65E8C8734D` at
`0xCEE0430CcC760f1Dce94d2E416CbeCe2b1CB8c79`, Studio Network chain ID `61999`. Deployment transaction:
`0xc4f1be49ed4f0af80e12e6abc4d2b16f5d3e9acc2bf26c8a4ed2c20146148312`; deployment finalized with `MAJORITY_AGREE`
and leader execution `SUCCESS`. All lifecycle parent transactions below were awaited to `FINALIZED`; successful writes
reported `MAJORITY_AGREE` and `SUCCESS`. Expected negative calls finalized with `ERROR` and the indicated guard.

## API profile

| Agreement | Finding read from chain | Evaluation tx | Settlement tx and result | Withdrawal tx / balance delta |
|---|---|---|---|---|
| `2` | `PASS`, `SUFFICIENT`; live `/json` response matched the frozen JSON assertions | `0x889f9daba34488e1cdfa5622b39e5ccaacb28e5ab4e7715c190eb4f0ca3d645f` | `0x92fd8762ee881c6023deb3f7456a436cc731bfa1ccdd19424c7d7788c4274faa`; 50,000,000,000,000 atto released | `0xf54eceb1eb2f1258b932a314dd8d4cf6b03c83a1df28341d2da4b36a584fbc9a`; provider +50,000,000,000,000 atto |
| `3` | `FAIL`, `SUFFICIENT`; HTTP 200 but JSON failed frozen expected fields | `0xd0af855d02036f4568ff3b874088ec5eff9d48a68ace56694ab8e5bb22a445f1` | `0xe34c98bf9031a203bb9d7c0535b9099d6ea4790137daacee5479ae9898d68a7c`; 50,000,000,000,000 atto refunded | `0x51c9c49e3b304f3de64c8366b2dff0e8cf43c2bdb5c8143a655a6c93dcaa0ef8`; buyer +50,000,000,000,000 atto |

Agreement `2` lifecycle hashes: create `0x9c43f4a85efae5677abe6251471aef39813d1a284cf45233a6c30f86476b5fb1`; accept
`0x0ece68a845fa9966bea674d968e8254b70d16bbf3f024d04912a7b37d49751cf`; fund
`0x1cd46094f0e48aae7856de900cb1fe901b698e305dfb155f86a727aa95a6ab7b`; freeze
`0xf67c513dbf529ed44ce60e56b3a76d0deaac566270814ab9acbf2668bf2ffcc0`; evidence
`0x15c4b724e8cdebeb23153649d31359fd63d8bd2d6eea2d5b986af1a8b7888c19`; finalizations
`0x13da6e3763ef42e4c1ec1f992b507c1d2ed50ba8ff88b4e851dc09ee3f750479` then
`0x30cde4ced03941ed05c2df20c0a60792d936458aa57c34d7bb49ecbf8ec0d507`. Double withdrawal
`0x3e5d5b3fbc515be4cf9ec5330f98f5f0909dbeee6cc961c950edce7842f020f3` finalized with expected `ERROR`.

Agreement `3` lifecycle hashes: create `0xb960d5d3f457585af28df21ff8136e50e4fe768824dfc537838850a23cf87e21`; accept
`0xb183376aea08d5f2fee79651b1f9a4c895b6e416e40eed61f8bf433b3b215f6a`; fund
`0x0fa7ec403258e975852fe4f7fc1389035120cc44285878062848e775c183c6d9`; freeze
`0xc245bbc368cc33b47acc4cd7002196cdb38180d004f7ed3ccff769a802767400`; evidence
`0x653ba6c269f9af8221447169a7583017044f8715af2db5ea00338edd87817dc7`; finalizations
`0x53961b2aed9c197dbf7590b1d49d0335540994dd3f9ffa69826bdd61dd4e342f` and
`0x19616e0293563041c5276473ed5ee6f9aa6ea992c9313cc0a9f7e25dab46afa0`. Double-withdrawal transaction was rejected;
`0x7cddc10aa284e62bd3a738be491dc64ed6e658cd2fdd90a3d358151ddd3bb4fc` finalized with expected `ERROR`.

## AI-agent profile

| Agreement | Finding read from chain | Evaluation tx | Settlement tx and result | Withdrawal tx / balance delta |
|---|---|---|---|---|
| `4` | `PASS`, `SUFFICIENT`; fetched `https://httpbin.org/robots.txt` supported the frozen assertion | `0xaffd0fb32747b3796b9e676a6396520c484b72dee33c9f4560d933b71c69c64b` | `0x1bc0d28b19b49fbdf5f90cc974487efe52a03cd35d46bb1109ec0ce5d2d0335d`; 50,000,000,000,000 atto released | `0xb788ff51cac4b9d501d9cd98f54d13074ea86ec7d14c7b81d966633aa03113cc`; provider +50,000,000,000,000 atto |
| `5` | `FAIL`, `SUFFICIENT`; fetched robots content did not satisfy the `SpecLockBot` assertion | `0xea42b6fb8e562608b279de37a66853892d30a958760de79cfc400474c516194f` | `0x26e529125a4e05083ee5388ff59ac375d50f707cb4f460798478752ef1a668ae`; 50,000,000,000,000 atto refunded | `0xfec7d280b3ba5a2559ee332caac8953d277185d6e8981fada92ec77bb9966150`; buyer +50,000,000,000,000 atto |

Both duplicate withdrawals were rejected: agreement `4` tx `0x88eba3aeb997b4c0ca383ab20cef62e700748012945a9119826085a9ab884f5f`; agreement `5` tx
`0xefa8fc4cc2e0faa169f41cbc0b599ac5bdc26e4cf8c750a3091b1d20d0c573ff`.

## Warranty anti-redirection and claim resolution

Agreement `7` was funded and settled with a 10,000,000,000,000-atto warranty holdback. A hostile claim referenced the
unrelated `/status/200` URL and supplied the actual SHA-256 of its empty response; transaction
`0x3e0d02fff2cb8ed14b0a2590d209c97113d2b4f89aa4a18957484963bb74ff4a` returned an empty claim ID and credited the exact
1,000,000,000,000-atto bond back to the caller. The holdback did not move. A valid claim against the original frozen
`/json` URL was filed as `7-wc1` with the actual fetched digest (`0x8a98636181fd5e656405003dc838e6a1f82174ba0cdc01ce647a7a760050a283`)
and resolved `REJECTED` by `0x935143caf31a6133d3a86a97d3ea2d449579f0b2f3fd2d2ed339b1ad9101123b`. Final warranty state was
`RELEASED`. Buyer withdrawal `0x961a4e956e915d0f9addf8b6e85d3660f59e94726f070ac6f7af9bc49979c13c` credited 1,000,000,000,000
atto; provider withdrawal `0x6632ab6ba1a4360c16351b75061ef1076717c4fcbf717816cb60f86eb97f3950` credited 51,000,000,000,000
atto. Each EVM child receipt showed `value_credited:true`; both claimable balances read back as zero.

## Milestone lifecycle, bilateral terms, and views

Agreement `10`, milestone `10-ms3`, was funded with 50,000,000,000,000 atto and evaluated `PASS`/`SUFFICIENT` against a
real `/json` response. Creation `0x47d0d97f8218f39dd61dbe5aeb1f03e3b862d37580e4906f8ec8320e6f50b1a9`; funding
`0x7ad696980dbfcb8b31d9498c52d2293c24ca084a7de1fa8c71c54c71e1aaf96e`; milestone definition
`0x5d58f353caefc4d7d9a6f49cf0871e301ff54a30218cfe0516aea3a79c972e24`. Freeze before provider economic consent was rejected
(`0x2013bc3a5ca0aff4bb05b3903e2f0ec022c9b4557cc2ce56267e167255ecf3a7`); evaluation before freeze was rejected
(`0x18232fa315540aef139f8f2046f460213a926f4cd0d438d01b1e8966eae9ccc2`). Provider consent
`0xb4be6f1b513c6f114fa7f4bb79b1ea642a4e1918323d24215904f4029d29253d`, freeze
`0xc5465a56cd7961981ebcec7c1586b2a241b314e42ee40e0f206169ef00c2fd2d`, evidence
`0x118bdfda629277f71a2aa69c8ce04a8b7d04201a4665eec6af7c7316aaeb4db1`, and evaluation
`0xbd3aac62a65fb2d31f9758b487df6fa8258453e1f928a193f3294a7bcf201ace` finalized successfully. Milestone consent calls were
`0x79d3a229e69ac296c5d18227ff297567012029dd9e0568016f541f67b7a40239` (false) and
`0xbda6f61527babea0a04f8721fd80bfa3059066d88f67b87deeb8a2fcf6021e25` (true). An outsider withdrawal was rejected by
`0xa0189501e35322d1fde21f221d7e27145915789bd2b33a35410ce76145762fe7`. Settlement
`0x3f27de4b8955f61387a540c4a4c9dc52cc8ef0b5e5449125976913099e507013` released all 50,000,000,000,000 atto;
`get_milestone_summary` returned `all_complete:true` and replay returned `matches_recorded_settlement:true`. Provider withdrawal
`0xf3297ae9afe2c26df7fa95f20bb8b173212cbcf7bea4b3aee5c216670f389603` increased provider balance by exactly 50,000,000,000,000
atto; duplicate withdrawal `0x44fa8dfbef6e4c43e58dcc69e28c3120b9eafd8e6aefaa5889b3a0ac66d8f327` was rejected.

## Recovery-aware settlement replay

Agreement `11` submitted evidence for live `https://httpbin.org/status/503`; the observed HTTP response was 503 with an
empty body (SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). Evaluation
`0xd7c2494d35c01a094c24da81a18d48a66900cdee2e0d82fd7c9655f567fa4832` read `UNVERIFIABLE`. Both finalizations
(`0x03f47fbc9d4ec1855875f2b9e5f64c1d74375a4382866822531fc3371428bb4b`,
`0xbac0a7e496ee14e0cb5dcf851a6f4ae30f7fe288de1371ad5889e5dd20595e42`) succeeded. Settlement
`0x135e8a5048a045ba325ae2a3bb808a6b8cf8f1d4885c09e7418681ba2412b3f0` entered `RECOVERY_PENDING`; recovery
`0xa2db859adc28015b6e72f24c8e1db02f990a55106ecd2e3608a20e12767c1e31` moved it to `REFUNDED`. Replay returned
`matches_recorded_settlement:true`, `recovery_applied:true`, and the exact 50,000,000,000,000-atto refund. Buyer withdrawal
`0x9cfdcd518cafd4b0e6f0bc1243b8e13dd9b965a5976ad6bd7cb357f6a40590b1` increased buyer balance by exactly 50,000,000,000,000
atto.

## Normal-evaluation digest enforcement and sufficiency gate

Agreement `12` used live `https://httpbin.org/json` (HTTP 200; fetched body SHA-256
`bab3dfd2a6c992e4bf589eee05fc9650cc9d6988660b947a7a87b99420d108f9`). Criterion `digest-case` committed a deliberately
different digest (`275291ade75b3b7abb15f921b32a12c1d6cf3a6a0355ed6fb24a255caac9f9d7`); criterion `insufficient-case`
committed the actual fetched digest but defined no `expected_json` assertion. Evaluation
`0x53e1b0963c1186b535cb1812ed204c8c3c058141cefb2dd6dfb68ed77a994f87` read `UNVERIFIABLE` overall. The first finding
was `UNVERIFIABLE` / `EVIDENCE` with rationale “fetched evidence does not match the committed digest”; the second was
`UNVERIFIABLE` / `INSUFFICIENT` with rationale “API criterion has no expected_json assertions”. Thus neither integrity-
violating content nor insufficient criteria produced a payable PASS. Evidence submissions were
`0xadda7f496746b8e2224dc16a9997184646bccec1f9a1083e547c4df52a6c87a4` (wrong digest) and
`0xda2a4ee3f0b534baaa9dd473552d602014c0425fa291642e32c224631add64d3` (matching digest, no assertion). Agreement creation
`0x2931a02b700bc1c3f7dd5aa8edfe4f21e6705964cc73ad15975e4ec940c6e106`, acceptance
`0x9e3b8eea7352561e04a202b67c3fd5c8a34e2467e13a40fbe7abef003a380d14`, funding
`0xfa24839fdc3bfe4892605e6847ce09a2cae5e5aa3d1a09cc7a62c40c877cc707`, and freeze
`0xa84526a5ec0277f19ee34fbe474ff5c45e025895c3426d42272be5cceea1354d` succeeded. Mutual finalization transactions
`0xaf80861d1ead0aca2818f78bc8c2cc74c48bc92a244dcf17f593507a761cf011` and
`0x70e84262ec7079c78b1e3395e63ab6c5d991401543129449ae5f7afb3f3066af` succeeded. Settlement
`0xb8103c5f7b1cc8e9351f20d2756ae300c738bde4cf49e21cc90f252a9caeaef7` entered recovery; recovery
`0x5d0652ca9ec7605103e5fc3be63cabb0178c4db52d0b2dd356ecbc88d6aac79d` completed the refund. Replay reported
`matches_recorded_settlement:true`, `recovery_applied:true`. Withdrawal
`0x6905926a117cd209cd0afd1b447028b7b8e1c42ad60917db51fb801f817aaace` increased buyer balance by exactly 50,000,000,000,000
atto.

## Incomplete probes and spending record

Earlier one-shot probes left agreements `8` and `9` funded at 50,000,000,000,000 atto each without settlement. Agreement
`8` was interrupted after the harness misparsed a trailing-comma milestone list; agreement `9` was interrupted after the
harness incorrectly assumed the contract-wide milestone sequence reset for each agreement. The corrected agreement `10`
run reads its milestone ID from `get_milestones`. These are incomplete harness runs, not successful lifecycle evidence;
the process-local signers were not persisted, leaving 100,000,000,000 atto unsettled. A separate warranty probe (agreement
`6`) also left 10,000,000,000,000 atto claimable to its ephemeral buyer. Across this turn and prior runs the recorded test
transfer principal totals 9,630,000,000,000,000 atto (0.00963 GEN); transaction fees were not itemized, so this is not an
exact fee-inclusive total. Every individual transfer was no greater than 300,000,000,000,000 atto (0.0003 GEN), below the
authorized 0.001 GEN per-transfer cap.
