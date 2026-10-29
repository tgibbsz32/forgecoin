# Android wallet vault device QA gate — 2026-10-29

The app manifest already sets android:allowBackup="false". This change adds an AndroidJUnit4 instrumented Keystore round-trip and authentication-tag tampering test using a disposable plaintext value, not a real seed. These tests must run **on an Android emulator/device**; a successful APK compilation alone does not prove that AndroidKeyStore can create and persist keys on target devices.

Next release gates: execute connectedAndroidTest on an authorized Android device, verify app process restart and clean-reinstall behavior, isolate encrypted wallet data from system backup and logs, establish authenticated user access policy, ensure recovery phrase re-derives exact public address on another device, and complete Android native FRG and Solana wallet UI acceptance. Do not enable wallet/mining controls, mint token or launch mainnet.
