# Native pool credited-block historical audit — November 2, 2026

**Status:** Prelaunch source-only hardening in [PR #196](https://github.com/tgibbsz32/forgecoin/pull/196). Does not activate FRG mining, Stratum, wallet transfers, Oracle infrastructure, or consensus. The frozen 20261026 mainnet remains locked.

## Why this is necessary

The pool previously reconciled mature rewards against a verified, contiguous ten-header daemon response. That protects recent maturation, but a previously credited block older than this window could be reorganized after the original credit and escape subsequent canonical checks. Pool payments must not proceed on a ledger with a known credited-chain conflict.

The existing [persistent LMDB reorganization quarantine](POOL-PERSISTENT-REORG-QUARANTINE-2026-11-02.md) holds accounting across restarts, but requires the pool to actually revisit the affected credited height before it can detect an older rewrite.

## This implementation

The native C pool now implements a **round-robin retrospective scan of every recorded `BLOCK_UNLOCKED` candidate in the actual LMDB blocks database**, including multiple candidates at a height. It validates each LMDB key, record size, matching height/status, 64-byte hash and parent fields, nonzero difficulty and reward before comparing historical evidence. A bounded timer dispatches one `get_block_header_by_height` request per period on the configured daemon RPC, and verifies the reply's structure, height, hash, parent, difficulty, reward, timestamp and orphan status.

- A matching canonical response advances the scan. A complete pass authorizes the *history audit gate* only; separate payouts, maturity, fees, canonical chain selection and wallet verification remain independent.
- A **valid but conflicting** canonical response freezes in-process reward accounting and writes the existing `frg.accounting.deep_reorg.quarantine.v1` LMDB marker. Mark persistence failure terminates the process.
- A malformed response, timeout, local LMDB error, allocation failure or in-flight ledger change keeps the audit unverified and the future payout path held. A transient invalid RPC reply is **not** mislabeled as a proven reorganization; no durable conflict marker is written from an unverified reply.
- The audit never assumes a previous process's scan results survived restart. It restarts after a newly credited candidate or a changed number of eligible entries.
- Late callbacks are rejected using a generation sequence, and a complete audit is required before the pool's already-compile-disabled wallet transfer path can consider payments.

## Limitations / risks to test

1. **Single daemon trust:** The current in-process scan uses the pool's configured daemon; independent observation from at least two separately operated nodes is still required to identify malicious or eclipsed RPC data. The separate [read-only chain watcher](../CHAIN_RISK_MONITORING_OPERATIONS.md) does not automatically authorize pool payouts.
2. **Throughput versus settlement availability:** One candidate is checked per two seconds. A sufficiently large ledger or rapidly accruing credits may cause audit restarts and delay payments indefinitely; this is intentionally fail-closed but requires scalability testing and potentially a reviewed batch/epoch mechanism.
3. **No automatic undo:** A conflict stops further crediting/payout consideration; it does not reverse previously signed transfers, repair miner balances, or select a canonical chain independently.
4. **No running pool validation yet:** Standalone json-c comparison tests are not equivalent to an actual LMDB + RPC + 61+-block restart/reorg fixture or dual-node security acceptance.
5. **Legacy daemon concerns:** The public `main` branch still does not contain the finalized frozen consensus integration. PR #185 remains distinct. No production network mutation is allowed.

## Required acceptance before public operation

- Standalone native comparator tests reject changed height/hash/parent/reward/difficulty/orphan and malformed RPC.
- x86_64 and ARM64 compile and native link CI pass.
- Disposable LMDB-backed fixtures cover multiple credited candidates at one height, clean full sweep, changed counts, mid-flight new credit, timeout, restart, orphan and 61+ block deep reorg.
- A running isolated pool proves recognized native daemon header replies and demonstrates 1% fee allocation, mature payouts and zero transfers while the audit is unverified/held.
- Independent-operator nodes, alerting and manual incident workflow are reviewed. No key material is included in these tests.

See [security research](../SECURITY_51_PERCENT_AND_TARI_MERGE_MINING_2026-11-02.md), [port contract](../NETWORK_PORTS.md), [issue #194](https://github.com/tgibbsz32/forgecoin/issues/194).
