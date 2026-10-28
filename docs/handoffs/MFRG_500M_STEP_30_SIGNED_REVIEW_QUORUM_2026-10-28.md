# miniFORGE Step 30 — offline signed reviewer quorum

Date: 2026-10-28. Repo: tgibbsz32/forgecoin.

## Delivered
- `tools/mfrg_signed_review_quorum.py`: validates Ed25519 signatures from distinct declared reviewers against a domain-separated claim containing exact checkpoint fingerprint and independently supplied SHA-256 of a reviewer registry/threshold policy. Requires threshold >=2; reviewer identities must be in the checkpoint's allowlist and independent policy. Duplicate reviewers, malformed keys, tampering and insufficient signatures are rejected.
- Ten synthetic positive/adversarial tests using ephemeral keys; regression tests for Step 29. Dedicated GitHub Actions and this handoff.
- No signing keys are loaded by production code; signatures are supplied as public evidence.

## Limitations
A SHA-256 matching a supplied policy does not prove who pinned it. Reviewer public keys, identity, authorizations, actual governance structure and signatures' institutional legitimacy require independently authenticated governance evidence. The signature quorum verifies submitted **offline checkpoint review** only; it is not a Solana SPL multisig deployment or a token transaction authorization. The code does not create signed checkpoint records, independently validate Solana genesis/mint or holder ownership, or enable issuance, staking, transfers, funding or sale.

## NEXT — Step 31
Bind signed approval quorum to actual checkpoint signature creation workflow through independently provisioned signer, protect against approvals reused across unrelated checkpoints/policies, and develop full offline verification and source-evidence pipeline. Do not move beyond read-only status until genuine authenticated mainnet identifiers and custody attestations exist.

Tokenomics unchanged: 500M proposed SPL mFRG, 50M lifetime fundraising (5M initial pilot), nine budgets, 30M same-founder beneficial / 6%, native FRG independent.
