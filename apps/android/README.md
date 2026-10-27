# ForgeCoin Android — candidate UI, NOT a public miner or wallet

The project includes the updated dark navy/cyan Android UI matching the ForgeCoin website with branding, read-only browser links to the pool dashboard, pool observer and staged block explorer, and disabled controls for native wallet creation/restoration, transfers, RandomX solo/pool mining, and Solana/mFRG.

**Not ready for release.** The only previously available Android native executable was a legacy ARM64 daemon from the retired P2P validation project, and is deliberately NOT shipped in the source tree or final preview APK. The current MainActivity intentionally disables node startup and all financial/mining operations. NodeService is legacy source retained for future porting, not authorized to run. No real new-mainnet wallet, RandomX miner or block acceptance has been verified.

## Verified local build
On the authorized Windows development machine, a debug UI APK successfully compiled using Gradle 8.11.1/Android Gradle Plugin 8.9.2, JBR, Android SDK 35. The candidate APK was placed in the user's Downloads folder, named `ForgeCoin-Android-UI-Preview-20261027.apk`. This is NOT a distributable mainnet miner or a final signed release. No Android device was connected via ADB for runtime tests.

## Remaining mandatory engineering gates
1. Port, compile and verify ARM64-v8a native ForgeCoin daemon, wallet APIs and RandomX mining component for the frozen 20261026 mainnet, with consensus and genesis checks against independent x64/ARM64 nodes. No old P2P daemon.
2. Implement native non-custodial wallet creation, wallet restoration from seed, encrypted seed storage using Android Keystore-backed keys, address display, synchronization, balance, safe send and restore tests. Avoid server custody and remote wallet RPC.
3. Implement bounded on-device mining controls (threads, thermal/charging safety, background limits, hash rate, accepted block receipt) and pool Stratum support with correct 1% fee/payout-accounting notices. Android foreground service behavior must satisfy current platform restrictions.
4. Validate explorer and pool URL/TLS routing and handle service unavailability without fabricating stats.
5. Add signed Android release builds, reproducible hashes, install/restore tests on actual arm64 phones, rejected block handling, stop/resume, permission and battery tests. Only after these tests and FRG launch authorization may operational controls be enabled.
6. Solana and mFRG controls remain visibly disabled until a separately approved future update.

Do not publish as a working public miner until all items above pass.
