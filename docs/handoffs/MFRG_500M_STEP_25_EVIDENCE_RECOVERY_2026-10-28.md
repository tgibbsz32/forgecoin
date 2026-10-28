# mFRG 500M Step 25 — offline provenance bundle integrity

Date: 2026-10-28. Repository: tgibbsz32/forgecoin. This step does not prove live deployment or blockchain facts.

## Delivered
- Offline SHA-256 integrity gate for raw evidence artifacts and backup copy, strict artifact allowlisted names, and two or more declared finalized HTTPS source snapshots with unique IDs and origins.
- 12 synthetic negative/positive test cases, Step 23 regression workflow, and this numbered handoff.
- Operator: `python3 tools/verify_mfrg_evidence_bundle.py bundle.json /path/to/artifacts`. Manifest must list `version=1`, `network=solana-mainnet-beta`, `mint`, `initialization_signature`, `sources`, `artifacts` filename-to-SHA256 mapping, and `backup` with `snapshot_file`, `sha256`, `size_bytes`.
- Evidence files are not added to the Git repository and must contain no secrets. Keep a separate immutable copy and independently pin the manifest hash.

## Hard limits and nonclaims
- Hash matching verifies file integrity relative to a supplied manifest **only**. It does not authenticate the manifest, actual owner mint, blockchain genesis, token account ownership, transaction signatures, RPC server honesty, source administration independence, or that the backup restores successfully.
- Different origin strings do not prove different operator infrastructure. Backup metadata is not a recovery drill. Step 24 SQLite result history, rollback prevention, actual crash recovery and consistency are NOT established by this tool.
- No live chain query, deployment, token issuance, sales, staking, custody changes or payments occurred. The repository still does not contain authenticated real mint initialization evidence; devnet mint is rejected.

## NEXT — STEP 26
Implement an actual isolated SQLite backup/restore drill with integrity checks and immutable/checkpointed evidence manifests, including rollback detection under a verified external anchor. Independently corroborate real onchain mint and holder history once authentic identifiers are supplied. Preserve all release holds.

Tokenomics unchanged: planned 500M SPL mFRG, six decimals, nine category caps, 50M lifetime fundraising (5M first pilot), 30M same-founder beneficial allocation (6%); native FRG remains independent.
