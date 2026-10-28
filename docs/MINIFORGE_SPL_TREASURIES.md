# miniFORGE (mFRG) — 500M SPL allocation, custody and controls

**Updated October 28, 2026.** This page supersedes the previously proposed **50M mFRG** three-bucket allocation. **No Solana mainnet mint, funded vaults, staking, price, active sale or verified issuance is established by this documentation.**

The **authoritative detailed allocation, release schedule, founder disclosure, locking, staking, liquidity, burns, crypto-denominated fundraising and legal risk gates** are in the [500M mFRG lifetime tokenomics policy](MFRG_LIFETIME_TOKENOMICS_500M.md).

## New fixed-supply target: 500,000,000 mFRG (6 decimals)

| Separate allocation | Quantity | % |
| --- | ---: | ---: |
| Crypto-for-mFRG exchange inventory | 50,000,000 | 10% |
| Long-term operational development | 100,000,000 | 20% |
| Ecosystem adoption and grants | 100,000,000 | 20% |
| Staking/participation incentives | 85,000,000 | 17% |
| Liquidity infrastructure | 60,000,000 | 12% |
| Engineering, privacy research and audits | 65,000,000 | 13% |
| **Founder unlocked immediately** | **15,000,000** | **3%** |
| **Team label (same founder-beneficiary), months 13–36** | **15,000,000** | **3%** |
| Emergency | 10,000,000 | 2% |
| **TOTAL** | **500,000,000** | **100%** |

**The founder beneficially controls 30M mFRG in total (6%).** The first 15M has no vesting. The additional 15M vest **625,000 monthly in months 13 through 36**. The two buckets are not independent team holdings.

## Custody and treasury operations

Each allocation has a separately named and independently reconciled account or enforceable vesting vault. A proposed 3-of-5 multisig should approve routine project treasury operations, subject to independent signer and conflict-of-interest policies. A proposed 4-of-5 approval threshold applies to the emergency reserve. **These controls are proposed, not yet on-chain or ratified.**

Funds raised by mFRG-for-crypto exchanges are **external USDC/SOL/other assets**, held in a separate proceeds treasury; they are **not** 500M tokens of additional issuance. Publish wallet holdings, vesting, grant payments, treasury expenses, founder compensation, and proceeds/runway monthly. Program-owned LP positions need separate accounting.

## Distribution sequencing

Maximum availability: **74M in year 1, 95M in years 2–3, 117M in years 4–10, 113M in years 11–20 and 101M in years 21–30**. These are outer limits, not automatic circulation.

Fundraising: **5M pilot, 15M additional year 1, 20M years 2–3, 10M years 4–10**. Price, legal permissions, issuance, treasury funding and validated payment settlement are prerequisites. No sale or wallet payment collection is live.

Staking: **85M reserved for a finite participation program**, with proposed 30/90/180/365-day locks and 1.0/1.1/1.2/1.4 weights, weekly reward claims, and seven-day cooldown after lock maturity. Not live; no guaranteed yield; not a substitute for RandomX mining.

Liquidity: **60M separately reserved**, subject to matching USDC/SOL and approved LP budgets. No fixed FRG conversion. A separate, genuinely reserve-backed wrapped FRG token could only be researched and audited in a later program.

## Verified vs proposed facts

- Intended standard SPL Token, name miniFORGE, symbol mFRG, six decimals. Historical **devnet-only mint**: `9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw`.
- **No authenticated mainnet mint address or current total supply is verified in this document.** If mint authority was revoked below 500M, the existing mint cannot be increased and a disclosed migration is necessary.
- Native FRG **50M primary emission is not a strict hard cap** under documented tail emission. See [CURRENT_MAINNET](CURRENT_MAINNET.md).
- [Official sale engineering gates](MINIFORGE_SALE_MECHANISM.md) and [informational website](miniforge-sale.html) remain disabled pending implementation and review.

**No fundraising offer, staking promise or permission to accept deposits is created by this specification.**
