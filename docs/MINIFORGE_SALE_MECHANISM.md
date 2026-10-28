# miniFORGE (mFRG) sale mechanism — draft product and engineering specification

**Status: development. No USDC deposits, presale, mint, offering or mFRG delivery currently available.**

The miniFORGE webpage provides public facts and a non-transacting checkout preview. The proposed standard Solana SPL token has a **50,000,000** target supply using 6 decimals. Its intended separable allocations are:

| Allocation | mFRG | Percentage | Intended use |
| --- | ---: | ---: | --- |
| Sale / trading treasury | 5,000,000 | 10% | Potential future sales/trades against Solana USDC and later separately reviewed assets |
| Post-sale liquidity/staking treasury | 5,000,000 | 10% | A separate 5M mFRG allocation designated for treasury custody after the sale; no staking yield or pool is active |
| Future issuance and development treasury | 40,000,000 | 80% | Reserved for staged circulation/distribution and development under future approved controls; not minting beyond 50M |

Only the **sale treasury** can supply a prospective website checkout. The other **45M** (5M liquidity/staking treasury after the sale plus 40M future issuance/development treasury) must never be silently included in checkout inventory. No part of the initial 5M sold is also counted toward the separate post-sale 5M treasury. The initial contemplated payment asset is **native Circle USDC on Solana mainnet**, canonical mint EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v. Do not rely on token names or icons for security. SOL may be used by purchasers to cover network transaction fees but is *not* an approved alternative price/payment method. Any future SOL, PYUSD, USDT or other chain token payment requires separate merchant support, escrow and pricing risk review.

## Required governance deadline and treasury disclosures

Select and publish an appropriate governance model **before the 5M mFRG sale ends**. No ten-seat chamber, token-vote entitlement, staking contract or treasury-signing threshold is finalized. The eventual rules must cover independent custody, approval procedures, conflicts of interest, how any sale proceeds will be held/used, and how the 5M post-sale and 40M development reserves can be disbursed. The proposed 50M supply is an intended limit; future issuance from the 40M reserve does not authorize additional minting above it.

## Intended buyer experience

1. Visit the clearly labeled miniFORGE sale page and read the target supply, treasury disclosures and risks.
2. Connect a Solana wallet by a user-initiated wallet provider prompt. The current preview can only read a public address and must never request a seed, key export or transaction signature.
3. After lawful issuance, secure custody, an approved and publicly posted unit price and a sale opening decision, the real backend obtains verified on-chain mFRG sale inventory and an exact signed quote that is short-lived. Quantities are represented in **atomic integers** (mFRG six decimals; USDC six decimals); no floating-point currency arithmetic. The quote includes an unguessable reference and the exact chain/mint, buyer address, payment recipient, amount and expiry.
4. The purchaser's Solana wallet displays the genuine USDC mint, payment recipient, exact amount, network and expected received mFRG. The buyer explicitly approves; unsolicited DMs or deposit addresses must never be accepted.
5. **Preferred future fulfillment:** a security-reviewed Solana atomic swap/escrow program executes payment **and** delivery of mFRG in the same successful on-chain transaction. Alternative merchant-custody modes present funding and delivery risk and need separately audited safeguards and disclosures.
6. A trusted server independently validates the finalized on-chain transaction and the actual mFRG credited to the buyer before displaying a confirmed purchase receipt. Failed transfers, wrong recipient, old reference, expired quote and mismatched amounts cannot count as accepted payment. Refund and late-payment exception handling must have a documented procedure.

## Backend modules built

- Offline SQLite quote and reservation module: locks concurrent inventory, enforces dedicated 5M maximum and supports exact USDC-to-mFRG integer conversion. The configured test unit price is **synthetic** and **not an official offer or price announcement**.
- USDC receipt validator: requires the transaction to be returned by an independently trusted Solana **mainnet** RPC queried at finalized commitment; validates buyer signature, order reference, success metadata, canonical Token Program, real USDC mint, merchant USDC token account owner, exact transferChecked quantity and matching before/after USDC balances. All inner instructions are inspected for duplicate merchant transfers. This isolated validator itself performs **no network call**, so no user-provided RPC response may be accepted as production proof.
- Journal: prevents using the same transaction signature across multiple sandbox orders; explicit late-payment refund review; no transition to fulfilled without a separate independently proven delivery component.
- Public WSGI status: read-only /api/v1/status and /api/v1/allocations, with *no* purchase, wallet signing, receipt acceptance, quote, token delivery or admin action endpoints. Production payments are hard-disabled in code.
- Static website: mobile-responsive sale preview, planned allocations, wallet public-address-only connection and disabled quote/purchase button. The GitHub Pages site never contains private custody credentials and never signs on a user's behalf.

## Required for an actual opening

**No sale may open solely by editing a boolean, including sale-status.json or an environment variable.** A separate code-reviewed release is required after all below are completed:

1. Mainnet token mint created, supply reconciled and mint/freeze/metadata authorities documented; 5M sale allocation actually funded and separately controlled, 5M post-sale liquidity/staking and 40M future issuance/development reserves independently inventoried.
2. Sale beneficiary/USDC receiver account is derived and independently verified as belonging to the approved treasury, with multi-party custody, key recovery, on-chain monitoring, rent and emergency pause.
3. Jurisdiction-specific securities/consumer/financial compliance, eligibility/KYC/AML/sanctions obligations as applicable and buyer protection, refund and risk disclosures reviewed with competent counsel; avoid promises of profit, guaranteed price or liquidity.
4. Published unit price or bounded allocation/auction mechanism, sale window, per-wallet and per-user controls, fair distribution rules, exact quote expiry, supply and payment threshold constraints and terms of service.
5. **Atomically secured mFRG delivery** or other independently reviewed guaranteed-settlement architecture, audited on-chain program deployment and full devnet multiwallet end-to-end testing.
6. Production Solana RPC (reliable, independent verification, finalized commitment, correct network), duplicate payment rejection, idempotent order ledger, chain outage/reorg handling and clear customer receipt/refund history.
7. Operator monitoring and emergency shutdown; no publicly exposed treasury signing keys or unrestricted RPC endpoints; rate limiting, logging minimization and automated alerts. Publish complete addresses and transaction proofs only once appropriate.
8. Deployment/release testing: frontend, server, buyer wallet prompts, mobile access, independent on-chain audit, disabled-state regression and production roll-forward/backout procedures.

## References

- [Solana Pay transfer requests and transaction validation](https://solana.com/docs/tools/solana-pay/quickstart/transfer-requests)
- [Solana payments and canonical USDC mint](https://solana.com/docs/payments/how-payments-work)
- [Official ForgeCoin miniFORGE treasury specification](MINIFORGE_SPL_TREASURIES.md)
- [Sale backend prototype in draft PR #122](https://github.com/tgibbsz32/forgecoin/pull/122)

The sales website is an informational software preview. It is not an ICO, token solicitation, guaranteed listing or proof of mainnet mFRG supply.
