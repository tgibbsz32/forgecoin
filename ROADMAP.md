> [Current mainnet specification, tokenomics and release status](docs/CURRENT_MAINNET.md) — October 26, 2026; prelaunch.

# ForgeCoin development roadmap — native-first (October 26, 2026)

**Direction:** The milestones below are ForgeCoin’s committed development direction. They describe future work, not released capabilities.

<small>Proposed future upgrades; implementation and timing are not guaranteed.</small>

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

## Later interoperability — Native FRG selling and swaps (USDC, ETH, SOL)

- **First: discovery and quotes.** Evaluate real liquidity providers/exchanges supporting *native* FRG, verify quote freshness, network selection, provider terms, fees and availability. No listing, trade or FRG price is currently promised.
- **Peer-to-peer route:** prototype authenticated offer matching and self-custodial settlement; publish fraud/chargeback/counterparty and dispute risks. A listing board is not an atomic swap.
- **Atomic-swap route:** evaluate Monero-derived FRG ↔ Ethereum/EVM approaches, refund paths, lock timing, reorgs and key safety on testnets. ETH and Ethereum-network USDC are candidates only after protocol validation.
- **SOL route:** investigate providers accepting native FRG or a separately validated bridge; Solana DEX access alone cannot settle a native FRG transfer.
- **Wallet Swap interface:** display executable third-party quotes, recipient/network/fees/slippage, explicit approval, timeout/refund and transaction tracking. Never fabricate rates or custody guarantees.
- Require independent security review, legal assessment of any custodial/exchange activity, and actual counterparties/liquidity before production trades.

## First post-launch integration — 1:1-backed Solana wFRG

- **First intended post-launch interoperability implementation:** develop, test and (once audited) deploy a Solana SPL/Token-2022 **wrapped FRG (wFRG)** token with **1:1 backing by reserved user-deposited native FRG** and a usable native deposit/mint/burn/redemption bridge. This aims to accelerate wallet/exchange/payment adoption, not create an ICO, additional PoW rewards, a genesis treasury or unbacked circulating supply. Define deposit proof, secure mint/burn, redemption, supply/liability accounting, confirmations, reorg handling, caps and emergency shutdown.
- Design independently controlled custody or cryptographic locking; evaluate real Monero-derived multisig limitations. Use separate monitoring and signing services, bounded queues, idempotent jobs and verified wallet RPC flags.
- Build a durable bridge ledger (e.g. PostgreSQL) for events, registered destinations, approvals, payouts and audits. Payment IDs are not authorization credentials.
- Establish independently verifiable reserve attestations despite native private transfers; a public view key alone does not prove an unspent balance. Keep spend keys isolated and view secrets protected.
- Respect native FRG's **8 decimal places** versus a Solana token's chosen decimals with exact integer arithmetic.
- Investigate SOL/USDC liquidity and optional Solana Actions/Blinks, bridge analytics and miner-opt-in liquidity contributions only **after** the safe core bridge is demonstrated. User deposits collateralize wrapped supply; optional pool liquidity and development revenue are separate budgets.
- Security audit, economic stress testing, operations funding, counterparty demand and explicit deployment approval are mandatory stage gates.

## Future major upgrade — FCMP++/CARROT on existing FRG where feasible

**Preferred network strategy:** adopt FCMP++ and CARROT through an independently audited **in-place hard fork**, preserving the existing native FRG chain, issuance and valid balances. A hard fork does **not** automatically mean a new blockchain. Only if legacy-output compatibility or security makes an in-place upgrade infeasible would a **separate successor network** and explicit, voluntary, supply-conserving bridge/migration be considered. The Solana wFRG wrapper is planned **before** this work, and would only be phased out after users can redeem and reserves/liabilities are reconciled.

- **Curve-tree LMDB/database:** incremental, deterministic global commitment roots and append/rollback indices; sync, pruning, rescan, crash consistency, deep reorganizations and cross-platform performance.
- **Consensus:** verify complete FCMP++ membership/spend proofs and Generalized Bulletproofs components against the correct tree root, with spend authorization, linkability and invalid-proof rejection.
- **CARROT:** integrate the reviewed carrot_core/carrot_impl wallet/address protocols, new outputs, seed recovery, view-only functions and legacy unspent-output compatibility without automatic fund duplication or retroactive privacy promises.
- **Mempool:** handle heavier proof verification, reject invalid entries, revalidate the full pool at the activation hard fork and after reorganizations, rate-limit expensive inputs and vet optimizations such as fe_pow22523.
- **Separate FCMP++ stressnet:** unique genesis and network identifier; heavy transaction loads, large templates, invalid proofs, deep reorganizations and complete sync/resource/failure evidence before agreeing an upgrade height.

## Future L1, L2 and L3 applications — additional protocol development

- **Native atomic swaps** with supported assets including Ethereum USDC, and research for **collateralized privacy-shielded synthetic stable-denominated assets** with reserves, peg/redemption mechanics and legal review.
- **TSS/MPC secured private block trading:** threshold-controlled cross-chain vaults, discreet trade intents, independent relayer/execution and atomic delivery-versus-payment where possible, with MEV and custody controls and an eventual disclosed **basis-point routing fee**. Transparent-chain settlement remains observable.
- **L2:** payment channels, batching, privacy-aware liquidity routing, secure exit/dispute paths and data-availability rules.
- **L3:** private-market applications, auctions, merchant payments and selective-disclosure services that need their own contracts/execution protocols.

**These are planned engineering workstreams and require their own protocols beyond FCMP++/CARROT.** For the staged Solana bridge, native hard-fork preference, separate-network fallback, holder-protective wFRG phaseout, security and stressnet specifications see [full future architecture](docs/SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md).

## Later privacy applications

Investigate private DeFi execution, sealed-bid auctions, and privacy-preserving governance as standalone research. Solana's public execution does not make those features private automatically: each requires separate cryptographic protocols, threat models, audits and credible user demand. No release dates, mining-linked Solana rewards, guaranteed yield or Token-2022 transfer fees are authorized.

## Design archive and decisions

The proposed October 24 **55M primary reference / 5M genesis treasury** is withdrawn; it must not be used as launch instructions. The official launch remains L1-first and zero-premine.

## miniFORGE (mFRG) Solana SPL issuance and custody - October 27, 2026

The intended miniFORGE SPL asset is **distinct from native FRG and future 1:1-backed wFRG**. As of this date, the Solana mainnet mFRG token is **not issued**, no sale/trading offer or liquidity pool exists, and mainnet issuance is blocked by **zero mainnet SOL** in the configured wallet. A *devnet-only* mint exists with 6 decimals and zero supply. Standard SPL Token is intended.

- **50,000,000 mFRG total target**, using separate token holdings: **5M (10%)** eventual sale/trading treasury for possible future USDC/token trading, **5M (10%)** future liquidity reserve once FRG develops observed market value, and **40M (80%)** undistributed pending separately approved mechanism.
- Mainnet token account/mint rent baseline was quoted at approximately **0.00553212 SOL** excluding metadata and transaction expenses. Recommended setup budget: **0.1 mainnet SOL**. This is a funding guideline, not a transaction quote or guarantee. Never send actual SOL to the devnet mint.
- Before activation, review independent treasury signing arrangements, key backup, operational policies, exact mint address, token metadata, mint authority revocation for a genuine 50M cap, raw base-unit supply/account reconciliation, regulatory conditions of any sale, and visible published risk notices.
- The native FRG chain retains independent zero-premine Proof-of-Work economics, eight-decimal values and an unlaunched, genesis-frozen release status. mFRG supply is NOT native FRG mining subsidy or backing for the proposed future wFRG bridge.
- An unreleased Windows desktop development prototype (not merged into the public release) contains Solana wallet creation/import, local encrypted backup/open/recovery controls, mainnet SOL balance query and network-aware mFRG display. Existing tests are not final independent security certification; published release packaging remains blocked by consensus review.

See [miniFORGE treasuries and issuance specification](docs/MINIFORGE_SPL_TREASURIES.md), [future privacy and interoperability architecture](docs/SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md), and [desktop Solana wallet readiness and security](apps/desktop/SOLANA_WALLET_READINESS.md).

## Official pool portal and observer: extended statistics and private worker accounts - October 27, 2026

The proposed public preview includes **57 detailed pool/network/statistics metrics** and **22 additional pool-observer metrics**, with default unavailable status unless an independently verified FRG-native pool stats API reports recent network-correct measurements. Existing probability/earnings calculators remain *illustrative*, not actual account earnings.

The proposed private portal is keyed to a verified **native FRG payout address**, registered worker aliases, and a separately hashed account password. Wallet ownership must be proven with native challenge signatures; knowing an address and worker name does not grant authentication. Account-level 5m/1h/24h hashrate, accepted/rejected/stale shares, worker uptime, per-round reward allocation, immature/unpaid/paid balances, payout confirmation IDs and history are planned. Secure payout **threshold** changes and payout **destination** changes require distinct authorization and independent payout signer controls. No such password interface is live or collecting credentials. Read [pool statistics and account security requirements](docs/POOL_ACCOUNT_STATISTICS_AND_SECURITY.md).
