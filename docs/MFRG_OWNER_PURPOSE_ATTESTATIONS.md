# mFRG owner-to-purpose cryptographic consent checks — Step 13

**2026-10-28. Non-transactional, offline only. No mainnet mint, treasury or beneficial owner independently authenticated.**

## Scope

The new [offline Ed25519 verification tool](../tools/verify_mfrg_purpose_attestations.cjs) checks an owner-signed, domain-separated consent message against the public key identified as the owner of an SPL token account in a separately saved, untrusted RPC inventory. It uses built-in Node.js cryptography, requires no private keys, makes no network calls, and cannot mint, transfer, sell or release tokens.

A correct signature demonstrates that the *private key for the claimed token owner public key* signed a message assigning a proposed allocation purpose. It **does not** demonstrate the human's identity, legal beneficial ownership, authentic on-chain account ownership, complete inventory, an existing mint, multisig/PDA governance, funded treasury or permission to execute a transaction.

The [template manifest](mfrg-owner-attestation.template.json) intentionally has a null mint and no claims. It cannot pass validation until the genuine owner's Solana mainnet mint and public account records have been independently authenticated.

## Exact message to sign

All fields are UTF-8 text with one newline between fields and an additional newline at the end. The exact order is: 

1. Domain string: FORGECOIN_MFRG_TREASURY_PURPOSE_ATTESTATION_V1
2. Literal network: mainnet-beta
3. Authentic mainnet mint public key
4. One of the nine approved allocation identifiers
5. Token account public key
6. Observed token-owner authority public key
7. Exact unsigned decimal token account balance in six-decimal atomic units
8. Unique 16–32 byte random nonce, lower-case hexadecimal
9. Issued time in YYYY-MM-DDTHH:MM:SSZ format
10. Expiry time in the same format (within 30 days)

Sign this exact newline-terminated string through the owner's trusted direct Ed25519 wallet message-signing capability; encode the 64-byte detached signature as standard base64 in the claim's signature_base64 field. Do **not** submit private keys, mnemonic phrases or wallet backups to any service. The verifier only accepts direct Ed25519 account-owner signatures; program-controlled PDAs and multisig controllers require separately verified governance and cannot be proven with a simple wallet signature.

Each claim in the manifest includes purpose, token_account, token_owner, amount_atomic, nonce, issued_utc, expires_utc and signature_base64. Other outer fields are schema=mfrg-purpose-attestations-v1, network=mainnet-beta and mint=(actual public key).

## Inputs and CLI

Use a genuine, saved SPL getProgramAccounts response with context and parsed account data, obtained as described in [Step 12](MFRG_TOKEN_ACCOUNT_INVENTORY.md). After separately authenticating mainnet provenance and mint identity, run:

    node tools/verify_mfrg_purpose_attestations.cjs --manifest ./local-signed-purpose-claims.json --inventory-json ./local-accounts.json --as-of-utc 2026-10-28T00:00:00Z

The snapshot itself remains **untrusted**. The code rejects invalid signatures, wrong mint/account/role/amount, excess purpose budget, duplicate accounts, expired claims, frozen token accounts and delegated or close-authority-controlled accounts. It always returns false for RPC provenance authenticated, mint creation authenticated, beneficial ownership proven, multisig/PDA approval, treasury funding and sale or issuance authorization.

The only claim it can positively report is an offline Ed25519 signature match for a specific proposed budget purpose and a *provided* parsed account-owner key. Even a passing response must not be labeled as a verified treasury account.

## Tokenomics and custody boundaries

Intended mFRG fixed lifetime supply: **500 million**, not observed issuance. Nine budgets: 50M fundraising (only 5M proposed initial pilot), 100M operations, 100M ecosystem, 85M finite staking rewards, 60M liquidity, 65M engineering/security, 15M founder immediate, 15M team-labeled but beneficially owned by the **same founder** (625k monthly at ends of months 13–36), and 10M emergency. Both founder allocations total **30M (6%)**. Cryptographic consent does not prove any account has received its budget.

Production sale/quotes/payments/fulfillment, token issuance, vesting, staking, liquidity and FRG native chain changes remain **disabled and unperformed**. The required next evidence is an actual owner-authenticated mainnet mint creation record and independently corroborated token account inventory, followed by multisig/contract-specific authority validation, legal and security reviews.

For treasury SPL multisig structure and a fail-closed, non-approval PDA review workflow, see [Step 14 custody authority preflight](MFRG_MULTISIG_PDA_READINESS.md). Direct Ed25519 signature consent is not a substitute for multisig account inspection or audited program-derived controls.

## Tests

Run locally without any Solana credentials:

    node --test tools/test_verify_mfrg_purpose_attestations.cjs
    python3 tools/test_reconcile_mfrg_token_accounts.py
    python3 tools/test_mfrg_policy.py
    python3 tools/test_mfrg_treasury_vesting_preflight.py
