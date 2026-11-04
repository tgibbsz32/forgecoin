# ForgeCoin Android — candidate UI, NOT a public miner or wallet

The project includes the updated dark navy/cyan Android UI matching the ForgeCoin website with branding, read-only browser links to the pool dashboard, pool observer and verified ForgeCoin mainnet-status page (rather than an unapproved raw-IP explorer), and disabled controls for native wallet creation/restoration, transfers, RandomX solo/pool mining, and Solana/mFRG.

**Not ready for release.** The only previously available Android native executable was a legacy ARM64 daemon from the retired P2P validation project, and is deliberately NOT shipped in the source tree or final preview APK. The current MainActivity intentionally disables node startup and all financial/mining operations. NodeService is legacy source retained for future porting, not authorized to run. No real new-mainnet wallet, RandomX miner or block acceptance has been verified.

## Verified local build
On the authorized Windows development machine, a debug UI APK successfully compiled using Gradle 8.11.1/Android Gradle Plugin 8.9.2, JBR, Android SDK 35. The candidate APK was placed in the user's Downloads folder, named `ForgeCoin-Android-UI-Preview-20261027.apk`. This is NOT a distributable mainnet miner or a final signed release. No Android device was connected via ADB for runtime tests.

## November 2, 2026: rebuilt isolated UI preview (not a miner)

After recovering local disk space, `apps/android` was rebuilt in a clean, detached-at-main D: QA worktree using cached Gradle **8.11.1**, Android Gradle Plugin **8.9.2**, Android SDK **35**, and Android Studio JDK **21**. The offline `:app:assembleDebug` build passed (36 Gradle tasks; no native daemon). The resulting **local-only** `app/build/outputs/apk/debug/app-debug.apk` was **3,601,422 bytes**, SHA-256 `9672dc4b70310c1e795dc3a10a218dcfa0c14fc6472217eead5fd3b86e760bf3`. `aapt dump badging` confirmed debug application ID `org.forgecoin.p2ptest.isolatedqa`. The ZIP contains only ARM64 native support libraries `libforge_randomx.so` and `libforge_runtime_probe.so`, **not** the `libforged.so` daemon or native wallet software.

The source contains a fail-closed APK verifier at `tools/verify_android_preview_apk.py` and negative/positive tests at `tests/android/test_preview_release_guard.py`. A GitHub workflow builds and verifies the restricted debug preview **without uploading an artifact or publishing to Releases**. Its result must be checked independently; a local build alone does not establish CI or Android device compatibility. No ADB device was connected. A manifest `extractNativeLibs` deprecation warning and Java 8 source/target deprecation warning remain cleanup items.

This preview intentionally does **not** create/restore an FRG wallet, transfer coins, mine, start an approved daemon, or connect to a public pool. P2P port `39480` is selected for future verified peers, while local RPC uses a private ephemeral loopback port. Public launch approval is unchanged.

## November 4, 2026: read-only mining safety diagnostics and build validation

A restricted Android GUI now displays **battery percentage and charging state,
Android thermal status (when API 29+ exposes it), power-saver state and logical
CPU count** as read-only diagnostics. This is groundwork for a future
temperature/battery-aware native RandomX worker, **not** the worker itself.
The solo and pool mining buttons, native FRG wallet creation/recovery, FRG
send/receive and payout functions remain disabled.

The connected Windows development computer compiled this branch using
JDK 21, Gradle 8.11.1, Android Gradle Plugin 8.9.2 and SDK 35.
`assembleDebug`, `testDebugUnitTest` and six offline Android preview
source/negative security checks passed. After removing the deprecated
`android:extractNativeLibs` manifest override and targeting Java 17, the
restricted preview verifier passed against a **3,629,747-byte** debug APK,
SHA-256 `24ae102b12a003671f8345d2f68fa7fe4481ec943ca4e246333a2ddad7ae97e3`,
application ID `org.forgecoin.p2ptest.isolatedqa` (debug signed, not a release).
Only `libforge_randomx.so` and `libforge_runtime_probe.so` are bundled;
**no native FRG daemon, wallet RPC, funded wallet or usable mining executable**.
The general MainActivity deprecated-API note still requires review. ADB found
**no connected physical handset**. None of this is verified on a real ARM64
device and no production APK or public download has been approved.

## November 4, 2026 — offline RandomX ARM64 self-test

The restricted DEBUG UI now offers **Verify one RandomX hash** on the Mining
screen. It runs the existing vendored native ARM64 RandomX light VM on a
background thread **exactly once** using the public RandomX test vector:
`test key 000` and `This is a test`. It compares the 32-byte output to the
upstream known-answer digest. This is NOT a miner: no nonce search, Stratum,
wallet, daemon, network, block submission, repeating hash loop or public FRG.

The one-hash button requires explicit confirmation and is blocked in release
builds, on battery saver, moderate-or-higher temperature, less than 20% battery
while unplugged, unreliable sensor state, or less than 512 MiB free RAM.
The screen reports only PASS/FAIL and elapsed duration, not an invented
continuous mining hashrate. Solo/pool mining and FRG wallet send/restore
buttons remain disabled.

The connected Windows QA machine passed Gradle
`:app:assembleDebug :app:testDebugUnitTest`, **23 JVM tests** (including
four new RandomX vector/negative tests), and eight Android release/security
source checks. The restricted debug APK was **3,634,999 bytes**, SHA-256
`f3fb70edf3c71ce887072d6059bb707ed74ea7bcb2185f3ec13e1c13f20bf224`,
with `org.forgecoin.p2ptest.isolatedqa`. It contains only ARM64
`libforge_randomx.so` and `libforge_runtime_probe.so`, with no native
FRG daemon, wallet or mining executable.

**A physical ARM64 Android device is still needed** to observe the actual
JNI known-answer test. Connected ADB devices were x86_64 emulators only.
Use disposable QA installations; do not import a funded wallet or expect
network mining or pool earnings.

## Remaining mandatory engineering gates
1. Port, compile and verify ARM64-v8a native ForgeCoin daemon, wallet APIs and RandomX mining component for the frozen 20261026 mainnet, with consensus and genesis checks against independent x64/ARM64 nodes. No old P2P daemon.
2. Implement native non-custodial wallet creation, wallet restoration from seed, encrypted seed storage using Android Keystore-backed keys, address display, synchronization, balance, safe send and restore tests. Avoid server custody and remote wallet RPC.
3. Implement bounded on-device mining controls (threads, thermal/charging safety, background limits, hash rate, accepted block receipt) and pool Stratum support with correct 1% fee/payout-accounting notices. Android foreground service behavior must satisfy current platform restrictions.
4. Validate explorer and pool URL/TLS routing and handle service unavailability without fabricating stats.
5. Add signed Android release builds, reproducible hashes, install/restore tests on actual arm64 phones, rejected block handling, stop/resume, permission and battery tests. Only after these tests and FRG launch authorization may operational controls be enabled.
6. Solana and mFRG controls remain visibly disabled until a separately approved future update.

Do not publish as a working public miner until all items above pass.
