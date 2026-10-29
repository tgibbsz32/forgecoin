# Android Solana wallet creation and recovery lifecycle — 2026-10-29

## Completed and verified
- `SolanaMnemonicGenerate`: 12-word BIP39 English phrases from 128 bits of OS cryptographically secure randomness, with SHA-256 checksum, canonical bundled BIP39 list.
- `SolanaWalletLifecycle`: standalone offline wallet creation and phrase restoration using existing BIP39 checksum validation, hardened Ed25519 Solana address generation, Keystore AES-GCM encryption and encrypted local no-backup file storage; the empty BIP39 passphrase and explicit m/44'/501'/0'/0' derivation convention remain fixed.
- Disposable instrumented emulator acceptance verifies new 12-word phrase, encrypted file save/read, restored phrase creating the same Solana address and invalid-checksum rejection.
- On the Windows development computer's Android API 36 emulator, Gradle `:app:testDebugUnitTest :app:assembleDebug :app:connectedDebugAndroidTest` **BUILD SUCCESSFUL**, with 3 connected device tests completed.

## Release gates
This milestone is an offline Android **wallet lifecycle core**, NOT a production wallet UI. The MainActivity remains intentionally disabled for Solana and native FRG financial controls. Implement a recovery-phrase confirmation flow, password/biometric or device-unlock policy, user-visible derivation path, restored-address review and screen-capture controls before enabling them. The prototype stores an encrypted mnemonic under a Keystore key with no user authentication requirement; screen-unlocked device compromise and in-memory Java strings remain concerns. Verify native FRG 25-word wallet separately, real ARM64 device and reinstall/cross-device restore, Solana signing and receive/send, independent crypto audit, library provenance and recovery compatibility.

No real key or seed was used. No production mint authority wallets, token issuance or Oracle mining activation.
