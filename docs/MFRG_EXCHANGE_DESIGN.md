# mFRG exchange design (prelaunch, non-transactional)

Status: **Design / preview only.** No wallet deposits, purchase quotes, treasury inventory, swap endpoint or on-chain transactions are enabled by the preview page `docs/exchange.html`.

## Native FRG and proposed Solana utility

- **Native FRG** is the eight-decimal RandomX-mined chain asset, with a 50M primary-emission reference and perpetual tail issuance (no permanent maximum).
- **mFRG** is a proposed 50M fixed-maximum six-decimal standard SPL token: 5M prospective presale, 5M DEX/liquidity reserve, 40M combined staking/collateral/ecosystem.
- **Intended FRG↔mFRG bridge:** **1 native FRG : 1 eligible mFRG**, with independently verified native FRG backing for every redeemable SPL token (including sale/DEX/staking inventories represented as backed). An audited escrow/redeem mechanism, complete reserves/liabilities evidence and 50M maximum bridge-capacity controls are mandatory. No conversion is live.
- **Planned use:** faster Solana transfers, supported DEX pools/swaps, optional audited mFRG staking funded from the finite reserve and verified mFRG purchases of USD-priced CITY packs in ForgeCoin's planned Discover Your City game.
- No current backing, active quote, fixed market-price peg, DEX liquidity, published official mint or redemption right is claimed. Solana transfers do not have native FRG privacy.

## Routes and phased delivery

1. Solana USDC / SOL → mFRG: first verify SPL mint address and decimals from mainnet RPC. Use a reviewed treasury-sale program for a fixed sale price and finite inventory, **or** provision actual DEX pool liquidity and connect a Solana routing provider such as Jupiter. A Jupiter quote is not a substitute for liquidity.
2. Ethereum ETH / USDC → mFRG: integrate a reviewed cross-chain order/solver provider such as deBridge, subject to supported route validation and correct Solana recipient handling. Fail closed when no route exists. Display the Ethereum source gas cost, protocol fees, order status and destination-finality conditions.
3. Add reviewed two-way native FRG ↔ eligible mFRG transfers only after a **fully reserved 1:1 bridge** is independently audited and funded, with lock/release, nonce/replay, finality/reorg, redemption, conversion precision and caps tested. No native bridge or redemption is currently enabled.
4. Later optional staking and game payments require independently audited treasury, accounting and blockchain confirmation safeguards.

## Launch-blocking configuration

- Published governance procedures **before mFRG introduction**, independently verified SPL mint, six decimals, 50M maximum, authorities, 5M/5M/40M allocations and independent audit.
- One verified native FRG per outstanding mFRG advertised as 1:1 redeemable, and a solvency plan for all presale/liquidity/staking units if backing is claimed; a $0.12 sale price does not establish FRG reserves.
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

## Historical assumptions

Older 500M allocation and automatic non-redeemability assumptions are superseded by the current [50M proposed tokenomics](MFRG_50M_CITY_TOKENOMICS.md) and expressly intended but **not implemented** audited 1:1 FRG bridging. This design does not authorize minting, sale payments, liquidity or redemption.
