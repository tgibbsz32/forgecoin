# STEP-002 — 2026-10-25 — real daemon template / native RandomX boundary

## Repository and source scope

- **Original FRG:** https://github.com/tgibbsz32/forgecoin
- **Separate FCMP++/CARROT:** excluded. No Solana, synthetic asset, or fork upgrade work was imported.
- Starting **main**: `6fc2bf8acb249ce6559c58ea272794bfaa91231b` (PR #103 reward-reconciliation fix was merged).
- Isolated development branch: `feat/pool-native-job-boundary-20261025`; separate Temp checkout; original user development checkout and its uncommitted consensus files left untouched.
- **Implementation commit:** `7aba00fd19d66c1397b09461a855e5795db784c8`.
- This handoff is intentionally committed separately so it can name that exact implementation commit.

## Implemented and changed files

- `services/pool_research/daemon_job_source.py`: bounded localhost JSON-RPC allowlist for `get_info`, `get_block_header_by_height`, `get_block_template`; no proxy or redirect; no generic method selection. Pin genesis/network type, ensure synced tip, request eight OS-generated nonce bytes via the daemon's `extra_nonce` field, verify reserved coinbase location, header, parent/height, and tip before and after issuing a template. Enforce worker assignment, expiry, u32 share difficulty, job capacity, native claimed-digest comparison, and stale-tip rejection before and after hashing. Exposes only Stratum-shaped `rx/0` job *data*. No automatic session refresh, block submission, rewards, or payout code.
- `services/pool_research/test_daemon_job_source.py`: 12 offline cases covering network/genesis mismatch, unsynchronized nodes, reserved bytes, cross-worker isolation, distinct native hashing jobs, RPC injection/shape rejection, expiry, nonce duplication, digest mismatch, low difficulty, a fork during native hashing, and the u32 target bound. Test fixtures model a varying coinbase-derived merkle root.
- `services/pool_research/tests/run_daemon_job_native_offline.py`: separately invoked, real persistent C++ RandomX digest checks against a known reference vector and a fixture daemon's per-worker job. No network or wallet access in the runner.
- `services/pool_research/README.md`: research-only boundaries and validation instructions.

**Protocol caveats:** This is a single-process research object with bounded jobs, not a concurrent Stratum pool. A failed verifier may consume a nonce in the in-memory preflight. The returned status is always `POW_THRESHOLD_MET_UNCREDITED`, never financial or network block acceptance. The primary signer/payout RPC remains disconnected.

## Executed tests and actual results

- Windows x64, Python 3.13: `python -m unittest discover -s services/pool_research -t . -q`: **127 tests run, 123 passed, 4 skipped, no failures**. The platform skips are from the earlier fixture suite.
- Native worker: compiled `services/pool_research/tests/randomx_worker.cpp` with MSYS2 g++ 16.2 and the existing native RandomX static library from the owner's original separate build tree. The initial CLI launch failed without the dynamic MSYS2 runtime on `PATH`; with the reviewed MSYS2 `mingw64/bin` directory added, the worker emitted reference digest `294083824fec5947ef2cd825e2bedcb34789e4cc6ad12d7823bcf0be51178f77` for the established seed/76-byte vector.
- `python -m services.pool_research.tests.run_daemon_job_native_offline --executable PATH`: **passed** the native reference hash, a worker-bound nonce verification, and duplicate nonce rejection; always **uncredited**.
- **Disposable actual daemon integration**: On a new empty, offline node directory and private loopback RPC ports, used an existing authorized disposable wallet address (never logged) to request a real ForgeCoin block template with `extra_nonce`. Daemon reported height **1**, network difficulty **500,000**, 76-byte RandomX hashing blob, and a validated worker job. Compiled native RandomX worker independently recomputed the claimed nonce and `DaemonJobSource.inspect` returned `POW_THRESHOLD_MET_UNCREDITED` with a matching digest. The candidate daemon process stopped after the probe; it returned exit code **1** on the scripted shutdown. No block submitted, no mining search, no reward credited. Because the expected genesis hash was read from this same disposable daemon for the experiment, the test is **not** independent chain-identity validation. The executable came from an earlier isolated consensus candidate build, not a reproducible release of this exact main commit.
- `git diff --cached --check`: passed before implementation commit. No changes to the user's live chain or original local work tree.

## Outstanding launch blockers — not solved in this step

1. Replace synthetic-only Stratum listener with a private *real-template* worker lifecycle and bounded job rotation. Test two independent actual XMRig instances for accepted/rejected/stale/replayed shares; the current source is **not** a public pool.
2. Verify native daemon `submit_block` end-to-end **only on a disposable isolated test network**, including block-template full serialization, canonical chain tracking, accepted-block evidence, invalid block rejection, chain reorganizations and restart/maturity. The present code **never** submits a block.
3. Integrate a ledger of **durably verified canonical shares and mature rewards**, choose/ratify PPLNS/other scheme, exactly specify a 1% optional operator fee, and verify crash-safe signed payouts. No pool wallet signing code exists.
4. Validate official pool and desktop custom pool with XMRig from clean Windows installs, 100-worker capacity targets, Linux/ARM64, network-specific genesis and difficulty, and security isolation. The current test did not load-test sockets.
5. Complete pool website/dashboard, explorer runtime, HTTPS, operating manual, independent reviews and release artifacts.
6. Diagnose the isolated daemon scripted exit-code **1**, and independently pin the mainnet network identity instead of reading it from the tested daemon.
7. Actual production deployment, pool payout custody and FRG mainnet launch are **not authorized by this research commit**.

**Next concrete step:** integrate daemon-bound job issuing and share verification into an isolated, loopback-only Stratum test service with XMRig-driven native proof-of-work (still no credits or block submission). Maintain the same fail-closed RPC/identity checks and record separate test evidence. Do not merge and advertise a pool until genuine block acceptance and payout maturity are independently demonstrated.
