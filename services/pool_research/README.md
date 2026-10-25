# ForgeCoin pool research: offline accounting model

This directory contains **experimental research**, not a production mining pool or payout service. Most modules are offline models. The explicitly invoked synthetic listener below opens loopback sockets and verifies fixed synthetic work with a supplied native RandomX executable. It has no chain submission, wallet access, rewards or payouts. Never advertise this directory as a working public pool.

The `WorkerRegistry` simulates a 100-active-connection limit by unique connection ID; it is not an HTTP/TCP server and does not enforce a limit on real sockets. `allocate_reward` demonstrates deterministic integer splitting, including a 1% operator fee, of an *assumed eligible* atomic-unit reward based on example share weights. It is not PPLNS, does not determine actual eligible rewards, confirm blocks, account for orphaned blocks, account for payout transaction costs, or provide audit-quality bookkeeping. No policy is implied on minimum payout, rounding, pool-fee basis or confirmation threshold beyond this example.

## Synthetic socket integration (2026-10-25)

`synthetic_listener.py` binds only `127.0.0.1` on an ephemeral port. It uses
Stratum-shaped login/submit/keepalived messages but deliberately reports
`SYNTHETIC_ONLY` and `POW_THRESHOLD_MET_UNCREDITED`, never production acceptance.
Do not point a miner at it: tests submit fixed nonces, not mining searches.
There is no configurable daemon, wallet, block submission or payout endpoint.

Each connection receives distinct synthetic header bytes, a session token and
template-bound job. Claimed digests are compared with freshly computed native
digests. The listener rejects cross-session jobs, digest mismatch, low difficulty,
duplicates, stale work and malformed messages. Research bounds: four sessions by
default (maximum eight), one native verification at a time with immediate busy
rejection, 4096-byte frames, 32 requests per connection (maximum 64), ten-second
idle timeout and sixty-second job lifetime. These are test controls, not proven
public DoS isolation or 100-worker throughput. Login strings are not authenticated
identities. Live job/session state is in memory and is not durable share accounting.
The default native adapter now keeps a bounded persistent light-mode worker;
public-pool throughput and isolation are still unverified.

```sh
# Socket regressions with an explicitly fake verifier:
python -m unittest services.pool_research.test_synthetic_listener -v
# Same regressions using a separately built trusted reference executable:
FORGE_SYNTHETIC_NATIVE=/absolute/path/randomx_reference python3 -m unittest services.pool_research.test_synthetic_listener -v
# Preferred persistent native protocol:
FORGE_SYNTHETIC_PERSISTENT=/absolute/path/randomx_worker python3 -m unittest services.pool_research.test_synthetic_listener -v
# Manual loopback research only (Ctrl-C closes it):
python3 -m services.pool_research.synthetic_listener --executable /absolute/path/randomx_worker --journal /private/research/checks.sqlite
```

Oracle ARM64 native socket tests: eight passed, including busy retry without
nonce consumption and verifier failure rejection. No listener is installed as
a service or left running after the tests. Persistent share accounting, live
miner compatibility, canonical chain jobs, block acceptance and payouts remain
unverified and disabled.

### Durable synthetic evidence records

The listener now requires a `SyntheticJournal` and commits a successful native
check before returning `recorded: true`. SQLite records contain job/nonce,
pseudonymous session token, computed digest, difficulty, hashing-blob SHA256,
seed and server timestamp. They contain no login strings, passwords, wallet
addresses or balances. Schema constraints fix `synthetic=1` and `credited=0`.
Records are evidence of synthetic checks, not miner credits or payout claims.

Transactions use synchronous FULL/DELETE journaling, a 100 ms lock timeout,
10,000-record maximum and 16,384-page ceiling (64 MiB with the default 4 KiB
pages). A full, locked, read-only or unavailable journal cannot produce a
success response. Duplicate identical records are idempotent; conflicting
records fail. Existing unrelated databases are rejected without modifying them.
Keep the database in a private research directory; this is not a hostile-path
defense, tamper-proof audit log or independent attestation.

On restart, prior evidence survives but live sessions/jobs do not: reconnect
for new synthetic work. A failed write may consume an in-memory nonce; reconnect
rather than interpreting rejection as lost earnings. A commit can also precede
a lost client response. No production credit-recovery semantics are claimed.
Tests cover reopen/idempotence/conflicts, abrupt child-process exit before
commit, integrity recovery, storage failures, record limits and socket restart.
Abrupt-process-exit testing is not a hardware power-loss guarantee.

### Persistent native worker

`tests/randomx_worker.cpp` implements a bounded tagged stdin/stdout protocol.
It retains one default-flags RandomX cache/VM for a seed, reinitializes on seed
changes, and exits after 64 requests. Input lines are bounded before allocation
can grow beyond 524,400 bytes. There is no JIT/MSR configuration, nonce search,
network access, daemon or wallet integration. Build explicitly against reviewed
RandomX headers/library; there is no runtime compiler or automatic download.

`persistent_randomx.py` permits one request at a time, checks response tags and
digest shape, bounds pipe reads and applies a deadline to both writes and reads.
Timeouts/malformed output/crashes discard the worker and return failure; requests
are not silently retried. A later explicit request can start a replacement after
cleanup. If cleanup fails, the adapter is disabled. Closing waits for outstanding
work and reaps the helper. A listener nonce reserved before verifier failure may
remain consumed; reconnect for new synthetic work rather than assuming a retry
of the same nonce will succeed. The legacy one-shot diagnostic protocol is
available only through `--one-shot-reference`.

Oracle evidence: 65 fixed-vector requests with recycle, seed/input comparisons
against the one-shot reference, native malformed-frame refusals, and 23
worker/journal/socket tests passed. Six worker fault tests use a fake Python
digest worker to exercise real subprocess failure paths; socket/native-vector
checks use actual RandomX. This is not an independent implementation comparison,
production performance certification, OS sandbox, miner compatibility or payout
acceptance. Process/cache reuse is implemented; no worker-capacity promise follows.

Run offline: `python -m unittest discover -s services/pool_research -p test_model.py -v`.

Before a public pool, implement and independently verify native FRG-compatible Stratum/RandomX template handling, difficulty-vetted shares, durable share accounting, a real connection limiter, reorg-aware reward eligibility, payout safety, rate limiting, ARM64 runtime performance and actual 100-worker load testing. Solo mining and independent pools must remain permissionless, and the official pool's intended 1% fee must be separately disclosed from transaction costs.

## Experimental persistent reward ledger (offline only)

`ledger.py` adds a local SQLite prototype for **already independently verified** block records. It stores per-block integer allocations, deduplicates block hashes, tracks pending versus mature rewards, persists across restarts, and reverses allocations when callers identify an orphaned block. It explicitly rejects automatic revival of a previously orphaned block. Tests: `python -m unittest services.pool_research.test_ledger -v` from the repository root.

**Not production-safe:** There is no native chain RPC verification, share/RandomX validation, Stratum listener, canonical-chain completeness guarantee, payout-address verification, PPLNS implementation, operational concurrency policy, payout scheduler, multisig wallet, transaction signing, or spend authorization. `balances()` reports hypothetical mature allocations, **not withdrawable balances**. The caller must supply a complete, independently verified canonical block-hash set for the ledger scope; supplying a partial set incorrectly marks omitted blocks as orphaned. Do not connect this prototype to a wallet or use it with real miners' funds.
Experimental offline Stratum prototype: stratum_protocol.py checks request shape, session capacity, and ordering only. Parsed login is NOT identity authentication; no sockets, RandomX validation, job generation, daemon RPC, share acceptance, or payouts. Run: python -m unittest services.pool_research.test_stratum_protocol -v.
Offline ForgeCoin template validator: template_adapter.py checks JSON-RPC get_block_template structure, seed hash, integer fields, blob hex, reserved region and basic length limits. This is synthetic fixture validation only: it does not call a daemon, verify chain identity, decode block versions or mining blob semantics, derive hashing work, validate RandomX, or submit a block. Tests: python -m unittest services.pool_research.test_template_adapter -v.
Isolated RPC fixture capture: python -m services.pool_research.capture_template --rpc http://127.0.0.1:39481/json_rpc --wallet-address DISPOSABLE_TEST_ADDRESS --output local-template-summary.json . Only explicitly configured loopback daemon is permitted; it writes sanitized metadata, not full block blobs. Do not commit private test addresses or connect to public/production nodes. Actual daemon capture and integration test are still pending.
Local RPC integration fixture: test_capture_template.py launches an ephemeral loopback HTTP fixture, verifies get_block_template capture metadata and local-only URL restrictions. This is a simulated daemon response, NOT actual ForgeCoin daemon integration or consensus validation. The actual candidate executable was inspected for --offline and isolated RPC flags, but real template capture remains pending until a disposable test wallet is provisioned.
Isolated offline daemon argument builder: isolated_daemon.py constructs localhost-only, offline, distinct-port invocation for a disposable empty data directory. It does not start a node. Never point it to a real mainnet data directory. Candidate-network disposable wallet creation and real block-template capture remain pending.
Candidate executable compatibility check: optional FORGECOIN_DAEMON_BIN environment variable enables test_isolated_daemon.py to inspect real forged --help and compare expected flags. Removed unsupported --non-interactive from generated isolated daemon command. This check does not start daemon or capture a mining template.

### Height-indexed reward reconciliation (2026-10-25)

`RewardLedger.reconcile_chain(canonical_by_height, tip_height)` now requires a
`dict[int, str]` with the canonical hash at every recorded height at or below
the tip, plus the tip itself. Missing heights, malformed hashes, duplicate hashes
at different heights and the former list/set API are rejected before updates.
For example, a ledger block at height 100 and tip 160 requires observations for
both 100 and 160. A hash observed at another height cannot mature that reward.
Competing candidates at one height are reconciled against that height's hash.
A shorter canonical chain orphans candidates above its tip; a tip rollback below
maturity demotes a still-canonical reward to immature. Orphan revival remains
blocked for independent investigation. Coverage checks and all changes run in
one locked transaction; an invalid view cannot partly change balances.

The caller must still obtain and verify a coherent snapshot from a trusted native
node. This API does not authenticate RPC, prove ancestry or network identity,
verify share weights, or authorize payouts. The old hash-set completeness warning
above describes the replaced API; partial observations now fail closed. Existing
SQLite schemas need no migration. No production financial concurrency or recovery
certification is implied.

Run the complete offline pool suite from the repository root:
`python -W error::ResourceWarning -m unittest discover -s services/pool_research -t . -v`.
Native binary and platform-dependent tests may explicitly skip when unavailable;
fixture hashes do not prove native mining or payout acceptance.
