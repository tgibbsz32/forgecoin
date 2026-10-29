# ForgeCoin Android Ed25519 provider migration — 2026-10-29

## Delivered
Replaced custom BigInteger Ed25519 scalar multiplication in SolanaPublicAddress.java with Bouncy Castle Ed25519PrivateKeyParameters.generatePublicKey(). Pinned org.bouncycastle:bcprov-jdk18on:1.78.1 in Android Gradle dependencies. Retained standalone Base58 encoding for public bytes (no secret scalar arithmetic).

## Verified Windows build
Remote Desktop Commander on TREYS_DELL_RTX: Gradle 8.11.1 via existing cache, Android SDK under LOCALAPPDATA/Android/Sdk, Android Studio JBR, offline Gradle commands `:app:testDebugUnitTest :app:assembleDebug` completed BUILD SUCCESSFUL (36 tasks). This verifies compilation, existing unit tests, and a debug APK artifact. It is NOT an Android device test and no Android Keystore encryption/decryption test or Android app UI acceptance took place. Existing derived address vector test in standalone Java smoke is not automatically part of JUnit Gradle suite and should be added there.

## Remaining blockers
The cryptographic dependency must receive provenance and implementation review before production custody. Verify Solana path/account parity in an independent Android unit test; add Keystore AES-GCM instrumentation tests for round-trip, tamper rejection, and device-bound recovery limitations. Add local secure persistence with Android auto-backup exclusions; implement BIP39 word generation and UI create/restore; exercise recovery on a fresh Android device. Native ARM64 FRG wallet and RandomX mining remain incomplete. Production wallets, mFRG mint and Oracle public activation are NOT authorized.

## Note
Android debug APK is development-only and not published or signed for release.
