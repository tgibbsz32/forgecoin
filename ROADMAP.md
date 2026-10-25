# ForgeCoin development roadmap — native-first (October 24, 2026)

> **2026-10-25 navigation:** [Consolidated milestone and acceptance roadmap](docs/wiki/Roadmap.md), [status snapshot](docs/wiki/Current-Status.md), and [software/testing guides](docs/wiki/Home.md). This original roadmap contains detailed planned capabilities; follow dated evidence for what is actually live.

**Status:** Proposed development milestones. Roadmap features are not launched, funded, security-audited or guaranteed.

**Native V1 launch:** Maintain the original Monero-derived FRG network with a **50,000,000 FRG primary-emission reference**, **no allocated genesis premine**, **100% of native block subsidies for Proof-of-Work miners**, and **perpetual 0.20 FRG/block tail emission** (therefore no fixed maximum supply). This restores the policy before the October 24 Solana/genesis-treasury redesign. Historical 55M/5M notes are withdrawn proposals. Existing development-chain and fresh-mainnet candidate are separate; there is no automatic balance migration.

## Phase 1 — Validate and release independent L1 (required before launch)

1. Resolve the existing genesis output: independently prove permanent unspendability or replace it in a fresh candidate and retest. No allocated FRG to founder or treasury.
2. Reconcile the exact miner reward calculation, 50M reference, coinbase maturity and tail subsidy against tested consensus code.
3. Mine and verify native blocks across the LWMA boundary through at least heights 90–92; repeat adversarial timestamp, chain-reorganization and fork-choice tests.
4. Check native consensus equivalence across Windows x64, Linux x86-64 and ARM64, publish reproducible binaries/checksums, and obtain independent review.
5. Validate wallet restore/send/receive, CPU solo mining, XMRig/pool compatibility, node discovery and RPC isolation; rehearse public bootstrap and incident recovery.
6. Complete the online blockchain explorer from `apps/explorer`: block/transaction lookup, pagination, confirmations and reorg-aware data; add API/UI and isolated-node tests, independent security review, HTTPS deployment, monitoring and rollback. Publish the public URL only after external verification. Finish the website, verified downloads and honest network statistics; never label placeholder data as live.

- **Initial Windows desktop release decision:** Solo **and** user-configured Pool mining are both mandatory supported and tested modes for desktop V1. Before desktop distribution, verify actual solo block acceptance/maturity and real FRG-compatible test-pool accepted shares, reward accounting and payout, plus start/stop/reconnect/telemetry behavior. Use disposable wallets and isolated infrastructure; log evidence without secrets. If either mode cannot be demonstrated, **hold the desktop release** rather than describing it as fully tested. An official public pool deployment remains Phase 2 and is **not** a prerequisite for testing against a compatible private pool.

## Phase 2 — Adoption, mining pool and noncustodial treasury

- **Build and deploy the official native FRG pool:** implement FRG-compatible Stratum/RandomX validation, durable share accounting, reorg/maturity handling and safe native payouts. The **1% operator fee** applies to eligible pooled rewards, separately from payout transaction costs; exact payout rules must be published before beta. The **100-worker target** is not verified capacity.
- **Tauri desktop solo/pooled mining:** retain local solo mining and custom pools; add verified official-pool selection, fee disclosure, accepted-share and payout status after deployment. Existing XMRig launch/telemetry is not an operational official pool. Solo mining has no project-pool fee; independent pools remain permissionless.
- **Pool website/dashboard:** complete overview, worker/share history, blocks, balances/payouts, setup and FAQ pages with a secured backend and timestamped read-only statistics. Any account or payout-setting changes require verified authorization. GitHub Pages alone cannot host the pool or backend.
- **Standalone Pool Observer:** build a separate read-only web tool with pool/network observations, solo-versus-pooled estimates, share effort and probability charts. Test calculator formulas and invalid inputs; label illustrative inputs and stale/unavailable data explicitly.
- **Delivery gates:** offline build and deterministic tests → isolated two-miner mature payouts/reorg/restart tests → private hosted staging and 100-worker load testing → independent security review → controlled beta → monitored public rollout with backup/restore and rollback. Public pool timing relative to mainnet launch remains undecided.

See the [pool, desktop, website, Observer and explorer implementation plan](docs/POOL_EXPLORER_IMPLEMENTATION_PLAN.md) for existing-source evidence, acceptance tests and release gates. All completion/deployment milestones above remain pending.

- Fund an optional development treasury from **voluntary donations, foundation-owned mining, an explicitly disclosed portion of real pool fees, and future revenue**, not from genesis issuance or miner-reward diversion.
- Publish custody, expenditure and reserve reporting; establish tested independent signer procedures before funds become material.
- Explore native FRG mining-participation governance bonds only after independent enforceability/security review; no votes or locks currently authorize consensus changes.

## Phase 3 — Native FRG selling and swaps (USDC, ETH, SOL)

- **First: discovery and quotes.** Evaluate real liquidity providers/exchanges supporting *native* FRG, verify quote freshness, network selection, provider terms, fees and availability. No listing, trade or FRG price is currently promised.
- **Peer-to-peer route:** prototype authenticated offer matching and self-custodial settlement; publish fraud/chargeback/counterparty and dispute risks. A listing board is not an atomic swap.
- **Atomic-swap route:** evaluate Monero-derived FRG ↔ Ethereum/EVM approaches, refund paths, lock timing, reorgs and key safety on testnets. ETH and Ethereum-network USDC are candidates only after protocol validation.
- **SOL route:** investigate providers accepting native FRG or a separately validated bridge; Solana DEX access alone cannot settle a native FRG transfer.
- **Wallet Swap interface:** display executable third-party quotes, recipient/network/fees/slippage, explicit approval, timeout/refund and transaction tracking. Never fabricate rates or custody guarantees.
- Require independent security review, legal assessment of any custodial/exchange activity, and actual counterparties/liquidity before production trades.

## Phase 4 — Optional Solana interoperability (not required for native launch)

- Prototype a standard SPL or Token-2022 **wrapped FRG** representation on devnet, backed **1:1 by user-deposited native FRG**, not new FRG issuance or a genesis treasury. Define deposit proof, secure mint/burn, redemption, supply/liability accounting, confirmations, reorg handling, caps and emergency shutdown.
- Design independently controlled custody or cryptographic locking; evaluate real Monero-derived multisig limitations. Use separate monitoring and signing services, bounded queues, idempotent jobs and verified wallet RPC flags.
- Build a durable bridge ledger (e.g. PostgreSQL) for events, registered destinations, approvals, payouts and audits. Payment IDs are not authorization credentials.
- Establish independently verifiable reserve attestations despite native private transfers; a public view key alone does not prove an unspent balance. Keep spend keys isolated and view secrets protected.
- Respect native FRG's **8 decimal places** versus a Solana token's chosen decimals with exact integer arithmetic.
- Investigate SOL/USDC liquidity and optional Solana Actions/Blinks, bridge analytics and miner-opt-in liquidity contributions only **after** the safe core bridge is demonstrated. User deposits collateralize wrapped supply; optional pool liquidity and development revenue are separate budgets.
- Security audit, economic stress testing, operations funding, counterparty demand and explicit deployment approval are mandatory stage gates.

## Phase 5 — Optional privacy applications

Investigate private DeFi execution, sealed-bid auctions, and privacy-preserving governance as standalone research. Solana's public execution does not make those features private automatically: each requires separate cryptographic protocols, threat models, audits and credible user demand. No release dates, mining-linked Solana rewards, guaranteed yield or Token-2022 transfer fees are authorized.

## Design archive and decisions

The proposed October 24 **55M primary reference / 5M genesis treasury** is withdrawn; it must not be used as launch instructions. The official launch remains L1-first and zero-premine.
