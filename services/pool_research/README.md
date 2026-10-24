# ForgeCoin pool research: offline accounting model

This directory is a **test-only model**, not a functioning mining pool, Stratum server or payout service. The accounting and protocol models open no sockets. Explicit capture utilities use loopback RPC and validate template structure only; they cannot validate RandomX shares, mine, access wallet RPC, or pay miners. Never deploy or advertise it as a working pool.

The `WorkerRegistry` simulates a 100-active-connection limit by unique connection ID; it is not an HTTP/TCP server and does not enforce a limit on real sockets. `allocate_reward` demonstrates deterministic integer splitting, including a 1% operator fee, of an *assumed eligible* atomic-unit reward based on example share weights. It is not PPLNS, does not determine actual eligible rewards, confirm blocks, account for orphaned blocks, account for payout transaction costs, or provide audit-quality bookkeeping. No policy is implied on minimum payout, rounding, pool-fee basis or confirmation threshold beyond this example.

Run offline: `python -m unittest discover -s services/pool_research -p test_model.py -v`.

Before a public pool, implement and independently verify native FRG-compatible Stratum/RandomX template handling, difficulty-vetted shares, durable share accounting, a real connection limiter, reorg-aware reward eligibility, payout safety, rate limiting, ARM64 runtime performance and actual 100-worker load testing. Solo mining and independent pools must remain permissionless, and the official pool's intended 1% fee must be separately disclosed from transaction costs.

## Experimental persistent reward ledger (offline only)

`ledger.py` adds a local SQLite prototype for **already independently verified** block records. It stores per-block integer allocations, deduplicates block hashes, tracks pending versus mature rewards, persists across restarts, and reverses allocations when callers identify an orphaned block. It explicitly rejects automatic revival of a previously orphaned block. Tests: `python -m unittest services.pool_research.test_ledger -v` from the repository root.

**Not production-safe:** There is no native chain RPC verification, share/RandomX validation, Stratum listener, canonical-chain completeness guarantee, payout-address verification, PPLNS implementation, operational concurrency policy, payout scheduler, multisig wallet, transaction signing, or spend authorization. `balances()` reports hypothetical mature allocations, **not withdrawable balances**. The caller must supply a complete, independently verified canonical block-hash set for the ledger scope; supplying a partial set incorrectly marks omitted blocks as orphaned. Do not connect this prototype to a wallet or use it with real miners' funds.
Experimental offline Stratum prototype: stratum_protocol.py checks request shape, session capacity, and ordering only. Parsed login is NOT identity authentication; no sockets, RandomX validation, job generation, daemon RPC, share acceptance, or payouts. Run: python -m unittest services.pool_research.test_stratum_protocol -v.
Offline ForgeCoin template validator: template_adapter.py checks JSON-RPC get_block_template structure, seed hash, integer fields, blob hex, reserved region and basic length limits. This is structural validation, exercised with synthetic fixtures and an opt-in real candidate capture: it does not call a daemon, verify chain identity, decode block versions or mining blob semantics, derive hashing work, validate RandomX, or submit a block. Tests: python -m unittest services.pool_research.test_template_adapter -v.
Isolated RPC fixture capture: python -m services.pool_research.capture_template --rpc http://127.0.0.1:39481/json_rpc --wallet-address DISPOSABLE_TEST_ADDRESS --output local-template-summary.json . Only explicitly configured loopback daemon is permitted; it writes sanitized metadata, not full block blobs. Do not commit private test addresses or connect to public/production nodes. Real candidate capture is documented below.
Local RPC integration fixture: test_capture_template.py launches an ephemeral loopback HTTP fixture, verifies get_block_template capture metadata and local-only URL restrictions. This is a simulated daemon response, NOT actual ForgeCoin daemon integration or consensus validation. The separate test_integration_capture.py exercises real candidate binaries when explicitly configured.
Isolated offline daemon argument builder: isolated_daemon.py constructs localhost-only, offline, distinct-port invocation for a disposable empty data directory. It does not start a node. Never point it to a real mainnet data directory. The integration harness creates its own disposable wallet and fresh database, supplies an empty configuration, and cleans up both.
Candidate executable compatibility check: optional FORGECOIN_DAEMON_BIN environment variable enables test_isolated_daemon.py to inspect real forged --help and compare expected flags. Removed unsupported --non-interactive from generated isolated daemon command. This check does not start daemon or capture a mining template.


## Reproduce real offline candidate capture

From the repository root, set `FORGECOIN_DAEMON_BIN` and
`FORGECOIN_WALLET_CLI_BIN` to the matching candidate `forged` and
`forge-wallet-cli` executables, then run:

```text
python -m unittest discover -s services/pool_research -v
python -m services.pool_research.integration_capture --daemon PATH_TO_FORGED --wallet-cli PATH_TO_WALLET_CLI --output local-evidence.json
```

On Windows, ensure the candidate wallet's runtime DLL directory is on the
child process PATH (the recorded run used `C:\msys64\mingw64\bin`). Use your
intended Python executable explicitly if adding that directory changes Python
resolution. Without both binary variables, the real integration test is skipped.
No binaries are downloaded or built by this test.

The harness reserves no persistent service: it prechecks ports 49580–49582,
creates a new offline wallet, starts an offline localhost daemon with an empty
configuration and fresh data directory, checks genesis height/offline/zero peers,
validates `get_block_template`, and stops the process in a finally block. DNS
checkpoints and update checks are disabled. HTTP proxies and redirects are
forbidden. Temporary wallet keys, password, address, logs and database are removed;
only sanitized metadata is published after clean shutdown. Do not use this tool
with public infrastructure or real wallets. The CLI accepts candidate paths
explicitly; it does not certify arbitrary binaries as safe or authentic.

### Recorded result, 2026-10-24

PR #25 was already merged at `3ed63d603d8fd6645fe624998e828630d37b8b13`.
`candidate-template-evidence.json` records a genuine archived Windows
consensus-candidate capture, including SHA-256 identities for both executables
and the observed genesis hash. This was the preexisting
`consensus-candidate-win64/bin` pair, **not a rebuild of current main** and not the
separate burn-genesis candidate. The candidate still reports upstream version
`v0.18.5.1-unknown`.

The real response passed the existing template validator: height 1, difficulty
500000, reward 2384185222 atomic units, 134 template bytes, 76 hashing bytes,
reserved offset 124 and requested reserve size 8. Seed hash matched the observed
genesis hash. The daemon reported offline mode, zero incoming/outgoing peers,
and exited with code 0. A second fresh-wallet/fresh-database integration run
passed in the full suite: **24 tests passed, none skipped**, Python 3.13 on Windows.
No daemon remained after the run. Wallet secrets and raw template blobs are not
committed. The retained summary cannot itself replay blob validation; rerun the
opt-in test to reproduce it with the actual binaries.

This establishes candidate RPC/adapter compatibility at fresh genesis only.
It does not establish RandomX share correctness, block submission, consensus
acceptance, later-height behavior, final monetary policy or public pool readiness.

### Failure handling follow-up, 2026-10-24

The harness now validates the daemon path and port policy before generating a
wallet, and rejects a template whose height or seed differs from the fresh
genesis context before publishing evidence. Shutdown timeout or a broken stdin
pipe triggers a kill and bounded process wait; an unclean exit cannot publish
success evidence.

Six failure-injection tests cover invalid daemon paths, template rejection,
unexpected peers, wrong height/seed, shutdown timeout and broken stdin. They
verify temporary-state cleanup and preservation of prior evidence on failure.
Validation: **30 tests passed, none skipped**, with the same archived candidate
pair and Python 3.13 on Windows, including a new disposable real-daemon capture.
The ordinary suite without binary opt-in passes 28 tests and skips the two
candidate-dependent tests. No daemon remained running after validation.
