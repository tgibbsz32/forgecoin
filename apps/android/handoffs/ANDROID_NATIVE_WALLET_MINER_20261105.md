# ForgeCoin Android native wallet and miner integration

The Windows worktree at `D:\ForgeCoin-Android-20261105-Build` resumed
`ci/android-jvm-tests-20261105` at `7d7f30734ff3f5b4ba0d8569a371d0c25507e67f`.
This is development evidence. Mainnet release authorization remains false.

## Reuse and scope

- Recovered the working ARM64 XMRig 6.26.0 executable and foreground-service
  source from the previous local Android project. The staged executable has
  SHA-256 `ca72838b0c5499465f3f8f81bd09b42e6b0823180b8ab675d0ef8e26baca4f47`.
  Its Android build patch and GPL license are in `../third_party/xmrig/`.
- The JNI bridge links the existing native ForgeCoin `wallet_api` from the
  frozen branch, including its Electrum mnemonic and key-file implementation.
  The prior Java key derivation and external wallet RPC client are not used.
- The Android header and launcher use the exact official website logo
  (`docs/images/forgecoin-logo.png`, SHA-256 beginning `fd4aede8`), with the
  website's navy, cyan and blue palette.
- Wallet and miner binaries are staged in `app/src/debug/jniLibs/arm64-v8a/`.
  Public network operations cannot be enabled by an Intent, config file, or
  successful instrumentation run. Local QA verifies FAKECHAIN, zero peers,
  and the frozen genesis hash before opening the daemon connection.
- Source consensus and network configuration were unchanged: P2P 39480,
  daemon RPC 39481, ZMQ RPC 39482; genesis nonce 20261026 and hash
  `4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c`.

## Reproduction

1. On Windows, export the pinned input with
   `git archive --output=apps/android/build/native-source-input.tar 7d7f307`.
   Use a fresh build root to change the native engine input.
2. Run `apps/android/tools/build-wallet-depends.sh` and
   `apps/android/tools/build-native-wallet.sh` with bash in the Windows PC's
   ForgeCoinBuild WSL distribution. The former builds the repository's
   checksum-pinned ARM64 dependencies; the latter links and stages the JNI
   library. An isolated source copy normalizes historical CRLF shell files.
3. Place the matching executable in
   `app/src/debug/jniLibs/arm64-v8a/libxmrig.so`. The service checks its exact
   hash, ABI and executable bit before startup; Gradle preserves the bytes.
4. With JDK 21, Gradle 8.11.1 and Android SDK 35:
   `gradle --offline :app:assembleDebug :app:testDebugUnitTest :app:assembleDebugAndroidTest :app:lintDebug`.
   Install both APKs on a disposable ADB device.
5. Run `python tools/test-isolated-mining.py --daemon <verified-forged.exe>
   --device <adb-serial> --mode both` from `apps/android`. Use `--mode wallet`
   for received-balance scanning and `--mode send` for send/cancel/receive.
   This harness starts an offline temporary FAKECHAIN and cleans up its own
   daemon and ADB forwards. Never run it against a public endpoint.

## Evidence and limits

- Windows ARM64 wallet JNI and APK compilation passed; Android lint,
  42 JVM tests and 10 Python source/package guard tests passed.
- x86_64 Android emulator with ARM64 translation: native JNI probe and
  two RandomX tests passed, including the upstream reference digest.
- Native wallet lifecycle passed: generate 25 words, standard FRG address,
  encrypted reopen, wrong-password rejection, overwrite protection, seed
  restoration to the same address, and bad-seed rejection.
- Isolated balance scan passed: an actual native FAKECHAIN coinbase was
  detected by the restored Android wallet and correctly remained locked.
- Android XMRig solo acceptance passed, advancing the disposable chain
  from height 1 to 25 and reporting nonzero measured hashrate.
- Android Stratum acceptance passed with one independently verified
  accepted share and two rejected shares; no pool credits or payouts.
  Later identity-gated rechecks encountered ADB transport/fixture timeouts.
- Native send preparation, cancellation and acknowledgment are wired for
  isolated instrumentation. The send test timed out during disposable wallet
  setup on emulator-5554; it never verified a broadcast. The follow-up uses
  one open wallet at a time and compiled successfully, but emulator-5570
  failed to install the APK with `cmd: Failure calling service package:
  Broken pipe (32)`. Sending remains disabled in the GUI.
- The release build compiled and its APK contents contained only the RandomX
  and runtime-probe support libraries. It excluded the wallet and XMRig
  binaries. The release readiness check returned `BLOCKED` as intended.
  A final signed APK ZIP has not been produced.
- No physical ARM64 handset was connected. Physical lifecycle/thermal
  testing, independent security review, and production signing/release
  validation remain separate gates. No mainnet activation occurred.
