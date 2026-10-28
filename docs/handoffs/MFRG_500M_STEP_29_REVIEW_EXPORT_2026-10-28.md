# miniFORGE Step 29 — checkpoint export and offline governance review
Date: 2026-10-28. Repo: tgibbsz32/forgecoin.

## Delivered
`tools/mfrg_checkpoint_review_export.py` exports an **unsigned** checkpoint record from local SQLite with logical ledger SHA-256, physical backup SHA-256, consumed/result counts, sequence, previous hash and record fingerprint. Requires two distinct reviewer IDs; these are policy declarations, not authenticated reviewer identities. No private signing keys or signing service is used.
`review()` checks explicit approval declarations from distinct allowlisted reviewers bound to the record fingerprint but does **not cryptographically validate approvals**. This is a planning/review format, NOT a security approval. Eight synthetic tests plus Step 28 regression CI.
Command: `python3 tools/mfrg_checkpoint_review_export.py /isolated/backup.sqlite --sequence 0 --reviewer reviewer-a --reviewer reviewer-b`.

## Unresolved
The input must be an immutable isolated SQLite backup, not a live database. No authenticated external reviewer registry, hardware signer, cryptographically signed approvals, or governance quorum has been deployed. The operator controls the reviewer ID list and could forge approvals. No independently authenticated production Solana mint, issuance transaction, source provenance, custody, or multisig deployment exists in verified repository data.
An approved-looking export is NOT signed, is NOT published to a trusted external anchor, and does not enable token operations.

## NEXT — Step 30
Introduce independently pinned Ed25519 reviewer public keys and cryptographically signed, exact-fingerprint approvals with threshold policy and adversarial tests, before signing any checkpoint. Continue strict read-only policy. Nine budgets, planned 500M mFRG, 50M lifetime fundraising/5M pilot, same founder beneficial 30M/6%, native FRG unchanged.
