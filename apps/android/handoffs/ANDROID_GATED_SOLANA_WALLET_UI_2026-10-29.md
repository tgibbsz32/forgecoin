# ForgeCoin Android — gated Solana wallet create/restore interface handoff (2026-10-29)

## Implemented
- Separated Solana mnemonic generation from encrypted wallet persistence: `SolanaWalletLifecycle.create()` now returns an uncommitted candidate phrase/address and does **not** create any wallet file.
- Added debug-only `SolanaWalletDebugFlow` backed by `BuildConfig.DEBUG` with a create button that displays BIP39 words, requires confirmation via words 4 and 9, and only then persists an encrypted Keystore-backed private app file. A debug-only restore dialog validates a phrase and creates a new encrypted record. Existing mFRG transfers, native FRG wallets and mining remain disabled.
- Updated emulator tests to assert that a newly generated candidate has no stored vault until the explicit restore/commit operation is called.
- Device: connected Windows PC / Android API 36 emulator. Gradle `:app:testDebugUnitTest :app:assembleDebug :app:connectedDebugAndroidTest` BUILD SUCCESSFUL; 3 connected tests completed.

## Strict status / release blockers
This is an **experimental DEBUG UI**, not production custody. There has been no automated UI interaction test of the confirmation dialogs, no physical Android test, screen-lock biometric/key authentication, recovery across a clean-install second phone, secure memory review, signed release, live Solana signing/send, native FRG ARM64 wallet/RandomX acceptance, or independent security audit. The debug UI is visible in debug builds: testers must never fund preview wallets. A release build hides these controls via `BuildConfig.DEBUG`.

The creation lifecycle still models a test-only wallet/address and currently stores mnemonic material encrypted by the device-bound Android Keystore. Device destruction or app deletion requires recovery from separately written mnemonic backup. Do not claim app readiness for storing treasury or mint authority. Before productizing, make explicit supported derivation convention and mnemonic passphrase policy, robust process-death/cancel handling and user authentication on decryption, and separately validate native 25-word FRG recovery.

No production keys created, no FRG mining launched, no mFRG issued, and no public sale authorized.
