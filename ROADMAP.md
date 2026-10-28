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

## Phase 2 - miniFORGE (mFRG) SPL issuance and proposed sale

- **50,000,000 mFRG target supply**, standard SPL Token, **6 decimals**, separate from native FRG. The devnet mint is development-only; an independently verified Solana mainnet mint and fully funded allocation are required before any sale can open.
- **5,000,000 mFRG (10%)** is designated as initial sale inventory. The proposed first payment asset is native Solana USDC, but **no sale is open**, and no price, sale dates, approved payment recipient or buyer distribution exists. Do not send any funds.
- Only after independent identity/metadata checks, custody controls, legal review, published terms and audited receipt/fulfillment can a sale go live. A source-code checkout prototype is not evidence of a production escrow or approved sale.

## Phase 3 - Post-sale mFRG treasuries, distribution and governance

- The **other 5,000,000 mFRG (10%)** is allocated to a **liquidity/staking treasury after the initial sale**. It is not the 5M sale inventory being sold twice. Liquidity provision, staking contracts, yield/reward source, withdrawal policy, custody and treasury approvals are NOT implemented or promised.
- The remaining **40,000,000 mFRG (80%)** belongs in the **future issuance and development treasury**. Release from that reserve only under future publicly approved, independently controlled treasury rules. In this context, future issuance means *staged circulation/distribution from the reserved 40M*, not a new mint above the proposed 50M total. If mint authority remains active, the total is a policy target rather than an immutable cap until it is revoked.
- **Governance policy milestone:** select, document and announce the governance framework **before the mFRG sale concludes**. Chamber size, voting structure, participant rights, staking relationships, decision thresholds, conflict handling, treasury signers and enforcement are undecided; the former ten-seat chamber is withdrawn as current direction. No live governance or deposit service exists.
- Record precise addresses, signer powers and on-chain balances for all allocations, verify independent custody/approvals and disclose treasury expenditures and release decisions. None of these treasuries represent a native FRG mining premine.

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
- [mFRG 5M / 5M / 40M treasury plan](docs/MINIFORGE_SPL_TREASURIES.md)
- [Sales engineering gates](docs/MINIFORGE_SALE_MECHANISM.md)
- [Provisional governance principles](governance-charter.md)
- [FCMP++/CARROT and L1–L3 architecture](docs/SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md)
- [Pool worker accounts and statistics](docs/POOL_ACCOUNT_STATISTICS_AND_SECURITY.md)

**No document here authorizes native FRG mining release, mainnet mFRG issuance, token sales, funds collection, advertised staking returns or treasury spending.**
