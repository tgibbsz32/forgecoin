# ForgeCoin development roadmap — native-first (October 24, 2026)

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

## Phase 2 — Adoption and mining-pool infrastructure

- **Build and deploy the official native FRG pool:** implement FRG-compatible Stratum/RandomX validation, durable share accounting, reorg/maturity handling and safe native payouts. The **1% operator fee** applies to eligible pooled rewards, separately from payout transaction costs; exact payout rules must be published before beta. The **100-worker target** is not verified capacity.
- **Tauri desktop solo/pooled mining:** retain local solo mining and custom pools; add verified official-pool selection, fee disclosure, accepted-share and payout status after deployment. Existing XMRig launch/telemetry is not an operational official pool. Solo mining has no project-pool fee; independent pools remain permissionless.
- **Pool website/dashboard:** complete overview, worker/share history, blocks, balances/payouts, setup and FAQ pages with a secured backend and timestamped read-only statistics. Any account or payout-setting changes require verified authorization. GitHub Pages alone cannot host the pool or backend.
- **Standalone Pool Observer:** build a separate read-only web tool with pool/network observations, solo-versus-pooled estimates, share effort and probability charts. Test calculator formulas and invalid inputs; label illustrative inputs and stale/unavailable data explicitly.
- **Delivery gates:** offline build and deterministic tests → isolated two-miner mature payouts/reorg/restart tests → private hosted staging and 100-worker load testing → independent security review → controlled beta → monitored public rollout with backup/restore and rollback. Public pool timing relative to mainnet launch remains undecided.

See the [pool, desktop, website, Observer and explorer implementation plan](docs/POOL_EXPLORER_IMPLEMENTATION_PLAN.md) for existing-source evidence, acceptance tests and release gates. All completion/deployment milestones above remain pending.

Governance, native miner bonding and any separately funded community treasury are deferred to the future-development track below. Phase 2 pool infrastructure does **not** authorize a governance treasury, treasury minting, a block-reward allocation or automatic transfer of the operator's 1% fee.

## Future development - FRG governance rules and community treasury (post-launch, not V1)

**Status: design and research only.** No binding elections, FRG bond/staking contracts, multisignature treasury, authorized treasury disbursements, or automatic fee allocation exist today. This work is not a prerequisite for the initial PoW launch. See [provisional governance charter](governance-charter.md) and [native bond feasibility gates](research/governance_bonds/FEASIBILITY_GATES.md). Every binding rule below requires an independently reviewed proposal and explicit owner/community ratification process.

1. **Representative chamber:** develop and publish a balanced **10-seat, one-vote-per-seat native FRG chamber** proposal. Decide precise miner/user/developer/infrastructure constituencies, founder eligibility (if any), qualification criteria, independent representation, election terms, vacancies, recalls and replacement rules. Ten seats are a design target, **not** allocated offices or automatic founder votes.
2. **Miner representation and FRG bonds:** require independently verifiable native PoW contribution (including fair treatment of verified pool miners) **and** an enforceable, owner-controlled native FRG governance bond for miner-representative eligibility. Research the minimum bond, term, observation/qualification period, lock/unbonding enforcement, key-loss and reorg recovery. Wallet holdings or a claimed lock alone must not qualify. Bonds are **not PoS consensus, yield farming, rewards issuance, or a right to additional FRG**.
3. **Voter eligibility and elections:** establish privacy-preserving identity/uniqueness protections, registration and candidate standards, independent verification, election snapshots, secure vote counting, published results, fraud challenges, appeals, anti-Sybil limits and conflict-of-interest recusals. A pool operator, founder or large bondholder must not gain multiple ballots simply by splitting wallets or workers.
4. **Decision and constitutional rules:** draft who may submit proposals and vote, notice/public-review periods, quorum, majority/supermajority thresholds for different proposal types, tie rules, amendment controls, transparent minutes, recall rights, emergency boundaries and independent security reviews. Exact thresholds are **not yet approved**. Chamber recommendations do not by themselves alter the PoW chain: consensus changes still require reviewed releases and independent node-operator adoption.
5. **Separate governance/community treasury:** specify lawful, voluntary and disclosed revenue sources, a clear treasury purpose, operating budgets, expense limits, approval and conflict-of-interest policies, independent accounting and publication of expenditures. Possible sources include donations, explicitly contributed project mining revenue or an **owner-approved, transparently disclosed contribution from actual pool-operator earnings**. The owner's **1% pool operator-fee wallet is not automatically the governance treasury**; no part of that fee is assigned to governance by default. There is **no genesis treasury allocation, premine, block-reward diversion, mandatory transfer tax, staking yield or unrestricted mint authority**.
6. **Treasury custody and execution:** evaluate native-FRG-compatible independent signing controls (a proposed **3-of-5 signer model is illustrative, not ratified**), secure signer/key recovery, spending proposal IDs, documented approvals, multi-party execution, timelocks where actually enforceable, transaction reconciliation, privacy-respecting evidence, emergency key rotation and an independently tested incident response. Do not fund or operate treasury custody until these controls are verified with real native-wallet behavior.
7. **Governance release gates:** complete bond and custody feasibility research, adversarial/duplicate-identity tests, independent reviews, published rulebook, transparent election rehearsal, ratification, and separately authorized activation. Existing practice governance dashboards, Solana-related categories and legacy votes remain **nonbinding experiments**.

**Strict separation:** the **pool reward/hot wallet** pays eligible miners; the **owner-controlled 1% pool fee wallet** receives the operator's earned fees; a **future governance treasury wallet** would spend only separately contributed or approved funds under ratified controls. None of these wallets may be conflated, seeded from a shared mnemonic, or granted each other's signing authority.

## Phase 3 — Native FRG selling and swaps (USDC, ETH, SOL)

- **First: discovery and quotes.** Evaluate real liquidity providers/exchanges supporting *native* FRG, verify quote freshness, network selection, provider terms, fees and availability. No listing, trade or FRG price is currently promised.
- **Peer-to-peer route:** prototype authenticated offer matching and self-custodial settlement; publish fraud/chargeback/counterparty and dispute risks. A listing board is not an atomic swap.
- **Atomic-swap route:** evaluate Monero-derived FRG ↔ Ethereum/EVM approaches, refund paths, lock timing, reorgs and key safety on testnets. ETH and Ethereum-network USDC are candidates only after protocol validation.
- **SOL route:** investigate providers accepting native FRG or a separately validated bridge; Solana DEX access alone cannot settle a native FRG transfer.
- **Wallet Swap interface:** display executable third-party quotes, recipient/network/fees/slippage, explicit approval, timeout/refund and transaction tracking. Never fabricate rates or custody guarantees.
- Require independent security review, legal assessment of any custodial/exchange activity, and actual counterparties/liquidity before production trades.

## Phase 4 — Intended first post-launch expansion: 1:1-backed Solana wFRG

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

## Future L1, L2 and possible L3 applications — additional protocol development

- **Native atomic swaps** with supported assets including Ethereum USDC, and research for **collateralized privacy-shielded synthetic stable-denominated assets** with reserves, peg/redemption mechanics and legal review.
- **TSS/MPC secured private block trading:** threshold-controlled cross-chain vaults, discreet trade intents, independent relayer/execution and atomic delivery-versus-payment where possible, with MEV and custody controls and an eventual disclosed **basis-point routing fee**. Transparent-chain settlement remains observable.
- **L2:** payment channels, batching, privacy-aware liquidity routing, secure exit/dispute paths and data-availability rules.
- **L3:** private-market applications, auctions, merchant payments and selective-disclosure services that need their own contracts/execution protocols.

**All are intended research and future implementations, not existing FCMP++ capabilities, regulatory exemptions or production promises.** For the staged Solana bridge, native hard-fork preference, separate-network fallback, holder-protective wFRG phaseout, security and stressnet specifications see [full future architecture](docs/SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md).

## Phase 5 — Optional privacy applications

Investigate private DeFi execution, sealed-bid auctions, and privacy-preserving governance as standalone research. Solana's public execution does not make those features private automatically: each requires separate cryptographic protocols, threat models, audits and credible user demand. No release dates, mining-linked Solana rewards, guaranteed yield or Token-2022 transfer fees are authorized.

## Design archive and decisions

The proposed October 24 **55M primary reference / 5M genesis treasury** is withdrawn; it must not be used as launch instructions. The official launch remains L1-first and zero-premine.
