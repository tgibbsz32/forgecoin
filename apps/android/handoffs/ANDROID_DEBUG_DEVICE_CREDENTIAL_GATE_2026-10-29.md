# Android debug wallet device authentication — 2026-10-29

Added an Android API 30+ BiometricPrompt requiring BIOMETRIC_STRONG or DEVICE_CREDENTIAL before the debug-only Solana Create/Restore dialogs. Devices without a configured secure lock, SDK <30, or non-debug builds fail closed. The original private encrypted vault key is still **not bound** to user authentication; this is a UI entry gate and MUST NOT be represented as a production vault security guarantee. The helper is not invoked for automatic addressFromStored calls.

Windows connected desktop: `:app:testDebugUnitTest :app:assembleDebug` BUILD SUCCESSFUL, 37 Gradle tasks. No interactive biometric or credential UI test was performed on Samsung, and no new on-phone instrumentation test for this feature was run. The debug APK remains experimental and should not hold funds.

Next: bind a new versioned Keystore key to per-use user authentication, require confirmation for decrypt, migrate disposable encrypted records safely, add physical-phone allow/cancel/failure instrumented UI scenarios and separate native FRG wallet/RandomX consensus integration. Independent security review and release authorization remain outstanding.