# ForgeCoin Solana SPL proposal — 50 million mFRG (October 27, 2026)

**Proposal and devnet development only — not minted, sold, traded, bridged or authorized for mainnet.**

## Proposed independent SPL asset

- Working symbol: **mFRG**; original **SPL Token** program, not Token-2022; draft 9-decimal token.
- **50,000,000 total allocation**:
  - **5,000,000 (10%)** reserved for a future USDC-denominated sale, exchange trading and/or liquidity. These are not circulating and no price, trading pair, swap route or commitment to sell exists.
  - **45,000,000 (90%)** reserved for future distribution/utility decisions. Not circulating or assigned to miners/founders by this allocation.
- SPL mint maximum supply is **not a native immutable field**; enforce a real cap only by reconciled issuance and final, verified removal of mint authority (with transparent inventories and custody review), or by independently audited capped minting logic.
- Any sale or liquidity pool additionally requires clear disclosure of ownership, lockups, treasury controls, authority keys, applicable consumer/financial/securities requirements, exchange risks, audit and user protections.

## Why this is NOT wrapped FRG

Native **FRG** is mined on a separate Monero-derived blockchain with private ledger transactions and a separate emissions policy. **mFRG in this plan is an independent token**: it is not automatically redeemable for native FRG, and its 50-million allocation is not backed by on-chain locks of 50 million FRG. **Never call mFRG a 1:1 backed bridge token unless an audited lock/mint/burn/unlock design and provable reserves actually exist.**

A later separate bridge proposal may create a properly collateralized representation, but it needs user approvals and a clearly distinct ticker/asset identity to prevent confusion or double claims.

## Wallet and public claims

The Solana wallet tab is deliberately **greyed out and non-interactive** until independently tested. Native FRG mining/wallet controls remain separate. Do not show fake SOL, mFRG or USDC balances; when devnet mint addresses or connected APIs do not exist, show `Unavailable` or `Not configured`.

*All token and roadmap details are proposals for future implementation and are not guaranteed.*
