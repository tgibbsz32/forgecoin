# miniFORGE (mFRG) — revised 50M policy and CITY integration
Status: **proposed, predeployment** · November 1, 2026. This revision supersedes the 500M allocation policy as a planning target, **not** as evidence of an executed mint, enforceable vesting, sale approval or audited deployment.

## Supply and allocation
Standard Solana SPL Token (not Token-2022); six decimals; intended immutable maximum supply **50,000,000 mFRG**. A fixed supply requires on-chain supply reconciliation and permanent revocation of mint authority after an independently reviewed issuance.

| Purpose | Tokens | Share |
|---|---:|---:|
| Initial presale inventory | 5,000,000 | 10% |
| Future liquidity reserve | 5,000,000 | 10% |
| Staking, collateral and ecosystem reserve, including game integration | 40,000,000 | 80% |
| **Total** | **50,000,000** | **100%** |

The 40M reserve is a **combined ceiling**, not three separately funded 40M budgets. Its suballocations, custody and release schedule require approval before deployment. **No founder token-supply allocation is created by the presale proceeds policy.** No allocation can be counted twice.

## Sale
Up to 5M tokens are earmarked for an initial sale, not an active offering. SOL and Solana USDC are proposed settlement assets. **Proposed uniform presale price: $0.12 per mFRG**, replacing the previous five price tiers. At full subscription of 5M tokens this equals $600,000 gross before costs and taxes. This is not an active offering. No checkout, payment address, public solicitation or sale activation before legal review, verified custody and explicit owner authorization. Proposed presale proceeds split: **90% project / 10% founders**, calculated from actual gross receipts. Founder proceeds: **50% immediately on receipt, 50% vested over six months** in six monthly installments. At $0.12 per mFRG and full sale of 5M tokens, illustrative gross receipts are $600,000, project share $540,000 and founder share $60,000 ($30,000 immediate and $30,000 deferred). This is a proposed allocation of sale proceeds, **not** an allocation of additional mFRG tokens, and remains subject to legal, accounting, tax and custody review.

## Intended 1:1 FRG bridge and Solana utility

The future mFRG role is to represent eligible native FRG in the Solana ecosystem at a targeted **1 FRG : 1 mFRG unit conversion**, enabling faster Solana transfers, supported decentralized-exchange (DEX) trading, optional staking and ecosystem payments. This is a **development intention after native FRG release and governance adoption**, not a live bridge, assured redemption, fixed DEX market-price peg or privacy guarantee.

**Backing and redemption:** To describe any mFRG as 1:1 redeemable, one independent native FRG must be verifiably locked or otherwise secured as available backing for each such outstanding mFRG. Presale inventory (5M), DEX/liquidity inventory (5M) and tokens drawn from the 40M reserve cannot be advertised as redeemable without equivalent native FRG collateral. If backed and unbacked tokens share one fungible mint, governance and audits must resolve the resulting ambiguity **before distribution**; no current token is verified backed. Publish native reserves, Solana liabilities, lock/release flows, custody and signers, double-counting prevention, proof-of-reserves, emergency exits and independent audits.

**Supply constraint:** mFRG's proposed fixed 50M ceiling does not cap native FRG, which issues perpetual tail rewards. Therefore not every future FRG could necessarily convert simultaneously. A prefunded, fully minted SPL supply with revoked mint authority would use reviewed escrow/lock-release inventory, not unbounded new minting. FRG has eight decimal places and mFRG six, requiring deterministic 100:1 atomic-unit scaling, clear dust, rounding and fee treatment.

**DEX and staking:** Use independently funded Solana liquidity pools and supported wallet-signed trading routes; disclose pool prices, slippage, market risk and fees. A 1:1 token-unit redemption mechanism does not guarantee a 1:1 **market price** against USD, SOL or any other asset. Staking is an optional future audited participation program; rewards must be funded out of an approved finite suballocation of the combined 40M reserve, not native proof-of-work issuance. No APY, lock terms or rewards are guaranteed. Solana transactions are public, not private like native FRG.

## Discover Your City utility
Discover Your City is a planned persistent multiplayer real-world-geography city/property simulation. Its internal **CITY** currency remains separate from on-chain mFRG. Proposed optional checkout: display CITY packs priced in USD; derive a time-limited mFRG quote from independently validated pricing and clear fees; user chooses mFRG or existing supported payment methods; server independently verifies finalized Solana payment, exact mint, recipient, amount, expiry and transaction uniqueness; **only then** credit CITY exactly once through an auditable ledger. Screenshots, browser callbacks and unverified signatures never confer CITY. All mFRG collected from game purchases is directed to a designated ecosystem treasury; do not silently burn or redistribute it. Treasury authority, quotes, chargeback/refund handling, sanctions compliance, custody and security require review. This is a proposed integration, **not a live payment feature**.

## Native FRG distinction
Native RandomX-mined FRG and Solana mFRG are separate chain assets, but the intended interoperability model is an **audited 1 FRG : 1 mFRG fully backed bridge for eligible units**. This is not yet an operational conversion, a present redemption entitlement, verified reserves or a promise of a fixed market price. Reserve/custody proof, secure cross-chain verification, governance and legal approval are required. Solana transfers do not inherit native FRG privacy.

## Migration / release blockers
The older 500M documents, scripts, treasury templates, website pages and test fixtures contain historical assumptions. **Do not use them to mint or distribute.** Before deployment: audit and migrate all references, reconcile token supply and reserve suballocations, confirm sale price and implement founder vesting, independently review mint authority/custody, complete security/legal review, and update all tests. No token transaction is authorized by this document.
