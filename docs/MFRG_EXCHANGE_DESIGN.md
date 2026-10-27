# mFRG exchange design (prelaunch, non-transactional)

Status: **Design / preview only.** No wallet deposits, purchase quotes, treasury inventory, swap endpoint or on-chain transactions are enabled by the preview page `docs/exchange.html`.

## Asset identity and non-interchangeability

- **FRG** is the ForgeCoin native L1 mined asset.
- **wFRG** is the separately proposed 1:1 native-FRG-backed Solana representation. It is not yet operational.
- **mFRG** (miniFORGE) is a distinct planned SPL token, with its own mint, issuance, sale allocation and liquidity economics. mFRG is **not** redeemable 1:1 for native FRG merely because the names are related.
- Do not show a contract address, token price, circulating supply, live inventory, or buy control until verified on-chain and formally approved.

## Routes and phased delivery

1. Solana USDC / SOL → mFRG: first verify SPL mint address and decimals from mainnet RPC. Use a reviewed treasury-sale program for a fixed sale price and finite inventory, **or** provision actual DEX pool liquidity and connect a Solana routing provider such as Jupiter. A Jupiter quote is not a substitute for liquidity.
2. **Ethereum payments are explicitly out of scope.** Only native USDC on Solana and SOL will be accepted for the initial presale.
3. Two-way trading and wallet integration can follow after live inventory and user flows are secure. Native FRG conversion requires a **separate**, fully backed and audited bridge; it is never a direct mFRG redemption assumption.

## Launch-blocking configuration

- Independent confirmation of official mFRG mainnet mint, SPL program, decimals, mint and freeze authorities, supply and token allocations.
- Treasury sale decision: official price denomination, per-wallet limits, start/end, refunds, unsold-token custody, inventory and restrictions. Payment proceeds to multisig treasury vault; token inventory escrowed in dedicated program vault. **Never implement payment to a plain treasury address with manual delivery.**
- Alternative DEX route: real pool liquidity; minimum receive and slippage bounds; quotes confirmed via current API; explicit fee/price impact.
- Signed Solana wallet support using maintained adapters, hardware wallet testing, allowance minimization and chain-id verification.
- Server-side API keys/proxy, rate limits and quote expiry, with on-chain checks rather than trusting browser-calculated balances or price.
- Cross-chain quote validation: asset IDs, source/destination chain IDs, output mint, recipient ownership, recovery/refund paths, replay protection and provider outage handling.
- Independent smart-contract review, admin-key and multisig disclosure, testing on devnet/testnet, transaction simulations and monitor/incident controls.
- Legal review of primary token distribution, geographical restrictions, disclosures, consumer protections and applicable money transmission / securities laws. Do not assume a self-hosted site exempts a token sale.
- Production TLS, content security policy, allowlist of trusted external providers, anti-phishing and immutable verified token identity.

## User experience acceptance tests

- Wrong chain, rejected signature, disconnected wallet, stale quote, insufficient SOL/USDC, slippage, failed transaction simulation, concurrent sellout and provider outage fail safely.
- Recipient receives exactly the quoted or bounded minimum mFRG amount, validated via destination-chain transaction.
- Each success screen includes chain, source token, output token, recipient, actual received, fees and explorer links.
- No purchase CTA is enabled merely because UI configuration has been edited.

## Suggested integration boundaries

A public, static GitHub Pages website can host the interface; secrets and signing authorities **must not** live on GitHub Pages or browser JavaScript. Build a separately deployed restricted quote API only if necessary. Prefer wallet-signed non-custodial trades and audited settlement contracts. Repository changes should be reviewed in a draft PR and **not deployed as a functioning exchange** until all launch gates pass.

## Prior tokenomics assumptions requiring confirmation

Earlier plans discussed 55 million mFRG SPL tokens, with 4 million for sale, 1 million participation incentives, and 50 million held for later allocation; a later proposal considered reserving 5 million from the held amount for liquidity. These are planning figures, not verified mainnet allocations. Reconcile them against the final mint authority and on-chain inventory before publishing sale quantities.


## Confirmed October 27, 2026 presale planning decisions

- Fixed intended supply **50,000,000 mFRG**, SPL Token classic with 6 decimals. Allocation: **5M presale / 5M liquidity reserve / 40M protocol-staking and future distribution**. No ETH, EVM, bridge settlement or cross-chain payment for the initial sale.
- Price ladder: 1M tokens each at $0.01/$0.02/$0.03/$0.04/$0.05, maximum $150K USD gross if sold out. A single purchase crossing rounds must split precisely at inventory boundary.
- Proceeds **intended** use: 50% liquidity, 20% upgrades, 10% infrastructure/security, 20% founders; founder share 50% following settlement and 50% over six equal monthly installments. Administrative flexibility and statutory remedies must be accurately disclosed and legally reviewed. No unqualified no-refund promise.
- Devnet precedes mainnet. No live sale until the on-chain escrow/sale program enforces atomic payment-for-mFRG delivery, remaining inventory, tier pricing, authorized token mint and treasury recipients. Browser previews and server quotes are not substitutes.
- SOL purchases need a bounded, independent and expiring SOL/USD price oracle and strict min/max received; no runtime owner-supplied price without appropriate review. USDC token accounts must use the official native Solana mint, not a token with the same ticker. Never permit unrestricted sends or hidden fee deductions.
- Strong operational controls: per-purchase transaction receipts, owner-signed wallet connection, multisig treasury controls, split fund reporting, immutable audit trails, KYC/geographic restrictions where legally required, and explicit SEC/state-law assessment before solicitation.
