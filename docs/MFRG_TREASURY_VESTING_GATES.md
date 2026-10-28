# miniFORGE 500M — segregated treasury and founder vesting activation gates

**Planning specification, October 28, 2026 · No treasury token accounts, vesting contract, mint or sale created by this document.**

## 1. Supply and beneficial ownership reconciliation

The intended 500M mFRG standard Solana SPL issuance (six decimals) includes exactly nine mutually exclusive custody allocations. Accounts below are *proposed*; real addresses, signer thresholds, governance and custody are **not yet deployed or verified**.

| Account purpose | Total mFRG | Intended control / operational rule |
| --- | ---: | --- |
| Fundraising inventory | 50,000,000 | Project multisig + reviewed per-tranche distribution; **5M initial pilot limit** |
| Long-term operations and development | 100,000,000 | Project multisig; approved budgets and runway |
| Ecosystem grants | 100,000,000 | Budget approval + independent milestones and public grants register |
| Staking/participation reward inventory | 85,000,000 | Restricted rewards treasury; independently reviewed contracts, **not live** |
| Liquidity reserve | 60,000,000 | Project multisig LP custody; separately acquired quote assets |
| Engineering, audits and security | 65,000,000 | Technical acceptance + independent reviews |
| **Founder unrestricted** | **15,000,000** | Founder-controlled wallet; **3% unlocked at mFRG launch** |
| **Team label / same founder beneficiary** | **15,000,000** | Enforceable independent vesting account; 625,000 monthly months 13–36 |
| Emergency | 10,000,000 | Restricted incident-response vault and higher multisig threshold |
| **Total** | **500,000,000** | **500,000,000,000,000 atomic units** |

**Both founder allocations benefit the same person (30M, 6%)**. This must be prominently disclosed in legal documents, website, on-chain treasury registry and governance reports; do not misrepresent the second 3% as independent team ownership. A separate external-asset proceeds treasury for USDC/SOL received in future exchanges is **not a tenth mFRG allocation**.

## 2. Founder release contract specification (NOT DEPLOYED)

- Immediate founder grant: **15,000,000 mFRG**, no lock once validly distributed at the token launch time `T0`. The founder controls that allocation; project treasury cannot describe it as locked, unsellable or employee-owned.
- Deferred founder-beneficial grant: **15,000,000 mFRG** deposited into an audited non-discretionary vesting escrow with **24 releases of 625,000 mFRG** each, starting **month 13** after `T0` and completing **month 36**. Months 1–12: zero vested under this grant.
- The precise UTC launch timestamp and **calendar-month** definition must be embedded and publicly verifiable. Do not approximate each month as a 30-day interval unless explicitly approved; daylight saving and leap-year edge cases must not affect token unlock math.
- Locked principal must not be released ahead of schedule through administrator backdoors, vault ownership transfer, delegate authorities, clawbacks or mutable clock sources. If recovery or emergency controls are required, publish their exact power and independent approval.
- Beneficiary should receive vested tokens through permissionless claims or predictable scheduled distribution, with no entitlement to additional yield or FRG native assets.
- At each month **m from 13 through 36**, cumulative deferred release ceiling = `(m - 12) × 625,000 mFRG`; before month 13 it is zero. At month 24: **7,500,000** mFRG vested; at month 36: **15,000,000** mFRG vested. Add the unrestricted 15M to compute total founder-accessible tokens.
- Test 12→13 cliff, each of 24 monthly boundaries, UTC month arithmetic, early-withdrawal denial, more-than-vested claims, idempotent repeated claims, unauthorized authority changes, program upgrade authority and full distribution reconciliation.

## 3. Recommended custody and permissions (not approved or operational)

Use independently reviewed multisig controllers, proposed **3-of-5** for normal project treasury disbursements and **4-of-5** for emergency fund actions. Independence matters: one person should not hold enough controlled keys or delegates to meet quorum alone. Store all hardware-backed keys offline where practical, with clear recovery and signer-rotation policy.

Publish a registry per account with exact mint, token account address, custodial program/owner, beneficial purpose, delegates, delegated allowance, close/freeze authorities, unlock schedules, approval thresholds and independent monthly balance snapshots. Document changes to any custody authority; do not commingle project proceeds with founder personal accounts.

Fund each wallet/vault **only after** mint identity is independently verified. Reconcile sum of project token balances + valid outside holdings to the on-chain mint total; deposits into LP pools and user staking vaults are *real holders*, so do not count the same underlying tokens both as a treasury asset and as a deployed distribution.

The proposed operational plan includes at least 12 months of liquid **external-asset** runway before major discretionary token sales. An inventory of mFRG by itself is not cash, and a forecast price is not a guaranteed liquidation value. Report operating costs, grants, founder salary/payments, unlocked holdings, treasury dispositions and LP fees monthly.

## 4. Reward and fundraising safeguards

- The **85M mFRG** finite reward inventory covers proposed 30/90/180/365-day mFRG participation locks (1.00/1.10/1.20/1.40 weights), weekly accrued reward claims and seven-day cooldown after maturity. **No contract or yield is active.** This is not FRG's RandomX PoW security.
- Proposed reward budget ceilings: **3M year 1, 10M years 2–3, 25M years 4–10, 25M years 11–20, 22M years 21–30**. When depleted, rewards stop or require separately justified real operating revenue; never promise fiat returns.
- The **50M mFRG lifetime fundraising** reserve has proposed limits: **5M initial pilot**, 15M additional in year 1, 20M years 2–3, and 10M years 4–10. **A 50M long-run budget does not expand the original 5M pilot escrow limit.** The disabled Python simulation and legacy devnet-only Rust program do not authorize the user to sell tokens.
- Liquidity **60M mFRG** must be paired with properly funded USDC/SOL and reviewed for impermanent loss, slippage, custody, manipulative trading and operating risk. Holding 60M mFRG is not equivalent to having trading liquidity.
- FRG and mFRG remain independent; **no 10:1 conversion, FRG backing, guaranteed redemption, yield or mandatory SPL transfer tax** is in effect.

## 5. Release gates (all currently outstanding)

- [ ] Independently establish actual mainnet mFRG mint identity, current total supply, program, decimals, signed issuer authority and existing holder obligations
- [ ] Decide whether 500M can be reconciled with existing authorized supply, without guessing or silently issuing a new mint
- [ ] Obtain and validate founder wallet and separately approved project multisig signers (addresses not yet verified here)
- [ ] Independently audit founder vesting vault and prove 24 × 625,000 monthly release schedule from funded escrow
- [ ] Construct nine separate balance/ownership proofs and a distinct proceeds ledger; validate 500M total and avoid double counting
- [ ] Approve market/legal/consumer/tax terms before **any** USDC/SOL payment or sale contract is activated
- [ ] Independently audit staking and escrow code, guard all deferred allocations and verify release permissions
- [ ] Preserve public `sale_enabled=false` / mint address null / production `productionReady` fail-closed conditions until separate approved launch

**Operational position:** This file does not grant authority to release any founder tokens, activate sale checkout, or increase network supply. See [mainnet mint read-only verification](MFRG_SOLANA_MINT_VERIFICATION.md) and [full lifetime policy](MFRG_LIFETIME_TOKENOMICS_500M.md).
