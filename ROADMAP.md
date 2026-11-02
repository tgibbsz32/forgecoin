# ForgeCoin development roadmap

**Updated November 1, 2026. Order: native FRG → governance procedures → optional mFRG → future ecosystem and privacy upgrades.** Proposed features and dates are not guaranteed. Native mainnet release and mFRG distribution remain unauthorized until required gates are met.

## Phase 1 — Verify native FRG mainnet and mining
- Resolve genesis-output unspendability, frozen consensus identity, RandomX/LWMA90 verification and cross-platform reproducible builds. Use P2P 39480, RPC 39481, ZMQ 39482.
- Test Windows/Android wallet-miner, accepted native solo and pool shares/blocks, payouts, chain maturity, explorer and Oracle monitoring.
- Native FRG: 50M primary-emission reference (not a hard cap), 0.20 FRG perpetual block tail; mining rewards accrue to miners. Official pool fee: planned 1% on eligible pooled rewards.
- **Prelaunch 51% resilience (non-consensus):** diversify independent miners/pools/peers, compare independent chain observers, alert on reorgs and difficulty anomalies, preserve the existing deep-reorg pool payout quarantine and test full 61+ block reconciliation. Tari-compatible FRG-parent merge mining remains isolated feasibility research; FRG-as-Monero-auxiliary is a separately audited future hard-fork proposal. [Security decision and sources](docs/SECURITY_51_PERCENT_AND_TARI_MERGE_MINING_2026-11-02.md) · [Implementation issue](https://github.com/tgibbsz32/forgecoin/issues/194).
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
- **Intended utility:** 1 FRG : 1 eligible mFRG reserve-backed bridge/redemption; faster Solana ecosystem transfers; supported DEX swaps/liquidity; optional finite-reserve staking; and mFRG payments for USD-priced CITY packs in ForgeCoin's Discover Your City game. These capabilities are development objectives, not live entitlements.
- **Backing gate:** independently verify one available native FRG for each mFRG advertised as 1:1 redeemable, including presale/DEX/staking inventory where applicable; reconcile liabilities, prevent double counting, design audited custody/lock-and-release mechanics, support FRG's 8 decimals versus SPL's 6, and cap bridge capacity below both the 50M mFRG ceiling and proven FRG reserves. Native FRG tail issuance continues indefinitely and is not entirely bridgeable by assumption.
- No sale, mint, bridge, redemption, staking, backing, DEX liquidity, game checkout, market-price guarantee or token rights are active.

## Phase 4 — Governed treasuries and ecosystem
- Implement reviewed Solana wallet interoperability and audited FRG ↔ mFRG reserve-backed transfers with custody, finality, reorg, escrow, redemption and independent proof-of-reserves reporting. A 1:1 unit ratio is not a DEX market-price peg.
- Add separately provisioned Solana DEX liquidity, optional staking funded from the finite combined reserve, collateral and grants under approved governance.
- Integrate optional mFRG checkout in ForgeCoin's Discover Your City game: USD-priced CITY packs, finalized-payment verification, exactly-once CITY credit and 100% of received mFRG to the designated ecosystem treasury. Never trust screenshots or client-side payment claims.

## Proposed future merged mining — unapproved R&D, not native launch scope

Two **distinct** possible mining integrations are research proposals only. The native FRG launch remains independent RandomX PoW, with its frozen consensus rules and 120-second target. No Tari/XMR earnings, merged-mining pool, miner toggle, chain security benefit, activation height or launch date is promised.

1. **FRG parent / Tari auxiliary (FRG + Tari):** investigate modifying a *patched* Tari RandomXM proxy to place Tari's auxiliary commitment into an FRG block's coinbase and mine both from one RandomX job. FRG's Monero-derived RPC/template and coinbase formats make a disposable-chain compatibility study reasonable, but Tari accepts the parent hashing blob/RandomX seed only if its actual proof and seed validation permit it. Changes to Tari, upstream approval, FRG pool accounting and miner job routing may be required. This **does not import Monero or Tari hashrate into FRG**; it could create an additional miner incentive if supported and economically worthwhile.
2. **Monero parent / FRG auxiliary (XMR + FRG):** investigate a properly audited FRG AuxPoW consensus extension so participating Monero miners can also solve FRG blocks. This could increase genuine FRG honest work *only if miners and pools adopt it*. It changes FRG block-validity and chain-selection rules, hence requires a separate specification, cryptographic review, stressnet and coordinated **hard fork**, not a wallet/pool toggle. Design coinbase commitment, deterministic RandomX seed binding, proof-of-work target, duplicate/replay protection, alternative-chain/reorg safety and fair difficulty accounting.

Tari currently runs multiple independent PoW lanes; those algorithms, policies and reward splits should not be copied into FRG by implication. Any merged-mining security claims must be demonstrated with decentralized participating hashrate and pool distribution. See [Tari/XMR feasibility and 51% safety plan](docs/SECURITY_51_PERCENT_AND_TARI_MERGE_MINING_2026-11-02.md), [Tari implemented RFC](https://rfc.tari.com/RFC-0132_Merge_Mining_Monero), [open implementation issue](https://github.com/tgibbsz32/forgecoin/issues/194). These remain proposals, **not guaranteed upgrades**.

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
