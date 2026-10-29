# ForgeCoin Desktop — In-Memory Solana Key Generation Core (2026-10-29)

## Completed
Added a development-only `SolanaVault.GenerateEncryptedKeypairInMemory` primitive. It draws a fresh 32-byte seed from the Windows/.NET cryptographic RNG, derives a valid Ed25519 keypair using libsodium, encrypts the 64-byte Solana keypair directly into the existing authenticated wallet-vault format, and clears intermediate byte arrays in `finally` blocks. It never deliberately writes a plaintext private-key file. Its empty mnemonic field is intentional: **it does not provide BIP39 recovery words and must not be presented as a finished owner wallet**.

Windows acceptance checks: two successive generated addresses differ; decrypted vault preserves the matching private/public pair; wrong vault password fails; no mnemonic is invented. GUI source compilation succeeds. These tests use disposable local keys and do not authorize real-value custody or release.

## Release blockers
The actual GUI Create Solana Wallet button is **unchanged** and still uses a temporary plaintext Solana CLI keypair. Do not wire this generator into user-facing creation until tested BIP39 entropy-to-mnemonic and mnemonic-to-keypair/address derivation (including Solana derivation conventions) have been specified and validated against independent known vectors; also implement backup/recovery on a clean device. Managed .NET strings and JSON can retain sensitive copies in memory despite zeroing byte arrays. The libsodium-26.dll native dependency must have pinned provenance, hash, license and safe release packaging plus independent cryptographic audit. The UI must distinguish FRG 25-word seeds from Solana BIP39 phrases.

## Next phase
Implement and validate a reproducible BIP39 mnemonic/derivation module using vetted libraries and offline vectors, remove the legacy plaintext CLI creation path only after end-to-end recovery equivalence, then test GUI create/restore and package under controlled release. No minting, token sale or Oracle mining activation.
