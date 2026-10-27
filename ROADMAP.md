> [Current mainnet specification, tokenomics and release status](docs/CURRENT_MAINNET.md) — October 26, 2026; prelaunch.

# ForgeCoin development roadmap — native-first (October 26, 2026)

**Direction:** The milestones below are ForgeCoin’s committed development direction. They describe future work, not released capabilities.

<small>Proposed future upgrades; implementation and timing are not guaranteed.</small>

**Native V1 launch:** Maintain the original Monero-derived FRG network with a **50,000,000 FRG primary-emission reference**, **no allocated genesis premine**, **100% of native block subsidies for Proof-of-Work miners**, and **perpetual 0.20 FRG/block tail emission** (therefore no fixed maximum supply). This restores the policy before the October 24 Solana/genesis-treasury redesign. Historical 55M/5M notes are withdrawn proposals. Existing development-chain and fresh-mainnet candidate are separate; there is no automatic balance migration.

## Planned miniFORGE (mFRG) value-accrual and native FRG staking relationship (not live)

miniFORGE (mFRG) is intended to become the principal **ecosystem value-accrual asset associated with native ForgeCoin (FRG)**. This is a project design objective, **not** a claim that mFRG presently holds the market value of FRG, is collateralized by FRG, has a guaranteed exchange rate, or provides legal ownership of FRG reserves.

**Proposed sequence:** (1) independently validate and launch native FRG proof-of-work mining; (2) separately launch an mFRG SPL presale, subject to legal review, mint verification and operational readiness; (3) observe organic FRG mining participation, liquidity, price discovery and market stability over a meaningful but currently undefined period; (4) only after this evidence exists, design and independently review a mechanism enabling holders to **stake or lock native FRG in connection with mFRG**. The timing, economics and feasibility of this mechanism remain to be determined.

A staking mechanism does **not** automatically transfer FRG value to mFRG: the specification must state whether FRG is deposited into transparent custody, locked by a verifiable protocol, used to back issued mFRG units, earns rewards, supports redemption, or serves another explicit purpose. Any conversion, ratio, backing representation, yield or redemption entitlement would require separate public rules, reserves and security validation; **none is promised or presently active**. Staking must not silently alter native FRG proof-of-work issuance or confuse mFRG with the separately proposed 1:1 native-FRG-backed **wFRG** wrapper.

**Pre-implementation gates:** obtain a market-observation methodology and published activation criteria; define custody and key management, accounting, contract roles, user withdrawal/redemption rules, risks, insolvency handling, independent testing and audits; assess securities, custody, money-transmission and tax treatment before accepting deposits. Solana transactions remain publicly observable despite native FRG's privacy properties.

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

## Future interoperability — mFRG with proposed FRG staking and 1:1 backing

- **Revised implementation direction:** mFRG is the Solana asset; do not issue a separate wFRG token. Following a reviewed mFRG presale and observed native FRG mining/price discovery, design a secure FRG stake/lock facility and reserve accounting targeting eventual 1:1 native-FRG backing of mFRG. Presale supply must be reconciled before making any collateral or redemption claims.
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

The intended miniFORGE SPL asset is **distinct from native FRG** and is the sole proposed Solana asset for a later FRG-linked staking/backing protocol. As of this date, the Solana mainnet mFRG token is **not issued**, no sale/trading offer or liquidity pool exists, and mainnet issuance is blocked by **zero mainnet SOL** in the configured wallet. A *devnet-only* mint exists with 6 decimals and zero supply. Standard SPL Token is intended.

- **50,000,000 mFRG total target**, using separate token holdings: **5M (10%)** eventual sale/trading treasury for possible future USDC/token trading, **5M (10%)** future liquidity reserve once FRG develops observed market value, and **40M (80%)** undistributed pending separately approved mechanism.
- Mainnet token account/mint rent baseline was quoted at approximately **0.00553212 SOL** excluding metadata and transaction expenses. Recommended setup budget: **0.1 mainnet SOL**. This is a funding guideline, not a transaction quote or guarantee. Never send actual SOL to the devnet mint.
- Before activation, review independent treasury signing arrangements, key backup, operational policies, exact mint address, token metadata, mint authority revocation for a genuine 50M cap, raw base-unit supply/account reconciliation, regulatory conditions of any sale, and visible published risk notices.
- The native FRG chain retains independent zero-premine Proof-of-Work economics, eight-decimal values and an unlaunched, genesis-frozen release status. mFRG supply is NOT a native FRG mining subsidy; no existing mFRG supply represents deposited FRG unless independently reconciled under the future reserve protocol.
- An unreleased Windows desktop development prototype (not merged into the public release) contains Solana wallet creation/import, local encrypted backup/open/recovery controls, mainnet SOL balance query and network-aware mFRG display. Existing tests are not final independent security certification; published release packaging remains blocked by consensus review.

See [miniFORGE treasuries and issuance specification](docs/MINIFORGE_SPL_TREASURIES.md), [future privacy and interoperability architecture](docs/SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md), and [desktop Solana wallet readiness and security](apps/desktop/SOLANA_WALLET_READINESS.md).

## Official pool portal and observer: extended statistics and private worker accounts - October 27, 2026

The proposed public preview includes **57 detailed pool/network/statistics metrics** and **22 additional pool-observer metrics**, with default unavailable status unless an independently verified FRG-native pool stats API reports recent network-correct measurements. Existing probability/earnings calculators remain *illustrative*, not actual account earnings.

The proposed private portal is keyed to a verified **native FRG payout address**, registered worker aliases, and a separately hashed account password. Wallet ownership must be proven with native challenge signatures; knowing an address and worker name does not grant authentication. Account-level 5m/1h/24h hashrate, accepted/rejected/stale shares, worker uptime, per-round reward allocation, immature/unpaid/paid balances, payout confirmation IDs and history are planned. Secure payout **threshold** changes and payout **destination** changes require distinct authorization and independent payout signer controls. No such password interface is live or collecting credentials. Read [pool statistics and account security requirements](docs/POOL_ACCOUNT_STATISTICS_AND_SECURITY.md).


**Revised mFRG-first policy (October 27, 2026):** No separate wFRG token is currently planned. miniFORGE (mFRG), a distinct Solana SPL asset, is intended to serve as the ecosystem's FRG-linked asset. Following the mFRG presale and a period of native FRG public mining and observed price discovery, a separately audited protocol may allow FRG holders to lock or stake native FRG for mFRG-related rights. The **target is an eventual 1:1 FRG-backed relationship**, but this is a future design goal, not an existing 1 FRG = 1 mFRG redeemability promise. Because mFRG presale tokens may circulate before FRG collateral exists, the project must define how unbacked presale supply, reserves, new issuance, redemption rights and total circulating supply will be reconciled before calling mFRG fully backed. No bridge, staking, 1:1 reserve, conversion or redemption is live; native FRG mining rules are unchanged.

## Proposed future development commitment — mFRG staking and protocol collateral (October 27, 2026)

**Committed roadmap direction; proposed implementations, not deployed features or guaranteed outcomes.** ForgeCoin intends for miniFORGE (mFRG), a separate Solana SPL asset, to become the ecosystem's staking and protocol-collateral asset linked to native mined FRG. This supersedes the proposal to launch a separate wFRG token. The following development workstreams are planned, subject to security, feasibility, governance and legal review:

1. **FRG staking with mFRG rewards:** after the native chain and mFRG presale have launched and FRG has undergone a meaningful period of mining and independent price discovery, design a voluntary, verifiable FRG lock/stake facility and distribute bounded mFRG allocations under published eligibility, accounting, and withdrawal rules. Staking does not alter native RandomX proof of work.
2. **mFRG collateral for cross-chain settlement:** evaluate mFRG security bonds for bridge operators and independently verified cross-chain swap/settlement roles, with enforceable penalties for objectively provable misconduct, transparent reserve requirements, and an explicit failure-recovery process.
3. **mFRG collateral for future L2/L3:** research use of mFRG in optional settlement-operator bonds and higher-layer financial protocols where collateral serves a real security function; do not require mFRG for ordinary L1 transfers, mining, or base privacy.
4. **Protocol governance:** evaluate clearly limited mFRG governance participation for the services backed by mFRG, without overriding native FRG consensus or miner/security governance.
5. **FRG reserve relationship:** investigate whether mFRG can develop a verifiable reserve connection to native FRG. **There is no current 1:1 FRG redemption promise, guaranteed peg, collateral coverage, staking yield, or right to a reserve.** The circulating presale supply and FRG reserve needs must be reconciled before any backing claim.

Fundamental **FCMP++/CARROT privacy upgrades must remain available without mFRG ownership**. Native FRG should continue operating if Solana, mFRG, or any future cross-chain mechanism is unavailable. Exact schedules, amounts, staking rewards, custody, slashing, contracts, audits and economics remain future specifications; none is operational or guaranteed.


## Fixed mFRG supply, staged presale and risk disclosures (October 27, 2026)

**Approved planning specification, not a live offer:** 50,000,000 miniFORGE (mFRG) standard SPL tokens (6 decimals), provisionally apportioned to a 5,000,000 mFRG presale vault (10%), 5,000,000 mFRG liquidity reserve (10%) and 40,000,000 mFRG future staking, collateral and distribution reserve (80%). No separate wFRG mint is planned. Mint authority, custody, vesting and whether mint authority can be revoked require publication and independent review before issuance.

**Presale proposal:** five inventory rounds of exactly 1,000,000 mFRG each, at $0.01, $0.02, $0.03, $0.04 and $0.05 USD per token, respectively, totaling **up to $150,000 USD gross only if every round sells out**. Accept **native Solana USDC** (mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`) and native SOL through independently verified, expiring USD-based quotes. **Ethereum and ETH payments are excluded from this presale.** No purchase endpoint, token delivery or presale contract is operational today.

**Anticipated use of proceeds, subject to actual costs and legal review:** 50% DEX liquidity, 20% network development, 10% infrastructure/security/audits and 20% founder compensation. The founder allocation is proposed to release 50% after defined sale settlement and the remainder in six equal monthly installments. These are intended budget percentages, not commitments to particular liquidity levels, deliverables, or investment outcomes; final terms must explain any administrative flexibility without misleading purchasers. Report actual USD fair values and spending. A qualified finality policy for properly completed sales may be considered, but **statutory refund, rescission and fraud remedies cannot be excluded by a no-refunds disclaimer**.

mFRG has no assured resale market, price appreciation, revenue share, 1:1 FRG redemption, or guaranteed staking reward. Future FRG staking and collateral integration remain proposed, depend on new reviewed protocols, and are not a buyer entitlement. These statements do not determine securities, money-transmission, consumer-protection or tax status; obtain qualified legal review, jurisdictional eligibility rules, disclosures and applicable registrations or exemptions **before inviting funds**. No marketing or disclaimer should imply legal immunity.
