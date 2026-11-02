# miniFORGE (mFRG) — proposed sale and settlement readiness

**Updated November 2, 2026. Design only; checkout and payment collection are disabled.** No mint, DEX swap, bridge, staking product or sale is active.

## Proposed supply and sale policy

- Standard six-decimal Solana SPL token; proposed maximum **50,000,000 mFRG**.
- **5M** initial sale inventory, **5M** future DEX liquidity, **40M** combined staking/collateral/ecosystem reserve. No separate founder token supply.
- Proposed uniform **$0.12/mFRG** sale price; $600,000 illustrative maximum gross if all 5M sell. Intended use of actual proceeds: **90% project / 10% founder**, half founder proceeds immediately and half over six monthly releases. No approved sale offer or deposit address.
- SOL and verified Solana USDC are proposed settlement assets, subject to audited pricing, legal conditions, secure custody and payment verification.

## Intended 1:1 bridge and solvent sale conditions

ForgeCoin intends a secure **1 native FRG : 1 eligible mFRG** redemption bridge to enable faster Solana transfers, supported DEX trades and optional finite-reserve mFRG staking. **If sale tokens are advertised as FRG-redeemable, secure and independently prove one native FRG for each such mFRG *before* issuing it.** SOL/USDC sale proceeds are not FRG collateral. Full coverage across fungible presale, liquidity and reserve inventory must be established before any universal 1:1 representation. The 50M mFRG cap limits bridge capacity while native FRG tail issuance continues. Fully preminted/authority-revoked mFRG requires escrowed inventory and lock-release, plus 8-to-6 decimal conversion and dust/fee rules.

## Mandatory launch gates

1. Verify native FRG release status and **adopt/publish governance procedures before mFRG introduction**.
2. Authenticate intended Solana SPL mint, six decimals, total supply, authorities, governance, token allocation and program security.
3. Independently audit custody, FRG reserves, eligible redemption liabilities, bridge finality/reorg/replay safety and emergency withdrawal/incident paths.
4. Approve legal sale conditions, treasury signers, founder-proceeds vesting, participant restrictions and applicable regulatory compliance.
5. Validate independently sourced SOL/USDC price quotes, atomic settlement where possible, on-chain finality, refund conditions, funded inventory and account reconciliation.
6. Enforce exact mint/chain/recipient/amount/expiry checks, idempotent receipts, replay prevention, authorization and production end-to-end failure testing.
7. Keep all interactive checkout and payment receiver endpoints **disabled** until explicit authorization; a static status JSON edit must not activate a sale.

## DEX, staking and Discover Your City

Future uses include independently funded Solana DEX liquidity, optional finite-reserve staking (no guaranteed APY), and verified mFRG payments for USD-priced CITY packs in ForgeCoin's planned **Discover Your City** game. Only finalized verified payments can credit CITY exactly once; 100% of received mFRG goes to the designated ecosystem treasury. These features are not live.

[Tokenomics](MFRG_50M_CITY_TOKENOMICS.md) · [Treasury controls](MINIFORGE_SPL_TREASURIES.md) · [Exchange roadmap](MFRG_EXCHANGE_DESIGN.md)
