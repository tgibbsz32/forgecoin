# mFRG issuance and website presale deployment runbook (draft, not authorized to launch)

## Final project inputs

Network: Solana mainnet-beta; **SPL Token classic**, six decimals; name miniFORGE; symbol mFRG; fixed intended supply **50,000,000.000000 mFRG** = **50,000,000,000,000 base units**. Sale inventory 5M, reserve liquidity 5M, future staking/protocol/distribution reserve 40M. All vault addresses are **UNASSIGNED**; no private keys are stored in Git. Mainnet mint address: **NOT YET VERIFIED OR CREATED**. Any existing devnet token is a separate mint and does not carry to mainnet.

## Secure mint workflow — gate before irreversible mainnet operations

1. Confirm no existing official mainnet mFRG mint. Independently review the 50M tokenomics, six decimals, reserve owners, fee budget, metadata URI, use of token program, issuance authority and freeze authority policy. Verify source wallet public addresses on hardware devices, not screenshots.
2. Prepare distinct **multisig-controlled** owner accounts for sale program escrow (5M), liquidity (5M), protocol reserve (40M), USD stablecoin proceeds, and founder vesting. One Solana address can control multiple associated token accounts (SOL and USDC); separation is for policy and accounting, not token mechanics. Never use private keys in website code, repo or chat.
3. Deploy and independently verify mint with 6 decimals on **devnet**; create associated token accounts, mint exactly the 50M test supply and transfer exact allocations. Verify mint, supply, program, signer roles and balances via independent RPC and a block explorer.
4. Once security and legal reviews are complete, repeat on **mainnet** using funded hardware/multisig fee payers. Record mint address and deployment signatures. Mint precisely once, distribute to controlled vaults and reconcile totals. Decide whether to **revoke mint authority** to cryptographically enforce 50M fixed supply (the strongest fixed-supply policy); if chosen, confirm all tokens are issued and allocated first because revocation is irreversible. Disclose freeze authority and its revocation/retention separately.
5. Verify mint, metadata, full 50M supply, account owners and vesting restrictions from two independent mainnet RPC sources before publishing any mint address or deposits.

## Sale program specifications

**Do not simply ask buyers to send USDC or SOL to an address.** Use an audited atomic exchange program. Price tiers in micro-USDC per whole mFRG are 10000/20000/30000/40000/50000. Each tier has exactly 1,000,000,000,000 token base units. See `services/mfrg-sale/mfrg-quote.mjs` for integer quote reference logic; this off-chain helper is **not** authoritative for inventory and cannot release sale tokens.

Required on-chain state: controlled mFRG mint, authorized USDC mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`, treasury/vault owner keys, start/end timestamps, sold-token count, paused flag, cumulative receipts, optional eligibility assertions and buyer maximums. Purchase validates exact account owner/program and quote expiry, user-signed transfer, current inventory, tier splits, output mint and recipient token account, and performs mFRG transfer atomically or fully reverts. Use checked arithmetic, race-safe sequencing, signed transaction simulation, arbitrary wallet tests and adversarial account-substitution tests.

USDC route: native Solana SPL USDC, six decimals, settled atomically with mFRG. SOL route: after independently sourced SOL/USD TWAP/oracle and deviation limits are security-reviewed, atomic SOL receipt and mFRG transfer; use max-age, confidence and slippage bounds. A preview price quote may vary before signature; only on-chain transaction execution establishes sale terms.

Frontend: Solana wallet adapter; choose USDC/SOL; show wallet balance, tier, cost, split tiers, token quantity, live inventory, price source, quote expiry, limits, receipt, and no-guarantee risk/eligibility disclosures; default disabled if config/health checks fail. Do not include a server-side hot-wallet transfer process to deliver tokens after off-chain purchase.

Treasury: 50% liquidity, 20% network development, 10% audits/infrastructure, 20% founder amounts of **eligible proceeds** under separately approved terms. Founder share: half upon specified settlement and remainder six equal monthly installments. Decide gross/net basis, settlement date, SOL conversion timing, legal obligations and on-chain vesting safeguards before funding. Publish USD fair-market-value accounting and report actual spending and any deviation.

## Tests and launch gates

- Correct quoted amounts for all tiers, micro-unit rounding, tier boundary and sold-out; concurrency two buyers at final token; cancellation and all recipient substitution cases.
- Full devnet end-to-end wallet flows for USDC and SOL, multisig operations and founder vesting; unit, integration, property and independent security review; production health/pause controls.
- Asset-id and RPC validation, oracle freshness, provider outage, insufficient fee balance and wallet disconnection.
- Legal opinion on offering structure, geographic buyer eligibility, securities, consumer-protection, AML/custody/payment activity, taxes and risk language. *No disclaimer grants immunity.*
- **No presale live before these gates are met; mainnet minting also requires verified treasury keys and approval.**

Official references: https://solana.com/docs/tokens/basics/create-mint ; https://solana.com/docs/tokens/basics/set-authority ; https://solana.com/docs/payments/how-payments-work
