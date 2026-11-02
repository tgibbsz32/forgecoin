# ForgeCoin development roadmap

**Updated November 1, 2026. Order: native FRG → governance procedures → optional mFRG → future ecosystem and privacy upgrades.** Proposed features and dates are not guaranteed. Native mainnet release and mFRG distribution remain unauthorized until required gates are met.

## Phase 1 — Verify native FRG mainnet and mining
- Resolve genesis-output unspendability, frozen consensus identity, RandomX/LWMA90 verification and cross-platform reproducible builds. Use P2P 39480, RPC 39481, ZMQ 39482.
- Test Windows/Android wallet-miner, accepted native solo and pool shares/blocks, payouts, chain maturity, explorer and Oracle monitoring.
- Native FRG: 50M primary-emission reference (not a hard cap), 0.20 FRG perpetual block tail; mining rewards accrue to miners. Official pool fee: planned 1% on eligible pooled rewards.
- Gate: independently reviewed, repeatable release and end-to-end mining evidence before public launch.

## Phase 2 — Determine and publish governance procedures before mFRG
- Seek FRG miner, contributor and community input; determine who may submit proposals, eligibility, discussion periods, vote/consent/decision rules, appeals and amendment procedures.
- Set founder responsibilities, treasury authorization and signer thresholds, conflict disclosures, security controls, records retention and emergency procedures.
- Publish the final, approved governance framework and its effective date. No fixed chamber, mandatory stake or binding ballot structure is currently ratified.
- **Gate: governance procedures must be determined and published before mFRG is introduced, promoted, minted, sold, distributed or given treasury authority.**

## Phase 3 — Optional separate miniFORGE (mFRG)
- Only after Phase 2, consider the current **50,000,000 six-decimal standard Solana SPL mFRG** proposal: 5M initial presale, 5M future liquidity, 40M combined ecosystem/staking/collateral reserve.
- Proposed flat presale price is $0.12/mFRG; maximum $600,000 gross if all 5M sell. Proposed proceeds 90% project / 10% founder, half founder share immediate and half over six months. No separate founder token allocation under the current proposal.
- Require independent legal, custody, payment-verification, supply/account reconciliation and security review before any authorization. The earlier 500M allocations, five-round price ladder and 80/20 proceeds split are superseded.
- No sale, mint, bridge, staking, backing, price guarantee or token rights are active.

## Phase 4 — Governed treasuries and ecosystem
- Evaluate optional liquidity, staking, collateral, community grants and game integration under approved governance and independently audited custody, signing and release controls.

## Phase 5 — Native FCMP++ / CARROT privacy research
- Research full-chain membership proofs, curve-tree databases, generalized Bulletproofs, CARROT addressing, wallet/mempool/consensus validation and deep-reorg performance.
- Prefer a reviewed supply-conserving in-place hard fork if safe; independent cryptographic audit and explicit activation approval are required.

## Phase 6 — Other L1, L2 and potential L3 services
- Native atomic swaps, MPC/TSS settlement, L2 secure payments and L3 merchant, marketplace and selective-disclosure systems remain separate review-gated proposals.

## Public statistics and accountability
- Provide read-only pool statistics by public FRG payout address **without accounts or logins**. Personal payout changes require secure independent wallet-control authorization.
- Display only verified native-chain hashrates, pool/solo miner and worker counts, and opt-in leaderboard records. Unsupported figures remain Unavailable.
- Homepage visitor and pageview counters are third-party estimates, not blockchain data.

[Current mainnet release gates](docs/CURRENT_MAINNET.md) · [Governance charter](governance-charter.md) · [Pool overview](docs/pool.html) · [mFRG status](docs/miniforge-sale.html) · [Privacy roadmap](docs/SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md)
