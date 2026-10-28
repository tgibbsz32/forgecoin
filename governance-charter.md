# ForgeCoin Governance Framework - Open Design Charter

**Updated October 27, 2026. Status: design principles only, not a ratified constitution.**
**The old ten-seat chamber proposal is withdrawn as current direction.** The project has NOT selected a replacement chamber, voter eligibility, on-chain voting system, binding mandate, staking arrangement or treasury signer model.

## Commitment and decision milestone

The project intends to select and publish a governance solution **before any authorized mFRG distribution begins**. This is a project milestone and does not imply that the sale has opened, that any ending date has been announced, or that buyer rights have been established. A finalized governance charter should explicitly describe any on-chain/off-chain operation and effective dates before funds or tokens are governed under it.

## Scope: two separate assets

- **Native ForgeCoin (FRG)** is issued via PoW consensus (50M primary-emission reference, not cap; 0.20 FRG tail). Full node operators voluntarily adopt consensus releases. No project committee, mFRG tokenholder or hosted voting API can rewrite consensus automatically.
- **miniFORGE (mFRG)** is a separate planned 500M standard Solana SPL token, allocated across nine categories (50M staged cryptocurrency fundraising, 100M operations, 100M adoption, 85M finite staking rewards, 60M liquidity, 65M engineering/security, 15M founder immediately unlocked, 15M founder-beneficial team-labeled vesting in months 13–36, 10M emergency). Both 3% buckets benefit the **same founder**. These are proposed allocations, not verified funds, staking, sale or voting rights. See [full plan](docs/MFRG_LIFETIME_TOKENOMICS_500M.md).
- The project-managed **1% eligible-reward mining-pool fee wallet** is separate from any governance/community treasury, the mFRG sale assets, and the eventual mFRG reserves. No automatic assignment of pool fees to governance is enacted.

## Principles that any future solution should address

1. **Community participation:** transparent submission of proposals, deliberation, published status, and meaningful feedback from miners, developers, users and infrastructure operators without requiring an arbitrary fixed number of seats.
2. **Legitimacy and eligibility:** privacy-preserving proof of independent participation, anti-Sybil defenses, fair appeals, challenge processes and options for non-token holders. No voting powers or required token bonding are approved now.
3. **Conflicts and protections:** disclose project interests, conflicts, recusal conditions, changing authority limits and independent security review. Do not imply founder veto, token majority or miner hash power automatically controls project assets.
4. **Treasury oversight:** the revised nine-category 500M mFRG allocation (including separate 60M liquidity and 85M staking reserves and 30M founder-beneficial holdings) needs independent custody, published approved budgets, signer thresholds, withdrawal/recovery controls, periodic reconciliation and auditable authorization. Specific amounts and powers are pending.
5. **Protocol accountability:** native FRG consensus rules require peer-reviewed updates and independent node adoption; a governance ballot alone cannot spend FRG, mint mFRG, activate staking, change native fees or force forks.
6. **Financial protections:** no yield, fixed price, dividend, collateral backing or guaranteed redemption entitlement follows from holding or staking FRG/mFRG absent separately implemented, reviewed and clearly disclosed programs.
7. **Transparency:** publish decisions, timetables, changes, implementation status, fees and treasury reports with privacy-preserving evidence that does not disclose spend keys or unnecessary personal data.
8. **Security and rollout:** independent audits and tests, emergency pause/recovery policies, rate limiting and separation of public UI from key custody/payout services are required before any production deployment.

## Governance options remaining open

Potential designs include community-managed off-chain proposals, representative governance, verified-holder proposals, user/miner councils, hybrid treasury oversight or protocol-enforced voting. These are options **for evaluation**, not decisions. Define constituency participation, vote weight, term or recall rules, quorum, supermajority thresholds, eligible actions, privacy model and constraints before choosing a solution.

## The existing practice election software is archival

Legacy test elections, simulated governance/FRG bond models, login categories and administrative dashboards are **nonbinding prototypes**. They provide no real voting registration, FRG lock, reward program, mFRG stake, payout right, election or treasury spending authority. Do not deploy them as the current governance protocol or ask users to submit wallet keys, passwords or money to participate.

## Release and regulatory status

No governance mechanism is ratified; the sale is not open, miniFORGE mainnet issuance is not verified, and the native FRG network remains under release restrictions. Regulatory, operational and security decisions are pending. See [roadmap](ROADMAP.md), [mFRG tokenomics](docs/MINIFORGE_SPL_TREASURIES.md), [sale information](docs/miniforge-sale.html) and [current native FRG status](docs/CURRENT_MAINNET.md).
