# ForgeCoin development roadmap

**Updated October 27, 2026. Proposed future upgrades and their timing are not guaranteed.**
[Current native mainnet release status](docs/CURRENT_MAINNET.md) | [miniFORGE sale information](docs/miniforge-sale.html) | [mFRG treasury controls](docs/MINIFORGE_SPL_TREASURIES.md)

ForgeCoin comprises **two separate assets**: native Proof-of-Work ForgeCoin (FRG), and a proposed standard Solana SPL miniFORGE token (mFRG). mFRG is **not** a 1:1 representation of native FRG, cannot be substituted for native FRG and has no guaranteed conversion or reserve claim. A fixed mFRG price, market listing, staking return or entitlement is not established.

## Phase 1 - Independent native FRG mainnet and mining tools

- Native FRG primary-emission reference: **50 million FRG** (NOT a hard supply ceiling), with **0.20 FRG per block** perpetual tail. Native block rewards are allocated to Proof-of-Work miners, subject to consensus maturity; no founder/team ICO premine or governance reward diversion is authorized.
- The October 26, 2026 mainnet identity is frozen but public launch remains **unauthorized** pending proof of genesis-output treatment, signed-source consensus agreement and adversarial reviews. The initial difficulty is 500,000 with a 400,000 floor and staged LWMA90 activation from height 16 in the frozen specification; validate actual implementation and Block 1 before activating.
- Release and validate Windows desktop miner/wallet, Android interface as verified, local secure node/RPC, native RandomX job acceptance, verified solo/pool blocks, spendable matured rewards, restoration and cross-platform reproducibility. A preview GUI does not establish a live mainnet mining service.
- Operate a fully verified block explorer, official pool backend, network and pool statistics pages, independent worker dashboard and Pool Observer. Pools must perform real RandomX share verification, immutable accounting and reorg-safe mature payouts. The planned operator fee is **1% on eligible pooled rewards** only; solo mining is fee-independent.
- On Oracle, protect daemon/wallet RPC and payout signer, publish only tested HTTPS/web resources, secure ingress, backup, monitoring and rollback, and confirm actual network identity before advertising mining endpoints or live statistics.

## Phase 2 - miniFORGE 500M SPL policy and controlled distribution

- Adopt a proposed **500,000,000 mFRG fixed-supply policy** with standard SPL Token, 6 decimals, independent of the native FRG chain. The historical devnet mint does not confirm a mainnet issuance.
- Verify mint identity and authority before creating/funding nine non-overlapping accounts. Revoke mint authority **only after** final supply reconciliation; if the legacy mint cannot be expanded, transparently review migration.
- Disclose **founder beneficial ownership of 30M (6%)**: 15M immediately unlocked and an additional 15M (labeled team) with 625k monthly vesting in months 13–36.
- Reserve 50M (10%) for staged **crypto-for-mFRG** exchanges (5M pilot, 15M additional year 1, 20M years 2–3, 10M years 4–10). No offered price, purchase or mainnet token delivery until legal, custody, contract and settlement gates pass.
- Keep all website previews non-transactional. See [full policy](docs/MFRG_LIFETIME_TOKENOMICS_500M.md), [sale specification](docs/MINIFORGE_SALE_MECHANISM.md).

## Phase 3 - Separate treasuries, grants, staking and liquidity (all gated)

- 100M long-term operations, 100M adoption, 85M finite staking/participation rewards, 60M liquidity and 65M engineering/security; 10M emergency. Maximum release policy and quarterly budget approval detailed in the lifetime plan.
- Stage independent custody and multisig approvals, founder related-party disclosure and proof of vesting; publicly report all allocated balances and crypto received from distributions.
- Proposed stake locks: 30, 90, 180, 365 days with 1.00, 1.10, 1.20, 1.40 weighting, weekly claims and seven-day cooldown. **Not live or guaranteed; staking cannot secure FRG PoW**.
- Liquidity pools require paired USDC/SOL assets, independent reviews and market-risk reporting. No fixed FRG peg, native private Solana transactions or guaranteed token returns. Burns, if any, require explicit fee-policy implementation.

## Phase 4 - FCMP++ and CARROT native protocol upgrades

- Intend to implement FCMP++ full-chain membership proofs, curve-tree commitment/index databases with deterministic roots, generalized Bulletproof components, CARROT addressing and wallet recovery, mempool validation and legacy-output compatibility.
- Prefer a **reviewed in-place hard fork** preserving existing native FRG supply and spendability if feasible. A separate successor network and opt-in supply-conserving migration are fallback research, not an approved chain replacement.
- Run a separate adversarial stressnet, cross-platform synchronization, deep reorganization and invalid-proof suites; obtain independent cryptographic/security audits before announcing an activation height.

## Phase 5 - Additional L1, L2 and possible L3 systems

- **L1:** native atomic swaps, independently secured collateralized stable-denominated systems and multi-party TSS/MPC controlled large-trade settlement. Transparent public-chain settlement is not intrinsically private; no venue, rate or product is live.
- **L2:** authenticated payment channels, batching, secure exit/dispute procedures, data availability and privacy-aware liquidity routes.
- **L3:** potential private-market applications, auctions, merchant payments, selective disclosure, private execution and permissioned integrations. These require additional protocols beyond FCMP++/CARROT and independent legal/security review.

## Observability and website release practices

Pool network statistics, pool accounting data, worker dashboards and mining calculators are different sources. Never represent estimates, historical chains, fake online worker counts or stale API responses as current new-mainnet measurements. An address alone is insufficient authorization to change native FRG payout destinations. Pool credentials and signed payout changes require independent native-wallet ownership verification and a secure backend.

## Sources and current status

- [Native mainnet identity and blockers](docs/CURRENT_MAINNET.md)
- [Native technical whitepaper, including separate mFRG economics](docs/WHITEPAPER.md)
- [miniFORGE sale-information and allocation page](docs/miniforge-sale.html)
- [mFRG 500M nine-category lifetime treasury plan](docs/MINIFORGE_SPL_TREASURIES.md)
- [Sales engineering gates](docs/MINIFORGE_SALE_MECHANISM.md)
- [Provisional governance principles](governance-charter.md)
- [FCMP++/CARROT and L1–L3 architecture](docs/SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md)
- [Pool worker accounts and statistics](docs/POOL_ACCOUNT_STATISTICS_AND_SECURITY.md)

**No document here authorizes native FRG mining release, mainnet mFRG issuance, token sales, funds collection, advertised staking returns or treasury spending.**
