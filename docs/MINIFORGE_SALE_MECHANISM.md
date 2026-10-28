# miniFORGE (mFRG) — cryptocurrency exchange distribution, technical gates

**Status October 28, 2026: DESIGNED / DISABLED. No deposits, quotes, exchange orders, wallet signing or token fulfillment are available on the website.** This specification supersedes older 50M-total / 5M-sale inventory assumptions **as an intended future policy only**. Production backend and simulator parameters are NOT automatically migrated by changing this document.

## Policy and inventory

**Intended supply:** 500,000,000 standard SPL mFRG (6 decimals), subject to verified mint and authority. **Maximum fundraising inventory: 50,000,000 (10%)**: 5M pilot at launch, 15M further in year 1, 20M years 2–3 and 10M years 4–10. No sale price, eligibility, allocation to purchasers, opening date, payment address or distribution mechanism is approved.

The other **450M mFRG** is earmarked in eight separate categories as disclosed in [lifetime tokenomics](MFRG_LIFETIME_TOKENOMICS_500M.md), including **30M (6%) founder-beneficial holdings**: 15M unlocked immediately; 15M vesting by 625k monthly in months 13–36. They are **not available for checkout inventory**. Liquidity, staking and operating treasury funds are also **not** sale inventory.

**Exchange consideration:** Initially evaluate canonical Solana USDC (mainnet mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`), with SOL and other coins only after independent settlement, pricing, custody and legal reviews. Accepting cryptocurrency instead of USD does not exempt sales from securities, money transmission, AML/sanctions or tax requirements. Quotes and receipts must state asset mint, network, slippage, exact integer consideration, receiving treasury, refund terms, participant restrictions and independent expiry.

## Required reviewed flow — not available yet

1. Verify mainnet mFRG mint, 6 decimals, supply, all treasury inventories, mint/freeze authorities, token metadata, vesting and project signers. If existing mint authority was revoked below 500M, plan a transparent migration; do not describe a mint increase as possible.
2. Publish legal-reviewed distribution terms, risk disclosure, supported consideration assets, valuation/auction or clearing rules, eligibility, timing and maximum commitments. Obtain jurisdiction-specific professional advice before solicitation.
3. Require a user-initiated wallet connection. Never request recovery secrets. An independently authenticated server must verify treasury inventory **only within the 50M fundraising allocation**, enforce tranche ceilings, reservations, exact atomic arithmetic, rate limits and correct network/mint.
4. Prefer an independently audited on-chain **atomic crypto-for-mFRG settlement** so consideration and delivery either both occur or both fail. For any alternate custodial delivery, specify escrow, refunds, incident handling and legal obligations. Validate transaction finality, recipient, token accounts and amounts against independently sourced RPC data.
5. Ensure idempotent receipts, prevention of reused signatures, double-spends, replay and stale quotes, and handling for chain outage/reorganizations. Maintain a ledger with crypto consideration value and token cost basis.
6. Keep browser checkout **hard-disabled** until reviewed smart contracts, a legal offering process, funded inventory and production acceptance tests are complete. Editing `sale-status.json` alone cannot make the site transactional.

## Existing sandbox modules — caution

A former offline quote/reservation test module was built around a **5M maximum inventory** and synthetic USDC-only unit prices; it is **legacy test software** that must be reviewed and updated to the actual approved tranche parameters if a future offering is authorized. The read-only WSGI status endpoints and static site **must not** accept payment. Existing receipt validation tests are not an audit and do not prove production readiness.

## Pre-opening go/no-go checklist

- [ ] Independent on-chain mainnet mint/address and fully reconciled 500M intent; verified final mint/freeze authority policies
- [ ] Nine allocation accounts reconciled; founder's unrestricted and vested beneficial ownership publicly disclosed
- [ ] Multisig funding and separate sale proceeds treasury; test withdrawal, incident and signer recovery
- [ ] Contract audit of payment/settlement, staking and vesting as applicable
- [ ] Legal, tax and financial compliance approval for chosen jurisdictions and crypto consideration
- [ ] Published exact inventory tranche, pricing method, dates, eligibility and refunds
- [ ] End-to-end devnet tests with adversarial wallet, stale price, RPC fault and duplicate/failed payment scenarios
- [ ] Accessible, accurate website with no live controls until authorization and independently reviewed release
- [ ] Native FRG chain launch gates resolved **separately**; not implied by mFRG issuance

**No solicitation, returns representation or guaranteed listing.**
