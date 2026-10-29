# Auth-bound vault host validation — 2026-10-29

Branch: security/android-auth-bound-vault-prep-20261029. Starting commit: 040213974ff008dac240e7771bba65d63b09fb84.

## Implemented

- Strict, bounded v2 Solana envelope with a separate format discriminator, canonical Base64, defensive copies, 12-byte IV and 128-bit GCM tag. The v2 header is GCM additional authenticated data. Legacy v1 files are not reinterpreted or migrated.
- Existing v2 key preparation now explicitly invalidates on biometric enrollment changes and refuses to create a replacement key during decryption. Missing/invalidated keys require mnemonic recovery; no automatic deletion or reset.
- Single-use pending encrypt/decrypt operations with exact Cipher identity checks and wiping of owned input buffers on completion, mismatch, cancellation or crypto failure. Caller owns and must clear original inputs and successful plaintext results. Java wiping cannot guarantee removal of all VM/provider copies.
- API 30+ platform BiometricPrompt adapter using strong biometrics and CryptoObject. Only success completes encryption/decryption; errors/cancellation discard the operation. Nonmatching biometrics remain retryable. CancellationSignal must be cancelled by a future UI owner when its lifecycle ends. No credential fallback or API 26–29 fallback.
- Offline FRG send-amount parsing with eight decimal places, matching src/cryptonote_config.h. Returns unsigned decimal atomic units without floating point or silent rounding; rejects zero, overflow, signs, whitespace and excess precision. This is transaction-input preparation, not native wallet/signing.
- RandomX argument validation is deterministic even when JNI is unavailable; missing native runtime has no substitute hash implementation. Native code remains a serialized per-call light VM, not a miner.

The adapter follows Android's auth-per-use CryptoObject contract:
https://developer.android.com/reference/android/hardware/biometrics/BiometricPrompt.CryptoObject

## Verification

Local Java/Gradle/Android SDK are accessible directly, bypassing the reported Remote Desktop Commander quota. No remote desktop calls, device installs, production app changes, wallet network calls or main branch updates were made.

- Gradle 8.11.1 `-p apps/android testDebugUnitTest`: PASS, 20 tests, zero failures/errors. Eight new tests cover envelope roundtrip/rejection/tampering, wrong key/AAD, consumed/cancelled/mismatched operations, exact FRG units/overflow and RandomX input/unavailable-runtime behavior. Software JCE is used for vault unit tests; this does not verify Android Keystore or biometric enforcement.
- Python `-m unittest discover -s apps/android/tools -p test_*.py`: PASS, one release-readiness regression test.
- `release_readiness.py --require-release`: BLOCKED, as expected. This is self-reported gating, not independent security verification.
- Gradle `-p apps/android assembleDebug assembleDebugAndroidTest`: PASS, including ARM64 NDK/CMake compilation and packaging of debug and instrumentation APKs. Instrumentation is compiled only; no device test execution is claimed. Existing Java 8 source/target, deprecated API and manifest extractNativeLibs warnings remain.
- `git diff --check`: PASS.

## Remaining blockers

1. Prompt success/cancellation/lockout/background races, unauthenticated doFinal rejection, missing/invalidated keys, enrollment changes and recovery on real API 30+ devices. Add device tests before connecting the adapter to active wallet UI.
2. v2 private atomic persistence, explicit migration with verified backup and rollback/recovery policy. The new flow deliberately does not write through the legacy v1-only storage layer. GCM detects modification, not replay of an older valid vault.
3. Native FRG ARM64 wallet API, canonical 25-word create/restore vectors, account scanning and transaction construction/signing/broadcast. No Java reimplementation of FRG signing was substituted.
4. Physical ARM64 RandomX known-answer execution, consensus seed/height selection, nonce search, accepted solo/pool submissions and thermal/foreground lifecycle testing. A compiled ARM64 library does not demonstrate execution or mining correctness.
5. Independent qualified mobile/cryptographic review and production release authorization.

MainActivity and production operation gates remain unchanged. This remains development groundwork, unsuitable for custody or public mining.
