# Android FRG and Solana/mFRG wallet implementation status — 2026-10-29

The user requires **the same two wallet systems as ForgeCoin Windows desktop**: native privacy FRG wallets using their own 25-word seed and a separate Solana/mFRG BIP39 wallet with encrypted, local software custody. Wallet creation, seed recovery, and secure local storage must work in the Android app, not require Phantom/Solflare or a hardware wallet.

## This change
Adds a small Android-compatible Java, **offline-only** BIP39 PBKDF2-HMAC-SHA512 2,048-round mnemonic-to-seed primitive and tests using the official BIP39 vector with the passphrase `TREZOR`. Uses UTF-8/NFKD to align with the Windows implementation. This does **not** validate BIP39 word lists/checksums, derive SLIP-0010 keys, produce an address, generate mnemonic words, store any seed or enable the currently disabled Android wallet UI.

## Remaining product gates
1. Integrate canonical checked-in BIP39 wordlist and checksum validation with wordlist integrity.
2. Implement standard hardened Ed25519 SLIP-0010 path m/44'/501'/0'/0', cross-check with independently known Solana vectors and Windows output. Document Solana CLI derivation alternatives explicitly.
3. Android Keystore-backed **authenticated encryption**, with device-lock and backup/recovery rules, for separate FRG and Solana accounts. Do not store raw seeds in SharedPreferences, logs or Android auto-backups. Keystore keys can be device-bound; mnemonic backup must allow recovery on a new device.
4. Complete create/restore UI, encrypted vault migration and clean-install Android-device tests. Ensure Solana recovery phrase is 12/24-word BIP39 and FRG native phrase remains 25 words.
5. Implement native ARM64 FRG wallet/RandomX and test solo/pool acceptance. None of the native wallet/mining or Solana financial operations are enabled.
6. Dependency audit, production signing, release QA, security review, explicit separate authorization before public mining or mFRG mint/sale.

The existing Android debug APK remains a restricted UI preview. No production wallet secrets, funds, keys, mint or public network activation in this change.
