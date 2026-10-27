# ForgeCoin Desktop — Solana wallet and mFRG balance support

**Status: functional development prototype; NOT independently audited or packaged as a public release.** The native FRG mainnet and pool mining launch gates remain frozen. This is separate Solana wallet functionality, not an extension of native FRG signing.

## Implemented in the unreleased C# WinForms development worktree

- New Solana / mFRG tab in Program.cs, SolanaWallet.cs and SolanaVault.cs.
- Create local Solana wallet with a reviewable official Solana CLI (solana-keygen.exe), extract a 12-word BIP39 recovery phrase, save a new password-encrypted vault without overwriting an existing wallet.
- Open an existing encrypted vault using its password; lock UI state, copy the public receiving address; import a separate Solana CLI JSON keypair and store it encrypted in a local vault; export and reimport an encrypted backup; reveal the stored mnemonic only after password re-entry and a disclosure warning.
- Encryption format: PBKDF2-HMAC-SHA256 at 300,000 iterations, separate AES-256-CBC and HMAC-SHA256 keys, random 32-byte salt/16-byte IV and encrypt-then-MAC integrity, with key-material handling limitations of managed strings. Backup format named forgecoin-solana-aes256-hmac-v1; password minimum 12 characters. This is not a substitute for audited custody software.
- Display account SOL balance in 9-decimal units on Solana mainnet or devnet; query account-owned SPL token accounts using the exact configured mint; sum raw token amounts as decimals. The only existing mFRG mint is on **devnet**, with zero issued supply as of October 27. On mainnet, display explicitly "Not issued on mainnet" until a newly verified production mint config exists.
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

## miniFORGE issuance

The target is **50 million standard SPL mFRG**, 6 decimals: 5m future sale/trading, 5m future liquidity, 40m later distribution. The Solana **mainnet mint does not exist yet**; the currently configured signer has 0 mainnet SOL. A recommended funding budget is 0.1 mainnet SOL, sufficient margin over the quoted ~0.00553212 SOL minimal rent for one mint and three token accounts, excluding metadata and fees. See docs/MINIFORGE_SPL_TREASURIES.md.

Never commit/export a real wallet JSON, mnemonic, vault backup, account password or RPC credential to a public repository or issue a public release solely on the strength of these QA results.
