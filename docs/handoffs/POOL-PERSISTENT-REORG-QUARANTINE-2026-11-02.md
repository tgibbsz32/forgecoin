# ForgeCoin pool durable reorganization quarantine (prelaunch)

**Date:** November 2, 2026. **Status:** Source-only engineering safeguard.
No production daemon, Stratum listener, Oracle firewall, wallet transfer, or
public mining is enabled or authorized by this change.

## Problem

The existing native jtgrassie-derived pool [PR #192] aborts the current
LMDB batch when a previously credited block is revisited with a changed
hash, parent or orphan flag. But that abort is not durable: after a pool
restart, a different block can be credited as though the deep-reorg alarm
never occurred. Ledger credits can also be lost if a write error is
reported but the nested balance transaction is committed anyway.

## Changes in the actual C pool

- The new `frg_accounting_quarantine.h` reads/writes
  `frg.accounting.deep_reorg.quarantine.v1` in the pool's **existing
  LMDB properties DB**. Value is the first conflicting block's height.
  Repeated alerts do not overwrite the first incident. A malformed
  marker is an error, **never** treated as absent.
- On a previously credited conflict or invalid saved block status,
  `process_blocks` first aborts all balances and block-state changes in
  the current parent LMDB transaction. It then writes the quarantine in
  an **independent** committed transaction, and latches the current
  process against further credits. If persistence fails, the process
  terminates rather than continuing ledger credits. The failure to
  persist is itself a required operator investigation.
- On a new process start, the database initialization checks the
  persistent marker before any normal pool listeners are started.
  It exits nonzero with an explicit error if the marker is present
  or cannot be reliably read.
- Every future canonical reward-crediting batch checks the marker
  inside its writable LMDB transaction. The `send_payments` path also
  checks the marker even in a future separately reviewed build that
  might remove the existing compile-time wallet payout restriction.
- `balance_add` now rejects malformed stored balances and overflow of
  64-bit atomic amounts. Both creation and update errors from
  `mdb_cursor_put` **abort** the nested transaction instead of
  logging an error and committing a partial or unchanged entry.
- No automatic unfreeze / erase path is provided. Recovery must be an
  explicitly authorized offline procedure after cross-checking chain
  history, every affected candidate, credited miner/operator balances
  and any already-sent transfers. Do not erase the marker to make the
  pool start without completing that reconciliation.

## Tests

`services/official_pool/tests/test_persistent_reorg_quarantine.c`
opens a real disposable LMDB ledger, marks an alert based on the
same C reorg decision helper as `pool.c`, verifies repeat alerts
preserve the first height, **closes and reopens the environment**,
confirms the hold survives, and then verifies a corrupted marker is
rejected rather than ignored. The fixture is included in native x86_64
and ARM64 pool CI and the Linux compatibility preflight.
`test_pplns_accounting.c` additionally verifies bounded uint64 balance
addition near `UINT64_MAX`; the Python source guard asserts the real
code actually checks the on-disk marker and aborts write failures.

Local **31 Python pool tests**, strict GCC native C LMDB and accounting
fixtures passed, as did the offline native C/C++ pool object compile.
Independent native cross-architecture pool CI still must verify
the committed source before merging.

## Important remaining gaps

- The hold triggers only when an already credited block is **revisited**.
  The ten-header mature window does not itself perform historical audits
  of all prior credited heights; a durable full-history reorg monitor is
  still needed.
- If a damaged database or storage failure prevents writing the marker,
  the current process exits, but the on-disk quarantine cannot be
  guaranteed. The operator must take the pool offline and investigate.
- The payout-path marker read and a future wallet RPC transfer are not
  transactionally coupled; a separate release design must prevent a
  concurrent writer from quarantining the ledger after the read but
  before a transfer. The safer existing production state is wallet
  transfers compile-time disabled with `disable-payouts=1`, wallet RPC
  port 0, and public Stratum off.
- This is **not** a 61-block running pool with a real daemon, not an
  actual signed genesis-output spend test, not live treasury/pool
  payout verification, not a completed network hard fork or launch.

Frozen selected P2P/RPC/ZMQ remain 39480/39481/39482. No Oracle change.
