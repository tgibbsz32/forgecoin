# Samsung ARM64 isolated QA — 2026-10-29

Connected target: Samsung SM-S931U, Android 17 (API 37), arm64-v8a. Device ADB serial targeted explicitly by ANDROID_SERIAL. Existing installed ForgeCoin package previously caused INSTALL_FAILED_UPDATE_INCOMPATIBLE because its APK signature differed from the current Gradle debug signature. This change gives **debug builds only** an applicationIdSuffix `.isolatedqa` to avoid replacing the original package.

Verified on Samsung: Gradle `:app:testDebugUnitTest :app:assembleDebug :app:connectedDebugAndroidTest` BUILD SUCCESSFUL, and **three Android instrumentation tests completed**. These are tests for AES-GCM Android Keystore authenticated encryption/tamper rejection, private encrypted file lifecycle, and 12-word Solana test wallet creation/recovery. No real wallet, transaction, native FRG signing, native RandomX mining or mainnet activation was exercised.

Caveat: After Gradle instrumentation finished, `pm list packages | Select-String forgecoin` on the phone returned no package entries, despite Gradle tests completing successfully. Test frameworks may remove installed test packages, and the existing app's install state should be checked on the device before any further user-facing claim. No manual uninstall commands were issued. Treat preservation as *configuration intent*, not separately confirmed after the test run.

Remaining blockers: Native FRG 25-word wallet creation/recovery and transaction signing, ARM64 RandomX solo/pool acceptance, device-authentication gate, UI automation, independent security review and signed release QA. Preview must not be funded.
