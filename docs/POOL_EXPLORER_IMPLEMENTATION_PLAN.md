> [Current mainnet specification, tokenomics and release status](CURRENT_MAINNET.md) — October 26, 2026; prelaunch.

# Native FRG pool, desktop, website and explorer delivery plan

**Updated: 2026-10-24. Status: planned work, not a deployment announcement.** This plan expands [roadmap phases 1 and 2](../ROADMAP.md). No official pool endpoint, production payout service, live pool dashboard or standalone Pool Observer is verified by this review. The online blockchain explorer has recovered source but still needs completion and public deployment verification. No dates or hosting capacity are promised.

For branch context, completed changes, preserved local drafts and next steps by workstream, see the [implementation handoff](HANDOFF_POOL_EXPLORER_2026-10-24.md).

## Existing source and remaining work

| Component | Evidence in this branch | Required completion |
| --- | --- | --- |
| Official native FRG pool | [Offline accounting model](../services/pool_research/README.md) and [feasibility research](ZERO_COST_MINING_POOL_RESEARCH.md) | Build/adapt a native FRG Stratum/RandomX server, durable share/reward ledger and maturity-aware payout service; deploy only after the gates below. The model is not a pool server. |
| Tauri desktop | [Desktop README](../apps/desktop-tauri/README.md), local daemon Solo mode, user-installed XMRig with a user-entered pool and local telemetry | Add verified official-pool configuration and status after deployment, while retaining solo and custom-pool choices. Running XMRig is not proof of accepted shares or payment. |
| Pool website/dashboard | Static GitHub Pages homepage and mining guide; local untracked pool-page drafts are not shipped artifacts | Complete overview, worker dashboard, blocks/shares, payout history, setup and FAQ pages against a separately hosted, secured API. |
| Standalone Pool Observer | No completed tracked Observer application or calculator implementation established here | Build a separately accessible read-only observer with honest data freshness and tested solo/pool probability calculators. It must work without the desktop. |
| Online blockchain explorer | [Flask API, static UI and deployment files](../apps/explorer/README.md); `smoke.py` requires a running node | Complete and test the public service, HTTPS, operations and website integration. Existing source and local smoke scripts do not establish public availability. |

## 1. Build the official native FRG pool

- Select and review an implementation compatible with the exact FRG network identity, address format, eight-decimal amounts, block templates, RandomX seed/version rules and difficulty. Do not assume a Monero/CryptoNight pool works unchanged.
- Implement Stratum jobs, share-target verification, duplicate/replay/stale rejection, candidate block submission and canonical-chain tracking. Persist share weights, rounds, immature rewards, orphan reversals, balances and payout transaction state across crashes.
- Charge the **1% operator fee on eligible pooled mining rewards**. This is a voluntary pool-service deduction, not a consensus diversion of the miner subsidy. Solo mining pays no project-pool operator fee. Separately disclose payout network fees and any XMRig donation policy.
- Before beta, specify the payout scheme (PPLNS/PROP or another reviewed scheme), exact eligible reward/fee basis, integer rounding, dust handling, minimum payout, maturity/confirmation threshold and orphan/reorg rules. The research allocator does not settle these decisions. Reconcile gross eligible rewards = operator fee + miner allocations, with payout costs separately accounted for.
- Implement a real active-worker connection cap and load-test the **100 concurrent worker target**. This is neither 100 unique people nor proven capacity. Test overload rejection and recovery; never advertise available slots from a hardcoded number.
- Separate public Stratum/read-only API services from accounting and payout signing. Keep wallet RPC and unrestricted daemon RPC private, use least privilege, bounded queues, authenticated administration, protected backups, payout limits and auditable recovery. Public monitoring must not need spend keys.

## 2. Integrate solo and pooled mining in Tauri

- Preserve synchronized-local-node solo mining and manual independent-pool configuration. Add an explicitly selected official-pool profile only after its network, TLS endpoint and fee policy are verified; no silent switch or invented endpoint.
- Show the 1% fee, separately disclosed costs, network identity, connection/TLS failures, accepted/rejected shares, hashrate and payout state. Distinguish local process telemetry from pool ledger confirmations and stale API data.
- Test start/stop, switching modes, thread settings, restart, offline node, wrong-network address, invalid TLS certificate, unavailable/full pool and custom-pool selection. Extend isolated Stratum fixtures with real two-miner end-to-end tests through mature FRG payouts before calling the integration complete.
- Wallet keys and recovery phrases remain local. Review endpoint validation, child-process arguments, loopback telemetry authentication and settings persistence. Release signed/checksummed desktop builds only after integration verification.

## 3. Complete pool website and dashboard

- Build overview metrics for network/pool hashrate and difficulty, last blocks, connected workers, tested capacity, effort, fee and payout policy; recent blocks must distinguish immature, confirmed and orphaned status.
- Add worker/share history, unpaid and paid balances, payout transaction references, setup instructions and FAQ. Link to the explorer only when its public URL and network identity have been verified.
- Provide private worker/account access where needed. A public payout address alone is not authorization to view private records or change payout settings. If accounts or threshold changes are offered, require verified wallet control, secure sessions, password hashing where applicable, rate limiting and anti-CSRF protections. Never collect wallet seeds or spend keys.
- Publish a versioned read-only API with source network, timestamps, freshness limits and explicit unavailable/error states. Review HTTPS, CORS allowlists, output escaping, caching, request limits and privacy-preserving logs. GitHub Pages serves static pages; it cannot run Stratum, Flask, wallet RPC or an account database.
- Verify desktop/mobile layouts, keyboard access, empty/stale/error states, incorrect API responses and exact eight-decimal monetary display against the ledger. No sample metric may appear as live network activity.

## 4. Build the standalone Pool Observer

- Deliver a separate read-only web tool, independent of Tauri and pool-account login, for pool/network observations and solo-versus-pooled mining estimates. Distinguish manual illustrative inputs from timestamped measurements; do not imply a working live feed before connection and validation.
- Include expected share/block time, daily expected blocks/rewards, pool contribution and effort/probability distributions. Under constant hashrate H and difficulty D, mean time is D/H and probability of at least one discovery by time t is `1 - exp(-H*t/D)`. A 100% effort does not guarantee discovery.
- Show the 1% pool fee assumption separately from transaction costs; explain pool luck, PPLNS eligibility (if selected), downtime, variable difficulty/rewards and reorgs. Estimates are not balances, actual payouts or guaranteed earnings.
- Test independent numeric reference vectors, zero/negative/nonfinite inputs, very small/large values, units, probability bounds/monotonicity, rounding and stale measurements. Check accessibility and chart labels; keep all signing/account mutation outside the Observer.

## 5. Finish the online blockchain explorer

- Extend the recovered `apps/explorer` service and UI: network overview, paginated recent blocks, height/hash lookup, transaction lookup, confirmations, fees and mempool/confirmed/orphan states. Verify eight-decimal formatting, wide difficulty values and canonical-chain changes against the daemon.
- Add automated fixture-based API/UI tests plus isolated-node integration tests: malformed identifiers, absent blocks/transactions, empty chain responses, RPC timeout/malformed responses, reorg/cache invalidation, pagination, large values and POST/mutation rejection. Existing `smoke.py` alone is not sufficient release evidence.
- Keep a fixed read-only RPC allowlist; do not expose generic daemon or wallet RPC. Review input/output handling, dependency versions, response limits, caching, rate limits and service isolation. The current nginx example is HTTP-only; HTTPS and certificate renewal are remaining deployment work.
- Validate hosting capacity, DNS or verified public routing, firewall/cloud ingress and least-privilege service deployment. Rehearse backup/restore, restart, monitoring, outage messaging and rollback without modifying the existing chain database. Review the existing server-specific deployment script before use.
- Publish the explorer URL and homepage links only after external HTTPS and network-identity checks pass. Describe privacy limits: public chain data cannot reveal arbitrary private recipient balances or prove treasury reserves from a public view key alone.

## Tests, security and rollout gates

All gates below are **pending** unless a linked report records the exact commit, network, environment, results and reviewer. This documentation update does not execute or pass them.

| Stage | Required evidence before advancing |
| --- | --- |
| A — Design and offline build | Final network parameters and pool payout specification; component threat models; deterministic accounting and Observer vectors; explorer API fixtures; build records. |
| B — Isolated integration | Two independent test miners, valid/invalid/stale/replayed shares, accepted native block, maturity and correct payouts to test-controlled wallets; reorg, duplicate-payout prevention, crash/restart and restore tests; desktop/dashboard/explorer consistency. No third-party funds. |
| C — Private hosted staging | Verify actual free-hosting quota and node coexistence; Windows miner and Linux/ARM64 server compatibility; 100-worker load/overload tests; TLS, firewall, RPC isolation, authentication and privacy checks; independent security review with release-blocking findings resolved. |
| D — Controlled beta | After stages A–C and explicit deployment approval, publish verified endpoints and fee/payout terms; cap participation, monitor accepted shares and reconciled payments, exercise alerts and rollback. Deploy explorer/dashboard/Observer only with validated data sources and honest stale/outage behavior. |
| E — Public release and operations | Record independent end-to-end verification, reproducible/signed artifacts where applicable, sustained service evidence and payout reconciliation; publish runbooks, support, backup/restore, incident response and operator handoff/retirement procedures. |

The online explorer is part of phase 1 release readiness. Pool construction and private tests can proceed alongside L1 validation, but whether a public official pool is required on mainnet launch day remains an explicit unresolved release decision. Independent solo mining and pools remain permissionless. No deployment, merge, live endpoint publication or production-funds test is authorized merely by this plan.
