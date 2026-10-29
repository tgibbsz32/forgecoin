# Android Private Encrypted Vault Storage — 2026-10-29

Completed Android emulator Keystore instrumentation test from previous PR #172: Gradle `:app:connectedDebugAndroidTest` completed BUILD SUCCESSFUL with one Keystore AES-GCM round-trip and tamper-rejection test on CityTest_API_36 emulator. This verifies emulator behavior only, not physical ARM64 devices, hardware-backed key assurance or new-device recovery.

This phase adds `SolanaVaultFiles` for encrypted-envelope-only writes within `Context.getNoBackupFilesDir()`, a no-overwrite wallet-name policy, file descriptor sync and temporary-file rename, and an Android instrumentation test that saves, reads, decrypts, rejects duplicate creation and cleans up a disposable wallet record.

The helper is not yet connected to wallet UI. A file in no-backup storage is still device-bound; restoring on a new Android handset must derive the same wallet from its separately backed-up BIP39 phrase. Do not store the mnemonic as unencrypted text. Current save operation is designed for new files, not robust transactional migration or secure key rotation; review power-failure and symlink/path-race behavior before production custody.

Pending: full emulator result for this branch, native FRG 25-word wallet restore, Android BIP39 generation, create/restore screens, real ARM64 phone tests, Keystore lifecycle and device-screen-lock policy, independent security review, mainnet launch signoff.
