# mFRG exchange design (prelaunch, non-transactional)

Status: **Design / preview only.** No wallet deposits, purchase quotes, treasury inventory, swap endpoint or on-chain transactions are enabled by the preview page `docs/exchange.html`.

## Asset identity and non-interchangeability

- **FRG** is the ForgeCoin native L1 mined asset.
- **No wrapped native-FRG bridge is part of the current project roadmap.** Native FRG and proposed mFRG are distinct network assets; there is no audited cross-chain conversion or redemption protocol.
- **mFRG** (miniFORGE) is a separate planned 50M standard SPL asset: 5M intended sale inventory, 5M post-sale liquidity/staking treasury, 40M future issuance/development treasury. mFRG is **not** redeemable 1:1 for native FRG merely because the names are related.
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

## Prior tokenomics assumptions requiring confirmation

Earlier plans discussed 55 million mFRG SPL tokens, with 4 million for sale, 1 million participation incentives, and 50 million held for later allocation; a later proposal considered reserving 5 million from the held amount for liquidity. These are planning figures, not verified mainnet allocations. Reconcile them against the final mint authority and on-chain inventory before publishing sale quantities.


## October 27 superseding decision

The live project plan is 5M mFRG sale, a separate 5M mFRG post-sale liquidity/staking treasury, and 40M mFRG future issuance/development reserve, with a governance solution chosen before the sale concludes. Any older 55M or wrapped-bridge material above is archived research, not current direction. No sale, exchange listing, staking or liquidity service is live.
