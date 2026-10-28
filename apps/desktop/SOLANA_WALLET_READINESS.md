# ForgeCoin Desktop — Solana wallet and mFRG balance support

**Status: functional development prototype; NOT independently audited or packaged as a public release.** The native FRG mainnet and pool mining launch gates remain frozen. This is separate Solana wallet functionality, not an extension of native FRG signing.

## Implemented in the unreleased C# WinForms development worktree

- New Solana / mFRG tab in Program.cs, SolanaWallet.cs and SolanaVault.cs.
- Create local Solana wallet with a reviewable official Solana CLI (solana-keygen.exe), extract a 12-word BIP39 recovery phrase, save a new password-encrypted vault without overwriting an existing wallet.
- Open an existing encrypted vault using its password; lock UI state, copy the public receiving address; import a separate Solana CLI JSON keypair and store it encrypted in a local vault; export and reimport an encrypted backup; reveal the stored mnemonic only after password re-entry and a disclosure warning.
- Encryption format: PBKDF2-HMAC-SHA256 at 300,000 iterations, separate AES-256-CBC and HMAC-SHA256 keys, random 32-byte salt/16-byte IV and encrypt-then-MAC integrity, with key-material handling limitations of managed strings. Backup format named forgecoin-solana-aes256-hmac-v1; password minimum 12 characters. This is not a substitute for audited custody software.
- Display account SOL balance in 9-decimal units on Solana mainnet or devnet; query account-owned SPL token accounts using the exact configured mint; sum raw token amounts as decimals. The project has a documented **devnet** test mint (with zero issued supply in the October 27 preflight). A Solana **mainnet** mFRG mint and authority state have not been independently verified in this repository. The application displays **"Mainnet mint unconfigured"** until a separately verified production mint config exists; this does **not** assert no mainnet token exists.
- Use read-only Solana JSON-RPC for balances; private keypair/seed remain local, never uploaded to RPC. No Solana token transaction signing or swaps are currently implemented.

## Release blockers and security review

1. **Temporary local plaintext keypair:** Solana CLI keygen writes a temporary private keypair JSON before vault encryption, then deletes it. A process crash, antivirus scan, filesystem snapshot, memory forensic recovery or unexpected CLI behavior may expose it. The 16-check QA run confirms ordinary-path deletion but not power-loss-safe cleanup or forensic erasure. A reviewed in-process Ed25519/BIP39 implementation or secure OS-keystore-backed creation path is preferable for release.
2. **CLI distribution and provenance:** Official Solana CLI must be installed locally; current installer does not bundle a pinned, reviewed solana-keygen.exe or its dependencies. Do not download or run arbitrary keygen executables. A prelaunch package without a trusted CLI cannot claim turnkey wallet creation.
3. **Mnemonic compatibility:** Solana keygen creates its own BIP39 words/derivation settings. Never claim that every third-party Solana wallet uses identical derivation paths. Importing existing 64-byte CLI keypair JSON cannot reconstruct its original seed phrase. An offline recovery rehearsal with the official CLI is still needed for exact mnemonic/address parity.
4. **Imported keypair verification:** JSON validates 64 signed-byte values and embedded public key address; independent Ed25519 public key derivation from seed should be validated before a public release.
5. **Backend/rpc security:** Fail closed on RPC errors and wrong network; review endpoint TLS, response limits, rate limits, compromised RPC server data, mint identity/decimal checks, token ownership, stale cache, symbol spoofing, UX accuracy and error states. The desktop does not display fake mFRG mainnet balances.
6. **Independent crypto/custody audit:** Require adversarial vault tests, brute-force/memory-security review, backup cross-version vectors, secure ownership/rotation tests, seed-display shoulder-surfing controls and restore from backup on a second computer.
7. **Native FRG:** Windows miner/daemon and wallet release packaging must still pass canonical genesis unspendability checks, consensus builds across supported platforms, Block 1 launch authorization, native PoW acceptance/maturity, official pool end-to-end shares/payouts, and wallet release verification. The current mainnet release configuration remains release_authorized false and mined_blocks_permitted_before_launch 0.

## Test evidence

October 27: 16/16 actual WinForms + encrypted-vault smoke checks passed for creation, address parity, wrong password, integrity rejection, encrypted restore, lock/reopen, mainnet placeholder and temporary-file removal. Evidence is local outputs/41-solana-vault-gui-smoke.txt. A passing smoke test does not certify wallet custody security.

## miniFORGE 500M intended issuance — planning only (October 28, 2026)

The current approved **project tokenomics plan**, which is not proof of on-chain issuance, is **500,000,000 mFRG**, standard SPL Token, 6 decimals. The nine allocations are:

| Allocation | Tokens | Share |
| --- | ---: | ---: |
| Crypto-denominated fundraising (5M pilot, 15M remainder year 1, 20M years 2–3, 10M years 4–10) | 50,000,000 | 10% |
| Operations and development | 100,000,000 | 20% |
| Ecosystem adoption and grants | 100,000,000 | 20% |
| Finite staking/participation rewards | 85,000,000 | 17% |
| Liquidity | 60,000,000 | 12% |
| Engineering/security | 65,000,000 | 13% |
| **Founder immediately unlocked** | **15,000,000** | **3%** |
| **Team-labeled allocation beneficially owned by founder; monthly vesting in months 13–36** | **15,000,000** | **3%** |
| Emergency | 10,000,000 | 2% |
| **Total** | **500,000,000** | **100%** |

**Both 3% buckets belong beneficially to the founder** (30M total, 6%). The deferred allocation is **625,000 mFRG per month for 24 months**. Do not describe it as independent team ownership.

The **non-transactional planning file** `config/miniFORGE.mainnet.plan.json` uses schema version 2 with 9 buckets, a 500M target and 6-decimal atomic integer accounting. All mint, sale, distribution, liquidity and staking permissions are **false** and all proposed account addresses are **null**. The existing app **does not use that file to decide which mainnet mint to display**: the display logic reads a different file, `config/miniFORGE.mainnet.json`, and requires a verified mainnet mint, `network = mainnet-beta`, and `productionReady = true`. Do not invent or ship this production file before verification. The devnet mint can never be substituted on mainnet.

Earlier October 27 CLI preflight noted a test fee payer with 0 SOL; the balance is **historical, not a current on-chain observation**. No mainnet SPL supply, authority ownership or account funding was independently established in this document.

Before production issuance, independently verify any existing mainnet mint, total supply, mint/freeze authorities, token program, token metadata, signer controls and final vesting plans. If a mint's authority was revoked below the intended 500M, increasing supply on that mint is impossible and requires an explicitly disclosed migration instead. Do not automatically create a new mint or transfer funds from a planning update.

The related **checkout prototype PR #122** was drafted for old 5M inventory and a USDC-only payment flow, and **must be audited and reconciled separately** before its logic can be merged into any distribution backend. Cryptocurrency swaps can still create securities, tax, money-transmission and sanctions obligations; the public sale remains disabled.

See [canonical tokenomics](../../docs/MFRG_LIFETIME_TOKENOMICS_500M.md), [technical sale gates](../../docs/MINIFORGE_SALE_MECHANISM.md), and [native FRG release state](../../docs/CURRENT_MAINNET.md).
