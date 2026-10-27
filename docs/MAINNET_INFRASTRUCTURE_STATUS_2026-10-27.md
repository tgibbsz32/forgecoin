# ForgeCoin infrastructure status and launch gates — 2026-10-27

**Network identity frozen; MAINNET NOT LAUNCHED.** Public mining, live wallet custody, pooled payouts, and native block-1 mining remain disabled. Later verification on October 27 is documented in [Phase 1 native Oracle and Android QA](PHASE1_NATIVE_ORACLE_ANDROID_QA_2026-10-27.md): actual XMRig RandomX share acceptance, wallet RPC, read-only explorer, persistent monitor and QA Android APK passed, but full blocks/payouts did not.

## Frozen native FRG identity

- Chain: original **native ForgeCoin FRG** (Monero-derived RandomX); isolated previous dev network and mined 20261020 candidate are retired and archival only.
- Genesis nonce **20261026**, network UUID `bd936359-09e4-4fdb-8ec0-12fa9d6ef090`, genesis hash `4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c`.
- Address prefixes **190/191/192** (standard/integrated/subaddress); P2P **39480**, local daemon RPC **39481**, local ZMQ **39482**; wallet RPC must stay authenticated and loopback-only.
- 120-second block target, initial difficulty **500,000**, floor **400,000**, LWMA N90 introduced at height **16**.
- Native FRG wallet precision **8 decimals**, primary emission constant **50,000,000 FRG**, planned perpetual **0.20 FRG/block tail**; therefore NOT a strict lifetime supply cap.
- Height 0 genesis includes an **11.92092895 FRG output**, identified by the project as a fork byproduct intended to be unspendable. Its permanent unspendability is **not independently proven**. The owner has requested retaining the chain and disclosing this risk rather than re-freezing genesis; do not claim formally verified zero-premine status or cryptographic burn proof.

Current release manifest: [`config/mainnet.identity.json`](../config/mainnet.identity.json). **`stage=genesis-frozen`; `release_authorized=false`.** Old network data must never be reused as new-mainnet state.

## Oracle host (150.136.209.227): inspected 2026-10-27

- Public `nginx.service` **active**, read-only `forgecoin-explorer.service` **active**, and persistent user-level `forgecoin-monitor.service` **enabled/active**. HTTPS `/pool/api/monitor` exposes verified read-only node status; HTTP 503 on daemon downtime.
- Legacy `forgecoin.service` **inactive**; `forgecoin-mainnet-staging.service` and `forgecoin-mainnet-explorer-staging.service` **inactive**. Never enable/restart as part of a docs or UI change.
- Official pool static preparation is hosted under `/pool/`; HTTP returned **200** at inspection. This **is not** a pool backend or working Stratum port.
- Read-only explorer `/api/overview` returned **503** with a clear new-mainnet-offline error. Treat stats as unavailable; do not display retired-chain metrics as mainnet.
- Frozen 20261026 ARM64 daemon, CLI, wallet RPC and native C pool binaries were compiled and verified on Oracle; isolated offline tests passed real RandomX share acceptance but did not mine blocks. Production daemon, pool Stratum and payouts remain **inactive**.
- Public TLS for `/pool/` was validated from Windows; mainnet P2P/Stratum exposure, authenticated production wallet RPC, wallet backups and operational incident response still require review.

## Pool, dashboard and accounts — staged vs required

The jtgrassie-derived pool source is under `services/official_pool/jtgrassie`. A public static dashboard and a separate Pool Observer exist; neither static site proves that a compatible native pool backend has passed real template, RandomX share, reorg, mature payout and ledger reconciliation tests.

**Planned pool policy:** **1% fee** from eligible pooled rewards. No automatic governance allocation and no fee from solo mining. Validate the fee receiving address against the frozen network before enabling deductions. Never solicit a seed or private key.

**Statistics required before public release:** verified node height/hash and freshness, last network block, difficulty and hash-rate, time-to-block distributions, block propagation and orphan rate, pool hashrate, active miners/workers, shares accepted/rejected/stale, rejection reasons and rates, per-worker hashrates over multiple windows, rounds, pool luck, block maturity, pending/confirmed/orphaned pool rewards, fee deductions, pending/paid payout ledgers, transaction IDs, minimum thresholds, payout schedules, backend health, API freshness, and charts with unavailable/unknown states on outages. No made-up metrics.

**User accounts after security review:** public FRG address identifies a user; a separately authenticated account controls saved worker labels/passwords, payout preferences and account history. Password hashes only (strong password KDF), rotate/revoke worker credentials, session and CSRF protection, ownership proofs/challenges, payout-address change confirmation with mandatory reauthentication and audit trail, explicit address/network validation. Avoid putting private worker or payout metadata in a public page or GET URL. The native pool needs compatible storage, reorg-safe ledger and authorization tests before changes go live. Static GitHub Pages cannot provide this authenticated backend.

## Release-blocking tests

1. Publish a prominent factual disclosure of the inherited 11.92092895 FRG genesis output. Its intended unspendability is **not cryptographically proven**; record the owner's acceptance of this unresolved supply risk before claiming any supply guarantees.
2. Deterministic cross-platform builds and consensus vectors (especially height 16 and LWMA transition); signed and verified release artifacts.
3. Native XMRig real-share acceptance PASSED in isolated offline QA; still test consensus-valid **full blocks**, deep reorgs, matured pool rewards, on-chain payouts, duplicates/retries and crash recovery before public pooled mining.
4. Oracle ARM64 daemon and pool build, P2P bootstrap, local-only RPC, TLS reverse-proxy, firewall and monitoring rehearsals on isolated data.
5. Native wallet create/backup/restore, send/receive, address-family and hardened authenticated wallet RPC validation.
6. Explicit owner authorization, staged launch, peer rollout and operational monitoring. Do NOT enable public services just to make stats available.

## Intended expansions — separate from native consensus

- **Solana SPL / mFRG (not deployed):** new independent proposed **50,000,000 SPL tokens**; **5,000,000 (10%)** reserved for future USDC sale/trading/liquidity, **45,000,000 (90%)** reserved for future distribution. SPL token is **not** a 1:1 wrapped FRG representation. No mainnet mint, sales, bridge, USDC pool or production wallet support exists. Authorized SPL supply policy requires mint-authority management, custody, legal review and transparent distribution.
- **Future native L1:** FCMP++ full-chain membership proofs, curve-tree DB, Generalized Bulletproofs integration, CARROT wallet/address upgrades, mempool transition and load-tested hard-fork compatibility; prefer in-place chain upgrade if feasible.
- **Future interoperability L1/L2/L3:** audited atomic swaps, protected settlement/escrow, Solana bridging if independently proven collateralized, threshold-cryptographic private block routing, payments, and application-layer services. No release date or privacy guarantee across transparent settlement layers.

*These are proposals for future upgrades, not guaranteed features, release dates or audited capabilities.* See [`docs/SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md`](SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md).
