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


## Native daemon template -> RandomX job integration (2026-10-25)

`daemon_job_source.py` is a **new isolation-stage native job boundary**, **not** an operational public pool. It only uses three allowlisted daemon JSON-RPC methods: `get_info`, `get_block_header_by_height` and `get_block_template`. The optional `LoopbackDaemonRpc` permits numeric localhost addresses with an explicit port and disables redirects and HTTP proxies.

An operator must explicitly supply the expected chain genesis hash, network type, and an approved **disposable** mining address. Each active worker receives a daemon-generated `extra_nonce` (8 random bytes). The returned serialized coinbase reserve, previous block hash, height, native hashing blob header, current tip and network identity are checked before any job is issued. A post-fetch tip check refuses races. Identical derived hashing jobs, cross-worker submissions, duplicates, invalid claimed digests, expired work and stale tips are rejected. A supplied trusted native `RandomX(seed, blockhashing_blob)` verifier recomputes the submitted nonce; the result is **always `POW_THRESHOLD_MET_UNCREDITED`**, never accepted as a payout or block.

The interface exposes Stratum-shaped `rx/0` job data but **does not open a socket, refresh jobs automatically, submit a block, account for PPLNS, persist shares or sign payouts**. It is single-threaded/single-process with a bounded outstanding job count; no production concurrency guarantees exist. Its nominal XMRig 4-byte target is limited to u32 share difficulty. Missing or improperly pinned genesis/network configuration prevents job issuance. Wallet/RPC keys never leave the host; the daemon HTTP client is intentionally loopback-only.

Offline fixtures:

```sh
python -m unittest services.pool_research.test_daemon_job_source -v
python -m unittest discover -s services/pool_research -t . -q
```

Optional actual RandomX CPU-worker exercise (requires a **separately built and trusted** `randomx_worker.cpp` binary and its runtime libraries):

```sh
python -m services.pool_research.tests.run_daemon_job_native_offline --executable /path/to/randomx_worker
```

**Observed developer evidence (Windows, October 25, 2026):** The helper compiled from the existing `tests/randomx_worker.cpp` using local MSYS2 g++ 16.2 and the already-built Fork RandomX static library. Its known 76-byte test vector returned `294083824fec5947ef2cd825e2bedcb34789e4cc6ad12d7823bcf0be51178f77`. A further test started a **disposable offline ForgeCoin daemon** in a fresh empty data directory, queried height-1 template with `extra_nonce`, and produced a matching native job digest. The daemon exited afterward. This **does not prove** compatibility with the repository's current source release or real mining payouts; the binary came from an existing isolated consensus-candidate build, not a reproducible new release build. No live production blockchain, miner, wallet funds, or pool server was touched.

**Next release blockers:** integrate actual worker session lifecycle and hash job rotation into a private Stratum service; independently check native chain identity, timestamp/seed and verified block candidate submission; handle genuine block acceptance, reorgs and maturity; implement durable verified share accounting, PPLNS, payout transaction recovery and minimum payouts; demonstrate multiple compatible XMRig miners, a 100-worker load target, secure payout RPC isolation and external review. Never confuse a real RandomX digest with an accepted network block, or a synthetic share ledger with an owed balance.


## Loopback native-template Stratum research socket (Step 003)

`native_stratum_research.py` adds a genuinely listening **numeric-loopback-only** Stratum-shaped test service which replaces synthetic header generation with the `DaemonJobSource` pipeline from Step 002. It accepts strict JSON-RPC-shaped `login`, `submit`, and `keepalived` frames through existing `SessionTable` validation. New connections receive a unique session ID and a daemon-generated `rx/0` job. Only the matching session/job can submit. Claimed hashes are recomputed with an explicitly supplied trusted native verifier; the protocol refuses duplicate/stale/cross-worker/low-difficulty jobs, inappropriate algorithms, oversized frames and concurrent overload.

The research socket is limited to **8** sessions maximum (4 default), uses bounded request counts and no public binding, payment keys, reward credits, block submission or wallet RPC. It is **not** a production pool or an authenticated miner/payout service: the miner's login string is never treated as proof of address ownership, and old jobs require reconnecting because proactive job broadcasts and difficulty rotation are not implemented. The response deliberately reports `POW_THRESHOLD_MET_UNCREDITED`, which **must not** be presented as a normal mining share acceptance to third-party XMRig clients.

Offline regression and optional real native CPU verification:

```sh
python -m unittest services.pool_research.test_native_stratum_research -v
python -m unittest discover -s services/pool_research -t . -q
python -m services.pool_research.tests.run_native_stratum_socket_offline --executable /trusted/randomx_worker
```

The optional runner uses a fake daemon and genuine C++ RandomX on a localhost socket; it opens no production daemon, accepts no funds, issues no payout, and exits after a single nonce check plus replay rejection. Release blockers are independent real-FRG daemon + actual XMRig interoperability, active worker rotation, canonical chain proof, accepted native block submission, recovery/reorg and PPLNS maturity-aware accounting, TLS, capacity and audited payout signing.


## XMRig 6.26.0 nonce-layout interoperability (Step 004)

A real, existing Windows **XMRig 6.26.0** executable was run for ten seconds with a single CPU thread, zero donations, RandomX light mode, and a loopback-only connection to `NativeResearchListener`. A **fixture daemon** supplied per-worker template fields; an actual C++ RandomX helper separately validated the miner-submitted nonce/digest. The bounded run reported **63 matching submissions**, all `POW_THRESHOLD_MET_UNCREDITED`. No pool shares, FRG, block rewards or payments were accepted. The miner was stopped by the test harness.

A first run found that fixture timestamps encoded in two bytes place the CryptoNote nonce at **byte 36**; XMRig `rx/0` instead patches **byte 39**. Although the existing offline bound-job validator allows variable nonce offsets, its `rx/0` job issuer now **fails closed if the daemon template doesn't place its nonce at byte 39**. The fake daemon was updated to use a five-byte timestamp varint, like current real ForgeCoin templates, and a unit test now asserts that the incompatible two-byte layout is rejected before job issuance. This is an interoperability constraint, not a consensus change.

Run the optional real-XMRig probe **only on an authorized Windows test machine** with reviewed XMRig/native binaries:

```powershell
python -m services.pool_research.tests.run_xmrig_native_loopback_offline --xmrig-executable C:\\test\\xmrig.exe --native-worker C:\\test\\randomx_worker.exe --seconds 10
```

The script accepts **no external pool endpoint**, opens only a random local TCP port, disables donation, limits XMRig to one thread and light RandomX, and terminates it at the hard-coded time bound. The script now fails if XMRig exits prematurely, rejects its CLI options, fails to log in, or produces zero native-verified submissions. The registered test login is a placeholder, not a real wallet address. Miner stdout may be empty due to Windows pipe buffering and process termination; the server-side native verification count is the principal evidence.

**Not proven:** mining against a canonical actual ForgeCoin daemon through the Stratum socket, a multi-worker XMRig load test, automatic job refresh on new block height, accepted block submission, active PPLNS rewards, mature wallet payouts, robust restart/reorg recovery, or an audited public mining pool. Do not open a public Stratum service or credit rewards based on these research fixtures.


## Real disposable ForgeCoin daemon + two actual XMRig instances (Step 005)

`tests/run_disposable_daemon_two_xmrig.py` adds a **manually invoked** isolated integration harness. It uses the owner-provided *disposable* offline wallet solely to obtain a public mining address, copied to a new temporary directory; starts a local **offline** ForgeCoin daemon on loopback-only P2P/RPC/ZMQ ports with a **fresh temporary chain**; and issues real `get_block_template` work through `DaemonJobSource` to two separate XMRig 6.26.0 instances connected only to the local Stratum research listener. Both XMRig processes use one CPU thread, zero donation and RandomX light mode. Their native shares are verified using the separately built C++ RandomX worker; **all are uncredited**, with no `submit_block`, share ledger, payout key or reward signing. At exit the miner/daemon processes are terminated and temporary files removed.

Observed on Windows in an extended **24-second**, worker-difficulty **30** bounded test: **2 local XMRig sessions received jobs**, **both submitted independently native-verified RandomX shares**, **59** matching submissions total, **19** legitimate busy rejections due to the listener's single global native verifier, and **0** credited shares, accepted blocks or paid rewards. An earlier 12-second run at difficulty 100 verified seven shares from only one of the two sessions. The extended test uses a stricter success condition: both distinct sessions must pass native RandomX verification.

The ForgeCoin daemon executable was an **earlier isolated consensus-candidate Windows binary**, not a newly reproducible binary from this repository's current main commit. The disposable chain is *mainnet-typed* but entirely offline/fresh and not the existing public network. The supplied genesis hash is obtained from the same daemon and therefore **is not independently verified**. This is an integration check, not security or canonical-mainnet evidence.

The script requires manually selected local binaries and the explicit disposable wallet filename, never follows URLs, opens no remote mining endpoint, and limits test duration and the number of worker processes. It is **not** the pool service and should not be deployed as one. Remediation remains necessary for busy-verifier fairness/throughput, automatic tip job rotation, accepted-block submission and durable canonical reward/payout accounting.
