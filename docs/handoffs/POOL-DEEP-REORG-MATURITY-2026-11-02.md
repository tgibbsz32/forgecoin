# ForgeCoin pool: 60-block maturity and late reorganization guard

**Date:** November 2, 2026. **Status:** Source-only draft engineering gate.
No public mining, Stratum, Oracle service, wallet transfer, or payout activation.

## Gap

The native C pool formerly skipped every stored candidate whose status was
not `BLOCK_LOCKED`. Consequently, when a previously credited candidate
was rechecked against a changed canonical hash or parent after a deep chain
reorganization, `process_blocks` simply ignored the inconsistency. Also,
the actual crediting callback trusted the request scheduler's 60-height
window but did not explicitly enforce the maturity tip for each candidate.

## Change in the actual native pool

`frg_reconcile_policy.h` is a pure C decision helper shared by the actual
`process_blocks` callback and a compiled regression harness. For every
candidate, it distinguishes:
- locked, younger than 60 heights: defer without credit;
- locked, at or beyond 60 heights, matching hash/parent and not orphaned:
  eligible to credit once under the existing integer 1% fee and nested LMDB
  transaction safeguards;
- locked but noncanonical/daemon-orphaned: mark orphan, no balances credited;
- already orphaned: ignore; already credited and still matching: ignore;
- already credited but conflicting hash, parent or daemon orphan flag:
  abort the **current parent LMDB reconciliation transaction** with
  `EPROTO` and log manual review required;
- malformed saved status or mismatched stored/observed heights: abort.
- non-`MDB_NOTFOUND` cursor read errors: abort the parent transaction instead
  of logging an error and inadvertently committing previously processed
  credits from the same reconciliation batch.

The mature-header callback now carries the observed tip captured when the
RPC request was constructed, avoiding accidental use of an unrelated tip
when asynchronous responses arrive. Startup's single-header callback
uses the pool's current reported network height. The pool verifies the
helper's status constants against native block-status values at compile time.

## Local executable fixture

`test_reorg_reconciliation_lmdb.c` opens and cleans up a real isolated
LMDB environment and consumes the **same C decision helper** as the pool.
It represents candidate block height 11, defers at tip 70 (59 heights),
credits at tip 71 (60 heights), commits exactly 0.99 FRG miner and 0.01
FRG fee atoms for a 1.00 FRG synthetic reward, then replays at tip 72
without a second credit. At tip 101, conflicting block hash, conflicting
parent, and an orphan flag each prohibit further credit. A second candidate
becomes orphaned at tip 71 and never receives a credit even after a later
matching callback. Failed and duplicate callbacks leave stored balances
unchanged.

Strict local GCC C11 warnings-as-errors compilation and **29 Python pool
source tests** passed. x86_64 and ARM64 native CI and compatibility
preflight exercise the same fixture and must pass before merge.

## Explicit release blockers

This is a **simulated height sequence and real LMDB fixture**, not a
daemon producing 61 real mainnet blocks, and not an invocation of the whole
pool callback against a running daemon. The detected inconsistency aborts
the **present transaction only**. It is **not** a persistent global payout
quarantine: after a restart, previously credited blocks may still require
additional rechecks. The normal mature-header scan covers only the requested
ten-height window; older credited blocks outside that window may not be
revisited automatically. A durable chainwide freeze / high-depth reorg
monitor, actual 60+ block live-pool ledger reconciliation, validated miner
signatures, round-dust distribution, real signed wallet transfers and
audited 1% operator fee reconciliation remain **necessary** before
authorizing pool payouts or mainnet release.

Frozen native P2P/RPC/ZMQ ports remain 39480/39481/39482. The legacy Oracle
19480 firewall allowance is separately unresolved. No production changes.
