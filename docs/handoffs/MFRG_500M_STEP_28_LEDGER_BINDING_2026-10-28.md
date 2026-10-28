# miniFORGE Step 28 — offline signed-checkpoint to SQLite ledger binding
Date: October 28, 2026. Repository: tgibbsz32/forgecoin.

## Implemented
- `tools/mfrg_checkpoint_ledger_binding.py` hashes canonically sorted full SQLite session, nonce and result records, verifies SQLite integrity and matching consumed/result counts, and compares the resulting logical hash and raw backup-file digest with the latest verified Ed25519 checkpoint from Step 27. Uses a read-only database connection.
- Five synthetic cases exercise success, changed row, deleted row, changed raw backup bytes, and wrong anchor. Step 27 regression CI.
- This implementation is **verification only**; signing and checkpoint generation are deliberately outside its scope pending owner-approved signer provisioning. A chain can be fabricated if the caller controls its supposed pinned signer/anchor.

## Caveats
A database changing concurrently can produce a torn raw-file hash versus SQLite read; operate only on immutable isolated backup copies. Checking an external hash does not establish independent anchor authenticity. No live mint, treasury ownership, Solana RPC source integrity, beneficial control or funding verified. Production token operations remain disabled.

## Next — Step 29
Create an offline export/review flow for independent checkpoint signing with explicit multisig governance approvals, and validate source provenance for genuine mainnet deployment identifiers. Test different SQLite page layout/serialization behaviors, backup consistency, and revision recovery. Continue release holds.

Unchanged: proposed 500M mFRG, 50M lifetime fundraising with 5M initial pilot, founder beneficial 30M/6%, nine categories; FRG native consensus unaffected.
