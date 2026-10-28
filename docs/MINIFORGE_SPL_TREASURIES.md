# miniFORGE (mFRG) - proposed Solana tokenomics and treasury controls

**Updated October 27, 2026. Sale is not open, and 50M mainnet issuance and token custody are not yet independently verified.**

miniFORGE (mFRG) is a **separate** 6-decimal standard Solana SPL Token asset, distinct from native Proof-of-Work ForgeCoin (FRG). Its goal and economics do not establish a fixed FRG conversion, reserve claim, dividend, guaranteed liquidity, staking yield, or inherited private transfers.

## Proposed supply and post-sale sequencing

| Allocation | mFRG | Percent | Treasury or sale policy |
| --- | ---: | ---: | --- |
| **Initial sale allocation** | 5,000,000 | 10% | Reserved inventory for a future, separately approved mFRG sale, initially contemplating USDC on Solana |
| **Post-sale liquidity/staking treasury** | 5,000,000 | 10% | A DIFFERENT 5M allocation to be held for liquidity/staking operations after the 5M sale; program mechanics and custody pending |
| **Future issuance and development treasury** | 40,000,000 | 80% | Held for later authorized releases, development funding and other publicly approved uses |
| **Total target** | **50,000,000** | **100%** | **Not a claim of verified mainnet supply** |

**Accounting distinction:** the 5M sold to purchasers is not also deposited into the 5M liquidity/staking treasury. The 5M post-sale treasury and 40M future-development treasury comprise the *remaining 45M mFRG supply allocation*. How USDC sale proceeds will be used, including how much will support liquidity or development, must be approved and separately disclosed; the 5M liquidity/staking row is a token allocation, not a proven USDC proceeds budget.

“Future issuance” describes planned distribution from the earmarked 40M reserve, NOT minting additional mFRG over the 50M target. If the project issues all 50M to treasuries first, on-chain mint authority must be irreversibly revoked under an approved supply policy to make that supply a technically enforced maximum. Until then, 50M is a target allocation.

### Verified and unverified identities

- **Token program:** standard Solana SPL Token (not Token-2022). Intended ticker mFRG, name miniFORGE, 6 decimals.
- **Devnet test mint:** 9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw, development only; test supply was zero in prior audit.
- **Solana mainnet mint, allocation accounts and metadata:** NOT verified published. No address presented here may be treated as a payment or token-sale destination.
- **Prior funding preflight:** the configured CLI wallet had 0 mainnet SOL in an earlier Oct 27 check. The 0.1 SOL recommendation is an approximate setup margin, not a current verified fee or a request to send funds to a specific address.
- **Capped supply and vesting:** 50M cap, custody, lockups, signer policy, planned distribution constraints and disclosures require documented independent review and on-chain proof.

### Sale and operations

Before opening the initial 5M sale, verify token mint, metadata, separate treasury allocations, fund custody and legal requirements; publish a price or price mechanism, window, eligibility restrictions, refund handling, accurate payment asset/recipient, transparent inventory and independently audited transaction delivery. Solana USDC is the contemplated initial payment asset, but no executable sales offer is live. Never collect deposits from an informational page.

After the sale, the **separate 5M liquidity/staking treasury** may be activated only under reviewed, published treasury decisions, custody, risk controls and audited contracts. Staking could involve token or FRG-related arrangements, but neither native FRG deposit backing nor yield arises automatically. Any announced future return, fee sharing or holder rights require explicit specifications and appropriate review.

The **40M issuance/development treasury** remains reserved for later controlled release; each release requires public accounting, governance approvals, recipient/utility specification and audits. Neither these treasuries nor a future mFRG sale creates a native FRG genesis premine.

### Governance milestone

The project intends to determine a governance solution **before the mFRG sale concludes**. No ten-seat chamber, token-voting contract, delegation model or binding quorum is ratified. The rules must specify eligibility, voting/representative authority, treasury spending controls, transparency, conflicts of interest and custody, without claiming native FRG consensus can be unilaterally changed. See the [open governance charter](../governance-charter.md).

### Technical release checks

1. Verify mint identity, program ID, 6 decimals, Solana mainnet signatures, token metadata URI and source authenticity.
2. Prove raw atomic supply and account balances with expected exact allocation, independent owner keys/multisig, freeze/mint authority and an irreversible fixed-cap decision if intended.
3. Verify sale inventory (no more than 5M), exact integer arithmetic, anti-replay receipts, secure atomic or independently guaranteed USDC-for-mFRG fulfillment and error/refund procedures.
4. Review staking/liquidity design separately: risk, legal treatment, management fees, security audits, unwind/withdrawal rights, on-chain monitoring and public disclosures.
5. Publish governance rules and signer authorizations by the sale end; review all development treasury disbursements with change-control policies.
6. Keep native FRG mainnet and official pool release gates separate; do not change existing chain consensus or bootstrap mining as part of this token distribution work.

## Canonical public links

- [miniFORGE sale page and accessible allocation explanation](miniforge-sale.html#allocation)
- [ForgeCoin technical whitepaper](WHITEPAPER.md)
- [Roadmap](../ROADMAP.md)
- [Solana sale/checkout engineering gates](MINIFORGE_SALE_MECHANISM.md)

This is a project plan, not a public offer of securities or a guarantee of value, staking payments, liquidity, anonymity or mainnet deployment.
