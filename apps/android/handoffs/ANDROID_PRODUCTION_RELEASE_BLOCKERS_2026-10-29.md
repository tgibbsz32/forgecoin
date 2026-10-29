# ForgeCoin Android — production release blockers and handoff (2026-10-29)

## Live infrastructure inspection
On the authorized Windows developer computer, ADB reports only an `sdk_gphone64_x86_64` emulator (emulator-5560), **not** a physical ARM64 handset. Android SDK has NDK r27d. No evidence of ARM64 ForgeCoin daemon/wallet/miner binary accepted against current consensus has been established. The Android README explicitly identifies a restricted preview; native FRG and RandomX operations remain disabled.

## New static fail-closed audit
`python apps/android/tools/release_readiness.py --require-release` requires physical ARM64 test evidence, native binary, consensus verification, native FRG 25-word wallet create/restore, signing/broadcast, ARM64 RandomX solo+pool acceptance, thermal/foreground safety, device authentication and signed independent security review. Its JSON evidence input is **untrusted self-attestation**, not independent audit. The script cannot replace evidence verification. The default report exits 0 to allow dev builds; `--require-release` exits 1 on missing gates.

## Work that remains, cannot be claimed complete
1. Cross-compile current FRG daemon, native wallet and RandomX for Android arm64; verify frozen genesis, chain IDs, pool/solo blocks and miner payouts with independent nodes and network fixtures.
2. Implement native FRG's proper 25-word mnemonic, wallet key derivation, spend/view key encryption, balance scanning and signed send on Android with end-to-end acceptance.
3. Enforce device authentication before decrypt, handle lockout/invalidated Keystore and recover with an offline seed on a new handset.
4. Connect a physical ARM64 phone to ADB and perform install, clean-device restore, mining thermal/battery checks, signing and recovery.
5. Commission an independent qualified mobile/cryptographic security review. Neither this model nor a self-authored test constitutes independent review.
6. Create immutable signed release artifacts only after evidence review and owner approval. No public mining activation or mFRG issuance.

The existing Android Solana debug wallet interface must not be used for custody of funds.
