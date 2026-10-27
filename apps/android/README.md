# ForgeCoin Android QA (development preview only)

This is the first Android build harness, **not the final native FRG wallet/miner**.

- Java Android app; Android API 26+; no external dependencies.
- Same 20261026 FRG identity as Windows and Oracle, with read-only HTTPS monitoring of the exact genesis and launch flags.
- Wallet, recovery, solo mining, pool mining, payout settings, Solana mFRG are visibly disabled. The app has no wallet keys, no recovery words, no wallet balance, no Android mining service, no RandomX miner, and no Stratum connection.
- Native FRG wallet/daemon integration, ARM64 JNI, encrypted wallet backup/restore, foreground background-safe mining service, CPU resource limits, thermal throttling, worker authentication, and actual mobile mining tests remain outstanding.
- Do not publish this QA preview as an operational wallet/miner. Source and APK must remain clearly labeled QA until all features and security tests pass.
- Network access in app code is HTTPS to the Oracle read-only monitor; the block explorer opens in the system browser. No private keys are created or transmitted.

## Build

Requires Android SDK platform android-36.1, build tools 36.1.0, and JDK from Android Studio installed at the build script's expected paths. No Gradle, additional downloads or privileged installation needed.

Run the build.ps1 script from PowerShell.

It uses AAPT, Java compiler, D8, zipalign and Android debug signing. The script refuses to overwrite an existing APK. Debug keystore is stored outside Git at %USERPROFILE%\.android\debug.keystore. Never use a debug key or this QA package ID for a production wallet release.

**Emulator verified 2026-10-27:** Installed the debug-signed APK on the Android API 36.1 emulator, launched `org.forgecoin.mobile.qa/.MainActivity`, confirmed read-only HTTPS Oracle request responded with expected HTTP 503 while offline, and checked via UI automation that all native FRG wallet controls are disabled. No AndroidRuntime crash was reported. The emulator was stopped afterward. A **physical Android handset**, wallet keys, RandomX mining and background service remain untested/unimplemented. Install on a USB device manually with `adb install -r PATH_TO_QA_APK` only for preview QA.

Built QA APK SHA256: FD8732AD6046971F307FC0ECDBFC24B664AAAC5C2F7EF082664529366DCA14DD. Never promote this debug-signed build to a public wallet/miner release.
