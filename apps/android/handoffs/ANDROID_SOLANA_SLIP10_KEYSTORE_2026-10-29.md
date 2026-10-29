# ForgeCoin Android — Solana SLIP-0010 and Keystore vault handoff (2026-10-29)

## Implemented
- Offline hardened Ed25519 SLIP-0010 private-seed derivation from BIP39 seed, path m/44'/501'/account'/0'. Mirrors the separate Windows desktop derivation helper.
- Android Keystore AES-256-GCM authenticated encryption helper with a versioned envelope, random IV provided by cipher initialization, and strict envelope-size checks. Stores no wallet data automatically and sends nothing to network.
- JUnit test source and a standalone Java test for deterministic address-seed derivation and account isolation.
- On the connected Windows developer PC: compiled the Java BIP39 + SLIP10 classes with Android Studio JBR and ran standalone known-vector test; `ANDROID_SLIP10_REFERENCE_VECTOR_OK`. The expected 32-byte derived seed hex is `37df573b3ac4ad5b522e064e25b63ea16bcbe79d449e81a0268d1047948bb445`, independently computed via Python standard-library HMAC/PBKDF2.

## Crucial limitations
The Android Keystore helper has **not been compiled against Android SDK or tested on an Android device/emulator** yet, so treat it as unverified prototype. Keystore keys are device-bound and cannot reconstruct a wallet on another phone: users need their separately verified Solana BIP39 recovery phrase. Never treat Android's encrypted device file as portable recovery, and disable auto backup for private wallet files. The code currently has no wallet-creation UI integration, no wordlist validation/generation, no Ed25519 signing, no cross-platform vault migration, no actual wallet persistence policy, no hardware-backed key attestation or app-lock, and no native FRG wallet/RandomX release acceptance.

Next major phase: integrate Android BIP39 wordlist/checksum, Ed25519 public derivation and exact address parity; add Android instrumented Keystore roundtrip/tamper tests and OS-backed private-file storage, then create/restore UI and cross-device mnemonic recovery acceptance. Native FRG and Solana/mFRG must remain separate mnemonic standards. All financial/mining buttons remain disabled.

## Owner-facing status
No owner wallet/seed should be generated yet. No mFRG mint, sale, transfer or public Oracle mining authorized.
