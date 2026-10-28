# miniFORGE (mFRG) — lifetime tokenomics, treasury and release policy

> **Adopted mFRG pilot sale planning figures (October 28, 2026):** 5M mFRG in five equal rounds at $0.08/$0.10/$0.12/$0.14/$0.16, yielding a **maximum $600,000 gross** if fully subscribed. Intended 80% project / 20% founder proceeds allocation ($120,000 founder total, half immediately and half over six months). These figures are **not an active offering, promised proceeds or permission to receive funds**. See [fixed pilot pricing and all nine token allocations](MFRG_PILOT_PRICE_AND_USE_OF_PROCEEDS.md).


**Policy revision: 28 October 2026 · Project allocation decision / implementation specification.** This document supersedes the older 50M mFRG / 5M sale / 5M combined liquidity-staking / 40M reserve proposal. **The proposed token distribution is not proof of minting, sale authorization, treasury funding, locking, deployed staking, live swaps or yield.** All financial functionality is disabled until the release gates are met.

## Two different assets

* **FRG:** The native RandomX-mined Monero-derived privacy coin. **50,000,000 FRG is the primary-emission reference, not a hard cap** in the currently documented consensus, which pays a **0.20 FRG tail subsidy per two-minute block** after the base-reward floor is reached. This mFRG policy changes no FRG consensus rule, subsidy or genesis state. See [native mainnet specification](CURRENT_MAINNET.md).
* **mFRG:** An independent standard Solana SPL token with **6 decimals** and a newly selected **fixed-supply target of 500,000,000 mFRG**. A truly enforced fixed supply requires verifying the exact mainnet mint, balances and authority, minting only the authorized total, and permanently revoking mint authority. The historical devnet mint is **not a mainnet payment destination**.

**There is no 10:1 peg, FRG collateral backing, shared emission schedule, promise of FRG redemption, guaranteed yield or inherited Solana privacy.** An optional future FRG-backed Solana wrapper, if researched, would be **a separate instrument**, not mFRG.

## Lifetime allocation: exactly 500,000,000 mFRG

| Separate budget / beneficial owner | mFRG | % | Operational designation |
| --- | ---: | ---: | --- |
| Cryptocurrency-exchange fundraising inventory | 50,000,000 | 10% | Legally reviewed staged mFRG-for-crypto distribution |
| Long-term operations and development treasury | 100,000,000 | 20% | Multisig, budgets and operating runway |
| Ecosystem adoption and grants | 100,000,000 | 20% | Milestone-funded development, payments and merchant adoption |
| Staking / participation reward reserve | 85,000,000 | 17% | Finite rewards; no mint inflation or guaranteed APY |
| Protocol-owned liquidity and integrations | 60,000,000 | 12% | Independently funded mFRG/USDC and mFRG/SOL liquidity |
| Engineering, privacy R&D, audits and security | 65,000,000 | 13% | Verified milestones and independent audits |
| **Founder — liquid at launch** | **15,000,000** | **3%** | **Unlocked immediately; founder-controlled** |
| **Team allocation — founder-beneficial** | **15,000,000** | **3%** | **625,000/month for months 13–36; also founder-controlled** |
| Emergency contingency | 10,000,000 | 2% | Restricted incident-response reserve |
| **Total** | **500,000,000** | **100%** | **All categories mutually exclusive** |

**Founder disclosure:** Both 3% buckets benefit **the same founder** (30M total, 6%). The label “team allocation” must never be described as independent employee ownership. At launch, 15M mFRG may be freely transferable with no contractual lock. The other 15M is a separately funded vesting position with **24 monthly unlocks of 625,000 mFRG**, starting in month 13 and completing in month 36. This means 7.5M unlocked during year 2 and 7.5M during year 3, no additional founder unlock after year 3. Founder salary or contract payments from operating proceeds are separate related-party expenses and require disclosure and approval. The founder's unlocked holdings may create substantial initial concentration and selling pressure.

## Maximum scheduled availability (millions of mFRG)

These are **authorization ceilings, not promises of circulation, sales or distributions**. Unused funds remain in locked custody and do not become freely tradable simply because the period arrives.

| Category | Year 1 | Years 2–3 | Years 4–10 | Years 11–20 | Years 21–30 | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Fundraising | 20 | 20 | 10 | 0 | 0 | 50 |
| Long-term operations | 3 | 9 | 20 | 32 | 36 | 100 |
| Ecosystem grants | 5 | 15 | 30 | 28 | 22 | 100 |
| Staking incentives | 3 | 10 | 25 | 25 | 22 | 85 |
| Liquidity | 20 | 12 | 12 | 10 | 6 | 60 |
| Engineering/security | 8 | 14 | 18 | 15 | 10 | 65 |
| Founder immediate | 15 | 0 | 0 | 0 | 0 | 15 |
| Founder deferred | 0 | 15 | 0 | 0 | 0 | 15 |
| Emergency | 0 | 0 | 2 | 3 | 5 | 10 |
| **Period limit** | **74** | **95** | **117** | **113** | **101** | **500** |
| **Cumulative limit** | **74** | **169** | **286** | **399** | **500** | |

**Potential initial active supply:** up to 15M founder unlocked + 5M pilot-exchange inventory delivered to purchasers + 5M initial liquidity tokens **= 25M mFRG** (5% of total), **only if** those transfers actually occur. Minted supply, unlocked supply, circulating supply, locked reserves and LP vault balances must be disclosed separately.

## Fundraising: exchanging mFRG for cryptocurrency, not necessarily fiat

The 50M fundraising inventory is a **10% maximum**. Proposed tranches: **5M pilot on launch**, **15M additional in year 1**, **20M in years 2–3**, **10M in years 4–10**. Unused inventory stays reserved; there is no automatic recurring sell order.

* Initially consider **Solana USDC**; expand to **SOL** only after separate price, settlement, custody, oracle and liquidity reviews. BTC or other assets require compatible settlement and explicit approval. An offer for cryptocurrency consideration is still an offer and potentially a taxable or regulated transaction.
* No sale price, executable quote, start date, wallet recipient or KYC framework is approved. Do **not** infer a market value from the 500M quantity. Illustrative arithmetic: a 5M exchange at $0.001 / $0.0025 / $0.005 equivalent produces $5,000 / $12,500 / $25,000 in crypto **only if fully subscribed** before costs. These are examples, **not pricing or return targets**.
* Draft a 12-month expense budget, fundraising disclosure, acceptable investor/participant rules, lock and refund rights, sanctions/AML procedures where required, legal structure and transparent use of proceeds **before** soliciting or receiving funds.
* For a future executable checkout, use independently reviewed **atomic payment-and-delivery** where practical. Never rely on a browser-only payment toggle, an unverified receiving address, or an unsecured pay-then-send model. The current website preview must remain **non-transactional**.
* Funds received are **external cryptocurrency assets**, not an additional mFRG allocation. Segregate fundraising proceeds from treasury inventory and record every receipt/disposition with cost basis and USD-equivalent valuation.

## Separate treasuries and operating policy

| Account | Holding | Intended custodian / authorization | Rule |
| --- | --- | --- | --- |
| Sale inventory | 50M mFRG | Project treasury multisig + reviewed fulfillment escrow | Release only against properly approved crypto exchanges |
| Operations/development | 100M mFRG | **Proposed** 3-of-5 multisig with independent signers | Quarterly budgets; 12-month external-asset runway objective |
| Ecosystem grants | 100M mFRG | Independent grant-approval process + treasury multisig | Milestones; remaining grant funds recoverable where possible |
| Staking rewards | 85M mFRG | Restricted vault, then audited reward distributor | Never promise APY; fund each epoch from reserved inventory |
| Liquidity | 60M mFRG | Multisig-controlled LP positions | Pair with separately budgeted USDC/SOL; withdrawals and impermanent loss disclosed |
| Security engineering | 65M mFRG | Multisig plus technical acceptance reviews | Audits, wallet/daemon upgrades, privacy research, bug bounties |
| Founder liquid | 15M mFRG | Named founder wallet | 100% unlocked at launch; related-party disclosure |
| Founder deferred (team label) | 15M mFRG | Audited non-discretionary vesting escrow | Months 13–36, 625k per month; beneficiary founder |
| Emergency | 10M mFRG | **Proposed** 4-of-5 approval / incident log | Critical incidents only; no routine payroll |
| Proceeds treasury | Received USDC/SOL/etc., **not mFRG** | Dedicated multisig and accounting ledger | Spend against approved budgets; monthly statements |

Signer thresholds, vault contracts, account addresses, contributor identities and grant-selection process are **recommendations pending approval and deployment**, not current on-chain facts. Keep founder holdings separate from project custody; do not count the same token in two reserves. Publish monthly holdings, vesting, unlocks, sales, proceeds, grants, LP positions, staking distributions, compensation, USD values and runway; reconcile to chain records.

Illustrative **net proceeds** deployment: 30% legal/security, 25% engineering, 15% matching liquidity assets, 10% infrastructure, 10% disclosed founder compensation and 10% operating contingency. These are **planning percentages only**; actual costs, taxes and audits may be higher. Avoid claiming that treasury-held mFRG represents cash or dollar-equivalent runway.

## Staking: proposed finite reward program, NOT proof-of-work security

Staking is **not live**, does **not** secure RandomX consensus, and provides **no ownership of FRG**, profit sharing, promised fiat yield or guarantee against loss. Any staking product requires independent economic, legal and smart-contract review.

| Lock chosen by participant | Weight applied to deposited amount |
| --- | ---: |
| 30 days | 1.00× |
| 90 days | 1.10× |
| 180 days | 1.20× |
| 365 days | 1.40× |

* Proposed mechanics: deposit into an audited vault; lock until maturity; **7-day withdrawal cooldown after expiry**; **weekly claims** of amounts already accrued; opt-in restaking only; no early withdrawal except a separately audited emergency policy.
* **Weighted stake = deposited mFRG × lock multiplier.**
* **Epoch reward = funded epoch distribution × (participant time-weighted eligible stake ÷ total time-weighted eligible stake).** Time weighting and cutoff logic must prevent end-of-epoch gaming and duplicate claims.
* Example: 100,000 mFRG held at 1.4× weighting against 100M eligible weighted-stake units, with 3M mFRG funded for the same epoch, gives **4,200 mFRG**, assuming all weights stay constant for the epoch. It is **not** 4.2% in dollars or a promised return.
* Finite maximum reward budgets: **3M year 1; 10M years 2–3; 25M years 4–10; 25M years 11–20; 22M years 21–30** = **85M**. After reserves deplete, rewards require genuine externally sourced revenue or stop. Never fund promised yield from new buyer deposits.
* Optional mFRG voting relates to **treasury and ecosystem policy only** until an approved governance system exists. Token votes cannot by themselves force FRG consensus upgrades or override independent node operators.

## Liquidity, service revenue, burns and interaction with FRG

* Candidate pools: **mFRG/USDC** and **mFRG/SOL** after independently verifiable mint and budgeted matching assets. Tokens alone do not create price support; pool opening prices are selected ratios, not fundamentals. Report protocol-owned LP positions, fees, impermanent loss and slippage.
* FRG's intended utility: private native payments, network fees, and miner incentives. mFRG: Solana-side governance/participation, services, grants and liquidity. Accept either asset for **optional paid services** such as merchant checkout, hosted nodes, mining/pool analytics and developer APIs where feasible.
* Potential **application-level service-fee** policy: 70% operations / 20% engineering and security / 10% mFRG burn **only for fees actually collected in mFRG under a separately deployed service policy**. Ordinary SPL transfers do not automatically burn 10%; burning does not guarantee appreciation.
* Swaps between native FRG and mFRG would be **market-rate**, with no fixed peg or issuer redemption promise. Private-chain-to-Solana atomic swaps or a limited custodial intermediary need extensive threat-model review. A hypothetical **1:1 FRG-backed Solana wrapper** would be a separately issued fully reserved asset with verifiable redemption, **not mFRG**.
* The native FRG mining-pool's separately proposed **1% fee** is a fee on that pool's accepted rewards, not a protocol-level tax on all FRG mining. Do not represent pool fees as guaranteed income.

## Thirty-year durability and legal risk

A schedule for 30 years is **not a 30-year revenue forecast**. Sustainable operation depends on independent miners/nodes, sustained security budget, merchant adoption, repeat paid service use, available liquid reserves, professional audits, transparent expense reporting and non-manipulated markets. Avoid specific appreciation probabilities or price targets.

**Review before sales and rewards:** U.S. federal and applicable state securities law, broker/exchange and money-transmission obligations, FinCEN, OFAC sanctions, participant identification as legally required, consumer terms, tax treatment of crypto-to-crypto swaps, founder compensation and rewards. The project should obtain qualified counsel and tax advice. Merely receiving cryptocurrency instead of fiat **does not** avoid these requirements.

## Release gates and implementation acceptance criteria

1. Independently verify the Solana mainnet mint identity, **500M intended supply**, **6 decimals**, token program, authorities and actual on-chain balances. If an existing mint's mint authority has been revoked below 500M, **do not claim it can be increased**; evaluate a transparently disclosed migration. Revoke mint authority only after final supply and inventory reconciliation.
2. Create separately named, safely controlled token vaults and external-asset proceeds vaults. Fund all nine non-overlapping allocations. Protect the 15M deferred-founder vesting in an independently tested contract; separately identify the 15M immediately released founder wallet.
3. Publish verified treasury addresses, signers/thresholds, vesting proof, reward budget and conflict-of-interest policy. Audit custody, distributor, and sale contracts before launch.
4. Complete a legally structured crypto-denominated distribution plan, auditable checkout/settlement and buyer protections before any payment is accepted. Keep all site purchase and wallet-signing controls disabled until approved release.
5. Deploy staking/LPs **only after** security testing and governance approval. Verify conservation of rewards, precise time-weighting, withdrawals, paused contracts and withdrawal controls.
6. Keep native FRG mainnet release gating separate. The present [native mainnet status](CURRENT_MAINNET.md) identifies unresolved public launch blockers and a tail subsidy exceeding 50M over the long run.
7. After all approvals, update the website status from verified chain evidence and deploy through reviewed releases. A static JSON status flag **cannot** activate a sale.

### Public reference pages

* [miniFORGE tokenomics website](miniforge-tokenomics.html)
* [Sale readiness website](miniforge-sale.html)
* [Sale backend engineering specification](MINIFORGE_SALE_MECHANISM.md)
* [Exchange design](MFRG_EXCHANGE_DESIGN.md)
* [Native FRG mainnet specification](CURRENT_MAINNET.md)

**Not an offer, tax opinion, prediction of token value or evidence that any allocation is on-chain.**
