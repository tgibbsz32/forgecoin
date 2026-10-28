# miniFORGE 500M Step 26 — isolated SQLite restoration drill

Date: 2026-10-28. Repo: tgibbsz32/forgecoin. Offline tests only, no production writes.

## Implemented
- `tools/mfrg_sqlite_recovery_drill.py` makes a consistent SQLite online backup from an opened read-only source into a temporary isolated database, performs `PRAGMA integrity_check`, checks session/nonces/results tables and consumed-vs-results counts, validates restored logical counters and computes restored backup SHA-256.
- Optional independently supplied checkpoint pins a restored backup SHA-256 and minimum consumed session/result counters; a lower count or wrong digest fails closed. This establishes only that a *supplied anchor* matches, not that it is authentic.
- 8 synthetic tests include roundtrip, exact pin, rollback counter, digest mismatch, missing result/table, invalid anchor and unchanged source. CI also runs Step 22/23 regressions.
- Command: `python3 tools/mfrg_sqlite_recovery_drill.py path/to/ledger.sqlite --anchor-json /secure/pinned-anchor.json`. Read-only validation does not overwrite source.

## Limitations
This is an **isolated backup/restore exercise**, not a deployed backup schedule, disaster-recovery test, secure archive, signed external checkpoint authority or production rollback prevention. A malicious database with consistent counts can pass without a trusted anchor. The optional anchor must come from a separately authenticated, tamper-resistant channel; checking the supplied JSON does NOT authenticate it. Physical/WAL storage, backup rotation, cryptographic signed checkpoints and restore to production after disaster are out of scope. No live Solana mainnet mint, account-control, provider-independence or treasury custody proof. No production minting, signing, payments, staking, transfers or presale changes.

## Next — Step 27
Develop an independently verifiable signed checkpoint/anchor chain bound to full ledger contents, sequence numbers and restore evidence, with rollback/replay detection and adversarial tests. Do not claim release readiness without genuine authenticated mainnet identifiers and security review.

Intended 500M mFRG with nine categories, 50M fundraising lifetime/5M first pilot, same founder beneficial 30M/6%, native FRG unchanged.
