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

## Discover Your City utility
Discover Your City is a planned persistent multiplayer real-world-geography city/property simulation. Its internal **CITY** currency remains separate from on-chain mFRG. Proposed optional checkout: display CITY packs priced in USD; derive a time-limited mFRG quote from independently validated pricing and clear fees; user chooses mFRG or existing supported payment methods; server independently verifies finalized Solana payment, exact mint, recipient, amount, expiry and transaction uniqueness; **only then** credit CITY exactly once through an auditable ledger. Screenshots, browser callbacks and unverified signatures never confer CITY. All mFRG collected from game purchases is directed to a designated ecosystem treasury; do not silently burn or redistribute it. Treasury authority, quotes, chargeback/refund handling, sanctions compliance, custody and security require review. This is a proposed integration, **not a live payment feature**.

## Native FRG distinction
Native RandomX-mined FRG and Solana mFRG are distinct assets. A potential future 1:1-backed FRG↔mFRG mechanism is a research proposal only, not a live bridge, redemption promise or claim of reserves. Any bridge needs a separately audited backing, custody, proof-of-reserves, consensus and legal design. Solana transfers do not inherit native FRG privacy.

## Migration / release blockers
The older 500M documents, scripts, treasury templates, website pages and test fixtures contain historical assumptions. **Do not use them to mint or distribute.** Before deployment: audit and migrate all references, reconcile token supply and reserve suballocations, confirm sale price and implement founder vesting, independently review mint authority/custody, complete security/legal review, and update all tests. No token transaction is authorized by this document.
