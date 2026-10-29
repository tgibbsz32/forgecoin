# Android BIP39 validated recovery core — Handoff 2026-10-29

Implemented a bundled canonical English BIP39 wordlist, offline word membership and checksum validation, and a composite `SolanaRecoveryCore` that only performs hardened Ed25519 SLIP-0010 seed derivation after a valid BIP39 phrase is supplied. The derivation uses the previously implemented m/44'/501'/account'/0' path and an explicit empty BIP39 passphrase.

**Windows validation:** Android Studio Java compiler successfully built the standalone Java components and both no-Android-dependency smoke tests passed: official `abandon` x11 + `about` checksum, rejection of the mutated phrase, and validated mnemonic -> SLIP-0010 output equal to independently tested direct derivation. The Android APK, instrumented tests and Keystore AES-GCM code were not rebuilt or exercised in this phase. Native FRG wallet/mining and Android financial controls remain disabled.

**Next phase:** Implement and cross-check Ed25519 public address generation and Solana base58 address display, implement user-facing 12/24-word recovery in Android, test mnemonic roundtrip on a device, Android Keystore tamper and backup behavior, and full APK build/signing. Enforce no private seed/phrase in logs or Android backups. Desktop FRG 25-word seeds and Solana BIP39 recovery must remain separate; no mainnet authorization or public token sale.
