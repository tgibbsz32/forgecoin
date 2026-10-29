# Android Solana Public Address — 2026-10-29

## Completed and verified on Windows
Implemented standalone offline public-address derivation: valid BIP39 English mnemonic -> 64-byte BIP39 seed -> hardened SLIP-0010 Ed25519 seed at m/44'/501'/account'/0' -> Ed25519 public point -> Solana base58 address. For the disposable BIP39 phrase `abandon` repeated 11 times then `about` with empty passphrase, the resulting address is `HAgk14JpMQLgt6rVgv7cBQFJWFto5Dqxi472uT3DKpqk`, independently equal to the Windows libsodium-derived Ed25519 public key `f036276246a75b9de3349ed42b15e232f6518fc20f5fcd4f1d64e81f9bd258f7` base58-encoded.

The connected Windows PC compiled and ran `SolanaPublicAddressSmoke`. Tests passed fixed known address, deterministic recreation, account separation and base58 leading-zero behavior.

## Critical security notes
The current Java reference computes Ed25519 public points using `BigInteger` modular arithmetic. That implementation may have variable-time behavior and is **not approved for production wallet use**. Before live wallets, replace with a vetted Android-compatible Ed25519 implementation with constant-time secret operations, pinned provenance, independent test vectors and security review. JVM strings and managed arrays retain data during garbage collection; ensure no mnemonic logging, storage or screenshots. The vault and UI are still not connected. No Android device runtime or complete APK test in this phase.

## Follow-on gates
1. Replace reference Ed25519 scalar multiplication with vetted cryptographic library and verify address parity.
2. Android Keystore AES-GCM Android SDK compile, tamper/recovery tests and safe private-file persistence.
3. Add Create/Restore UI with separately verified BIP39 word backups and explicit passphrase policy.
4. Run complete Gradle build, Android arm64 install, and clean-device recovery tests.
5. Continue native FRG 25-word mnemonic wallet and RandomX work; keep mining and token controls disabled.
6. Independent audit before production mint authority custody; no public mint/sale/mining authorization occurred.
