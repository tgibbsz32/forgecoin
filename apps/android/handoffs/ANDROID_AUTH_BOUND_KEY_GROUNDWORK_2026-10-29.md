# Android authentication-bound crypto groundwork

Adds `SolanaAuthenticatedKey` as a **non-integrated** future CryptoObject key candidate: a separate v2 Android Keystore AES-256-GCM key requiring per-operation strong biometric authentication. This class does not expose raw key material. The caller must pass the returned Cipher into an Android BiometricPrompt CryptoObject, verify success, and only then call `doFinal`. Use a versioned v2 vault format; never reinterpret existing v1 envelopes using this key.

Limitations: DEVICE_CREDENTIAL is intentionally **not** included because a per-operation CryptoObject token with combined credential modes has platform limitations. Credential fallback, user enrollment changes, recovery on another handset, invalidated keys, IV and envelope binding, rollback protection, atomic storage, migration, UI tests, error handling, and external security review require further design and validation. Existing v1 test vaults are unchanged and not automatically migrated. This addition is not production custody functionality and must not be connected to active wallet UI without authenticated CryptoObject tests.

The independent security review and actual native FRG Android wallet/RandomX miner remain uncompleted; successful compilation is not an acceptance test.
