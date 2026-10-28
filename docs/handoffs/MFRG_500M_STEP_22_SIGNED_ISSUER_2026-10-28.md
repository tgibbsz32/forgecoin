# mFRG Step 22 handoff — signed session envelopes and durable nonce reservation

Date: 2026-10-28. Scope: offline prototype only. No mint or holder custody evidence supplied.

Implemented `tools/mfrg_signed_challenge_issuer.py`, 12 synthetic tests, dedicated CI, Step 21 regression.
- `new_claim()` generates 256-bit random session ID and per-account 256-bit nonce using OS CSPRNG, five-minute issuance/expiry proposal. Signing is performed externally; project signing keys are never loaded.
- `verify_envelope()` validates domain-separated Ed25519 signature on all issuance fields against a public key independently pinned by operator. Rejects modified signatures, future/expired sessions, duplicate nonces and malformed payloads.
- `Ledger` persists reservations and consumption in SQLite. Transactional uniqueness checks and `BEGIN IMMEDIATE` coordinate verifier processes sharing **the same durable SQLite DB**. Reopen preserves replay history. No network or hosted multiserver coordination.
- No integrated service, trusted key provisioning, proof of actual mint, proof of signer governance, challenge response verification in this module, remote distributed database, durable backup/restore protocol, or actual launch. Verifier orchestration must first independently authenticate issuer key, verify signed envelope and owner response using Step 20, ensure all challenge/nonces match, then consume reservation atomically. This module alone does not enforce that entire sequence, and `Ledger.consume` can be invoked by a caller without proof; do not use as a production API.

Outstanding: Design and test full integration, independent live chain attestations and mint identifiers, production storage permissions, replay recovery, issuer key lifecycle and rotation, PDA/multisig ownership verification. Original SPL budgets unchanged: proposed 500M, 50M fundraising lifetime (5M pilot), same founder beneficial 30M/6%; native FRG unaffected. No issuance, staking, multisig, payments, sales or treasury moves occurred.

Next Step 23: integrate verified challenge response with atomic reservation and consumption, fail closed on mismatches, and model recovery/idempotency. Remain strictly read-only.
