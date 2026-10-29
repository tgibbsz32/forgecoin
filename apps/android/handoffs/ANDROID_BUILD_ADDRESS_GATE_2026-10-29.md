# Android debug build recovery and Solana Base58 address gate — 2026-10-29

## Completed
Repaired source-tree corruption that was preventing any Android Gradle build: removed stray execution-status lines from root settings/build/properties, app Gradle, AndroidManifest, MainActivity and NodeService. Added the missing network-security config with cleartext traffic disabled. Used existing Windows Android Studio JBR, SDK 35 and cached Gradle 8.11.1 to run `gradle :app:assembleDebug :app:testDebugUnitTest`: **BUILD SUCCESSFUL** after fixes. Repeated this with the new address tests: **BUILD SUCCESSFUL**.

Added a Solana 32-byte-public-key Base58 encoder, tests for canonical zero/one encodings and invalid key length, and an explicit fail-closed seed-to-Ed25519-public address gate.

## Important limitation
The app **does not yet derive a Solana public key from a seed**. `SolanaEd25519Public.addressFromSeed` deliberately throws until a vetted Android-compatible Ed25519 implementation is integrated and cross-checked against the desktop key vectors. Base58 encoding alone does not establish phrase-to-address parity. Do not enable wallet creation, import, sending, or balance operations. Existing Android Keystore vault remains untested on physical device/emulator; debug APK is not a releasable miner and includes no validated native FRG RandomX runtime.

## Next major phase
Integrate vetted Ed25519 public derivation (with deterministic cross-platform vector), compose validated phrase -> seed -> public key -> Base58 address, then instrument Android Keystore AES-GCM vault and tamper/recovery tests. Test on actual ARM64 phone or emulator. Native FRG create/restore, solo/pool mining and official chain consensus remain separate blockers.

No owner wallet, mFRG token issuance, funds or public Oracle launch occurred.
