# mFRG exchange design (prelaunch, non-transactional)

Status: **Design / preview only.** No wallet deposits, purchase quotes, treasury inventory, swap endpoint or on-chain transactions are enabled by the preview page `docs/exchange.html`.

## Asset identity and non-interchangeability

- **FRG** is the ForgeCoin native L1 mined asset.
- **No wrapped native-FRG bridge is part of the current project roadmap.** Native FRG and proposed mFRG are distinct network assets; there is no audited cross-chain conversion or redemption protocol.
- **mFRG** (miniFORGE) is a separate proposed **500M fixed-supply standard SPL asset** (6 decimals), with **50M (10%) staged crypto-denominated fundraising inventory**, separately budgeted 60M liquidity and 85M staking incentives. The complete nine-category breakdown and the **6% total founder-beneficial allocation (3% unlocked immediately, 3% vesting months 13–36)** are in [lifetime tokenomics](MFRG_LIFETIME_TOKENOMICS_500M.md). mFRG is not redeemable for FRG at any fixed rate.
- Do not show a contract address, token price, circulating supply, live inventory, or buy control until verified on-chain and formally approved.

## Routes and phased delivery

1. Solana USDC / SOL → mFRG: first verify SPL mint address and decimals from mainnet RPC. Use a reviewed treasury-sale program for a fixed sale price and finite inventory, **or** provision actual DEX pool liquidity and connect a Solana routing provider such as Jupiter. A Jupiter quote is not a substitute for liquidity.
2. Ethereum ETH / USDC → mFRG: integrate a reviewed cross-chain order/solver provider such as deBridge, subject to supported route validation and correct Solana recipient handling. Fail closed when no route exists. Display the Ethereum source gas cost, protocol fees, order status and destination-finality conditions.
3. Two-way trading and wallet integration can follow after live inventory and user flows are secure. Native FRG conversion requires a **separate**, fully backed and audited bridge; it is never a direct mFRG redemption assumption.

## Launch-blocking configuration

- Independent confirmation of official mFRG mainnet mint, SPL program, decimals, mint and freeze authorities, supply and token allocations.
- Treasury sale decision: official price denomination, per-wallet limits, start/end, refunds, unsold-token custody, inventory and restrictions. Payment proceeds to multisig treasury vault; token inventory escrowed in dedicated program vault. **Never implement payment to a plain treasury address with manual delivery.**
- Alternative DEX route: real pool liquidity; minimum receive and slippage bounds; quotes confirmed via current API; explicit fee/price impact.
- Signed Solana and Ethereum wallet support using maintained adapters, hardware wallet testing, allowance minimization and chain-id verification.
- Server-side API keys/proxy, rate limits and quote expiry, with on-chain checks rather than trusting browser-calculated balances or price.
- Cross-chain quote validation: asset IDs, source/destination chain IDs, output mint, recipient ownership, recovery/refund paths, replay protection and provider outage handling.
- Independent smart-contract review, admin-key and multisig disclosure, testing on devnet/testnet, transaction simulations and monitor/incident controls.
- Legal review of primary token distribution, geographical restrictions, disclosures, consumer protections and applicable money transmission / securities laws. Do not assume a self-hosted site exempts a token sale.
- Production TLS, content security policy, allowlist of trusted external providers, anti-phishing and immutable verified token identity.

## User experience acceptance tests

- Wrong chain, rejected signature, disconnected wallet, stale quote, zero liquidity, quote exceeding price impact, reverted source transaction, partial cross-chain fill, delayed settlement and provider outage fail safely.
- Recipient receives exactly the quoted or bounded minimum mFRG amount, validated via destination-chain transaction.
- Each success screen includes chain, source token, output token, recipient, actual received, fees and explorer links.
- No purchase CTA is enabled merely because UI configuration has been edited.

## Suggested integration boundaries

A public, static GitHub Pages website can host the interface; secrets and signing authorities **must not** live on GitHub Pages or browser JavaScript. Build a separately deployed restricted quote API only if necessary. Prefer wallet-signed non-custodial trades and audited settlement contracts. Repository changes should be reviewed in a draft PR and **not deployed as a functioning exchange** until all launch gates pass.

## Superseded historical assumptions

The historical 55M, 50M and three-bucket mFRG plans are **superseded** by the October 28, 2026 **500M intended fixed supply** and [nine-category lifetime distribution](MFRG_LIFETIME_TOKENOMICS_500M.md). This document remains an informational exchange design and does not authorize payments, minting, a swap or liquidity. Native FRG remains an independent PoW asset with a continuing tail-emission policy.
