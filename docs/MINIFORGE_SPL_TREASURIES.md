# miniFORGE (mFRG) — Solana SPL token, treasuries and public-release conditions

**October 27, 2026 — planned mFRG Solana mainnet allocation, NOT issued or offered.**

miniFORGE (mFRG) is a **separate fungible Solana SPL asset**, not native ForgeCoin (FRG), not a privacy upgrade, not a mining subsidy, and not the future 1:1 deposit-backed wrapped FRG (wFRG). Creating mFRG does not automatically create exchange liquidity or a price. Nothing in this plan redirects native FRG Proof-of-Work rewards or creates a native FRG premine. Solana balances and trades are publicly visible.

## Proposed exactly 50,000,000 mFRG maximum distribution

| Restricted allocation | Tokens | Percent | Immediate purpose |
| --- | ---: | ---: | --- |
| Future sale/trading treasury | 5,000,000 | 10% | Hold pending separately approved future potential mFRG sale or trades against USDC/other tokens |
| Future liquidity reserve | 5,000,000 | 10% | Hold for possible future liquidity when FRG develops observed economic value; not yet placed in a DEX |
| Future distribution reserve | 40,000,000 | 80% | Hold until an independently reviewed and publicly described distribution mechanism is adopted |
| **Total planned** | **50,000,000** | **100%** | **Not yet issued on mainnet** |

The proposal uses **standard SPL Token** (not Token-2022 extensions) and **6 decimals**. Target native units: 50,000,000,000,000 base units. Minting exactly 50m and assigning balances are not enough to enforce a fixed cap while an active mint authority can issue more. The irreversible decision to revoke mint authority must occur only after token issuance, proof of all three destinations, final metadata/custody reconciliation and explicit owner signoff.

### Chain state / identity

- **Devnet development-only mint:** 9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw, on-chain verified using Solana CLI with 6 decimals. The devnet mint has **0 issued units**; it is not a mainnet token or a treasury with mFRG in it.
- **Mainnet mint:** NOT CREATED. Do not display devnet mint as mainnet mFRG or accept deposits/transfers to it expecting production value.
- **Mainnet funding wallet (public address only):** 2xLoLobNEk39Vne4FhG91i2j14Pxq75M4RAt4Pvwrk26, observed with 0 mainnet SOL at the October 27 preflight. No private key, seed phrase or account credential should be committed into a repository.
- **Budget:** mainnet mint rent ~0.0010668 SOL, three standard account rents ~3 × 0.00148844 SOL = 0.00446532 SOL, total rent baseline ~0.00553212 SOL, plus metadata accounts, signatures, priority fees and margins. Recommended funding budget **0.10 mainnet SOL** (not an exact guaranteed fee). Even 0.05 SOL may suffice for a simple mint, but refresh quotes before signing.
- **Production controls:** separate verified token accounts for all three allocations; decide independently controlled custody, ideally multi-party treasury signing rather than interpreting separate accounts under one signer as independent security. Securely back up/rotate signing keys. Keep sale, liquidity and distribution authorizations distinct; publish addresses and balances after issue.
- **Metadata:** Metaplex-compatible token name miniFORGE, ticker mFRG, icon, verified metadata URI, immutable/stewarded update authority policy. A base SPL mint alone does not render a name or logo in third-party wallets.
- **Market and legal:** Do not publish an executable offer, guaranteed investment claims, fake valuation, return or liquidity promises; determine compliance and sale terms before selling for USDC or other consideration.

### Required evidence to call it mainnet-ready

1. Mainnet funding, secure custody and explicit approval of three owner accounts and mint/freeze/update authorities.
2. Mainnet mint address and confirmed creation signature.
3. Exactly 50m tokens issued in total, exactly 5m/5m/40m in confirmed separate native token accounts, no hidden recipients, supply reconciliation in raw integer units.
4. Token metadata visible and correct; independently verified mint program/decimal/supply/authority.
5. Signed final supply policy and mint authority revocation verified on-chain if fixed cap.
6. Independent security review of desktop Solana backup/recovery, API handling, account protections and public disclosures.
7. Only then update apps/desktop/config/miniFORGE.mainnet.json with verified address and productionReady true so desktop can query mFRG balances on Solana mainnet.

### Native FRG and separate future wFRG bridge

Native FRG remains a separate eight-decimal privacy-preserving CPU-mined chain, still genesis frozen and not authorized for public mining. A future backed wrapper **wFRG**—if implemented—must redeem native locked user deposits one-for-one; it must have distinct mint, reserves, burning, independent bridge ledger, proof of backing, finality and security controls. This document does not represent mFRG as collateralized by native FRG.

This is a token allocation **plan**, not an ICO announcement, offering memorandum, a treasury authorization, or permission to bypass native FRG's hard launch gates.
