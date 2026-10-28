> **Current mFRG policy (October 28, 2026): Historical archive only.** The previous 50M mFRG three-bucket notice below is superseded by a **500M proposed fixed-supply target, 50M fundraising and 30M founder-beneficial holdings (6%)**. See [canonical current policy](MFRG_LIFETIME_TOKENOMICS_500M.md). Native FRG mining economics remain independent.

> **October 27, 2026 superseding notice:** This is historical research/evidence. The current direction has **no approved fixed ten-seat governance system** and **no planned wFRG bridge**. The separately proposed 50M mFRG SPL token has **5M initial sale**, **5M post-sale liquidity/staking treasury**, and **40M future issuance/development treasury**. Governance is to be selected before the sale concludes. The current active specifications are [ROADMAP.md](../ROADMAP.md) and [miniFORGE allocation](MINIFORGE_SPL_TREASURIES.md). Do not treat earlier planning decisions here as active authorization.

> [Current mainnet specification, tokenomics and release status](CURRENT_MAINNET.md) — October 26, 2026; prelaunch.

# Zero-cost ForgeCoin mining-pool feasibility research

**Research status:** 2026-10-24. **Pre-launch investigation only. No pool has been deployed, funded, audited or shown to produce correct native FRG payouts.** A zero-dollar hosting bill is a constraint, not a guarantee of unrestricted or durable service. Hardware, electricity, existing cloud quota and operational time still have value.

## Goal

Allow multiple independent Windows miners to submit RandomX shares to a ForgeCoin (FRG) pool with auditable proportional payouts, while keeping required monthly hosting charges at $0. The launch is *native FRG only*. No wrapped FRG, bridge or proof-of-stake features are part of pool mining. Pool rewards must originate exclusively from native PoW blocks and network transaction fees under actual consensus. Pool software must never generate additional FRG.

## Hosting comparison — verify actual account quota before configuration

| Candidate | Nominal recurring cloud charge | Practical assessment |
| --- | --- | --- |
| Existing Oracle Cloud Always Free Ampere A1 | $0 only within remaining quota and eligible services | **First-choice feasibility test**, using existing machine where possible. Do not assume unused cores/RAM because explorer, node and other services may occupy them. |
| User-owned Windows/Linux desktop | No new cloud charge | Good private two-miner test and fallback. Public use depends on dynamic IP, port forwarding, availability, upstream restrictions and home electricity. |
| Oracle E2.1.Micro free VM | $0 within eligible quotas | Potential lightweight Stratum/API frontend; modest RAM means avoid colocating a RandomX validator/full daemon without performance proof. |
| Other perpetual-free provider | Potentially $0 | Evaluate only after confirming durable compute, public inbound TCP, egress, storage and non-crypto-mining policy; promotions and trial credits do not count. |
| Temporary trial/free credit | $0 only during trial | **Not eligible** as the permanent zero-cost plan. |

**Important 2026 quota correction:** Oracle's current documented Always Free A1 limit for new/current eligible allocations is **1,500 OCPU-hours and 9,000 GB-hours per month**, approximately **2 OCPU / 12 GB for a full month** in aggregate, and up to two E2.1.Micro instances. Older 4 OCPU/24 GB reports should not be used to plan new instances. Verify tenancy-specific limits, grandfathering and resource consumption before changing an existing VM. Oracle advertises 10 TB/month outbound transfer, subject to service conditions. Running a pool on the *existing* Oracle VM avoids consuming another VM allocation but increases memory, CPU, storage and outage coupling. Always Free capacity can be unavailable or reclaimed subject to provider conditions.

Official Oracle sources:
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- https://www.oracle.com/cloud/free/
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm

## Candidate pool implementations

### A. Standard Stratum pool (preferred **first proof of concept**, not a vetted production choice)

Architecture: external miners -> TLS-capable Stratum endpoint -> FRG-aware share target/template validator -> localhost-only ForgeCoin daemon RPC -> validated main chain; independently auditable ledger tracks submitted shares, orphaned blocks, maturity and payouts; payout service uses isolated native wallet RPC with strict limits.

Required demonstrations:
1. Correct block templates, RandomX seed/height/version behavior and full wallet/address decoding for **the exact fresh candidate network**.
2. Two distinct external Windows miners each submit valid low-difficulty shares and at least one native candidate block is accepted by the standalone daemon.
3. Accurate miner difficulty/share accounting, stale/duplicate/replay invalidation, no fake accepted shares and clear worker identity controls.
4. Share-based payout calculation with documented PPLNS/PPS/PROP decision, maturity delay, round/truncation, dust thresholds, fees, and handling of orphaned and reorged blocks.
5. Pool wallet segregation, encrypted backup and key recovery, payout limits, rate limits, private wallet RPC, audit logs and transparent fee policy. Prefer no custody if technically viable.
6. Arm64 build/runtime, systemd restart persistence and firewall policy verified while existing node and explorer remain healthy.

**Software caution:** Historical CryptoNote Node.js pools such as zone117x/cryptonote-nodejs-pool and dvandal variants were developed for CryptoNight families, not a verified ForgeCoin RandomX network; upstream zone117x explicitly states it is not maintained. Do not deploy them without a compatibility/security review and code adaptation. An FRG-specific implementation or actively maintained RandomX-aware fork may be required.

References:
- https://github.com/zone117x/node-cryptonote-pool
- https://github.com/dvandal/cryptonote-nodejs-pool
- https://xmrig.com/docs/miner/config/pool

### B. P2Pool (preferred **long-term decentralization design**, feasibility unknown for FRG)

P2Pool distributes coinbase outputs based on share-chain accounting rather than entrusting all FRG block rewards to an operator-controlled payout wallet. In Monero this supports noncustodial, zero-fee decentralized mining. However the published P2Pool is **for Monero**, not a drop-in ForgeCoin binary. A proper FRG fork requires new sidechain identity and genesis, correct native consensus/network IDs, mining/job format, payout output construction, address prefixes, share difficulty, pool block validity and cross-node interoperation. Sidechain rules and RandomX use must be independently tested; no promise of immediate compatibility or zero development cost.

References:
- https://github.com/SChernykh/p2pool
- https://www.getmonero.org/get-started/mining/
- https://docs.getmonero.org/interacting/mining/guides/p2pool/xmrig-p2pool/

### C. Daemon solo-mining service (baseline only)

Two PCs can mine individually through their own daemon or XMRig daemon-mode interface; this **does not** pool proportional shares or smooth payout variance. Use it to verify block templates and miner compatibility, not advertise it as a pool.

## Proposed no-charge deployment topology

Stage 0 (**offline**): On Windows, run isolated fresh-candidate `forged` and two miners against a loopback-only prototype Stratum endpoint and test addresses. Compare valid share counts to RandomX reference, deliberately submit stale/invalid shares, induce restart and synthetic fork, verify accounting against independent calculations. Do not use production keys or mix candidate and current development-chain addresses.

Stage 1 (**private Oracle ARM64 proof**): Inspect free quota and existing VM capacity first. If adequate, host a pool gateway as a separate unprivileged systemd service beside the existing daemon, communicating via `127.0.0.1` only. Use a distinct candidate daemon/data directory **only if resources permit**, never overwrite the development daemon or its LMDB. Keep ingress limited to test miner IPs; keep unrestricted daemon RPC and wallet RPC off the internet.

Stage 2 (**controlled public beta, only after independent review**): Publish one dedicated Stratum port with TLS, per-IP connection/share limits, DDoS protection within free allowances, health checks and uptime disclosures. Expose minimal public pool statistics but no keys, internal RPC or wallet addresses that compromise privacy. No paid load balancer, premium database, managed K8s, domain purchase or trial-credit dependency. Existing GitHub Pages may present documentation/statistics; it cannot accept Stratum TCP mining shares.

Stage 3 (**payout verification**): Test a mined coinbase through maturity and real low-value native wallet payout to **test-controlled addresses** on isolated chain. Require receipts, mining-share ledger reconciliation, failed-payout recovery, fee disclosure and fork reversal testing before public third-party funds are involved.

**Operational caveat:** Centralizing a pool and full node on one $0 VM creates a single point of failure and potentially concentrates early FRG hash power. Encourage continued solo mining and multiple independent pool operators. Plan for quota exhaustion and inability to guarantee SLA.

## Owner-approved initial pool design (2026-10-24)

- Offer both **solo mining and pool mining** in the desktop application. Solo mining remains permissionless and does not incur the project-pool operator fee.
- **Initial project-operated pool operator fee: 1% of eligible pooled mining rewards**. Distinguish it from network payout transaction fees and publish accounting before connecting external miners.
- **100 concurrent miner/worker connections** is the *planned advertised maximum*, not verified throughput. Connections represent worker sessions, not necessarily 100 unique people. Enforce a tested active-session cap in the pool gateway before launch; no claim of 100 supported miners may be made until a load test proves it.
- Initial project pool is expected to be the first advertised ForgeCoin pool, **not an exclusive consensus-authorized pool**. Other operators are free to create independent pools; users may select one, and existing solo miners remain supported.
- Display an explicit in-app explanatory caption. No specific pool endpoint is currently verified or hardcoded. Until deployment, the pool option remains user-configured and must not pretend the project pool is live.
- Future operator handoff or project-pool retirement requires advance notice and complete matured payout accounting; the blockchain does not depend on the operator remaining online.

## Open operational decisions

1. **Pool architecture**: prioritize conventional Stratum with transparent payouts first, P2Pool-only noncustodial design first, or prototype both?
2. **Fee implementation**: the 1% operator fee is approved; determine precise fee deduction rules, accounting and miner-facing reporting. Payout transaction fees/costs are separate.
3. **Payout policy**: PPLNS vs proportional rounds, maturity/confirmation threshold, minimum payout, orphan and fee treatment. Nothing is ratified.
4. **Infrastructure isolation**: use existing Oracle VM if capacity allows, or reserve a standalone free VM/desktop with separated failure domain?
5. **Release coupling**: make an independently tested public pool a mainnet launch requirement, or start with solo mining and open public pool afterward?

## Required exit criteria

A pool is **not launch-ready** until the exact final FRG network parameters are frozen; share validation, miner accounting, chain reorgs and payouts pass under native consensus on Windows and ARM64; wallet custody and network perimeter receive security review; a basic operational budget confirms $0 within actual OCI quota; and two independent miners can mine and receive correct native FRG. Do not set up a public pool on the existing Oracle deployment before these checks or before genesis and final mainnet policy are approved.

## Implementation and rollout tracking

The [native pool and explorer implementation plan](POOL_EXPLORER_IMPLEMENTATION_PLAN.md) expands this feasibility study into pool construction, Tauri solo/pooled integration, pool website/dashboard, standalone Pool Observer and online explorer completion. The offline accounting model is not a deployed pool. Required gates are offline tests, isolated mature payouts and reorg/recovery tests, private hosted staging with capacity/security review, then controlled beta and public operations. Payout verification must precede beta participation involving third-party funds; the earlier numbered topology sections are not permission to defer it until after public beta.
