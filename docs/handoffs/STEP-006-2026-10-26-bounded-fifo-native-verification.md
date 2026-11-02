# STEP-006 — 2026-10-26 — bounded FIFO native RandomX verification

## Repository, branch and actual implementation

- **Scope:** original `tgibbsz32/forgecoin` native FRG pool. No FCMP/CARROT, Solana, live network, treasury or production wallet work.
- Existing research PR: #105, branch `feat/pool-xmrig-loopback-20261025`; starting commit `944ee49a8992fa076a0db281137a9a941049e618` after Step 005.
- **Implementation commit:** `996126b37259121c961168d303255f5eca16b76d`.
- Files:
  - `services/pool_research/native_verification_queue.py` — bounded asynchronous FIFO and **one serial native RandomX helper**, max pending queue length 1–8, per-claim timeout, cancellation skipping, queue overflow rejection, cleanup. Each socket's request handler awaits its own pending share and therefore cannot flood the verifier with unlimited work.
  - `services/pool_research/native_stratum_research.py` — sends worker jobs through the FIFO instead of immediately rejecting the second concurrently hashing miner. Verifier work occurs off the event loop; all successful results remain **`POW_THRESHOLD_MET_UNCREDITED`**, no block submitted.
  - `services/pool_research/test_native_verification_queue.py` — four focused async tests for FIFO fairness across three competing sessions, queue overload, canceled pending work never reaching native hashing, and closed queue rejection.
  - `services/pool_research/test_native_stratum_research.py` — updated actual socket test proving a waiting second miner eventually verifies after a deliberately blocked first worker instead of receiving `busy`.
  - `services/pool_research/README.md` — implementation limitations, run instructions and actual observed metrics.

## Executed test evidence

- `python -m unittest services.pool_research.test_native_verification_queue services.pool_research.test_native_stratum_research -v`: **12 tests passed**, no errors.
- `python -m unittest discover -s services/pool_research -t . -q` on Windows Python 3.13: **140 tests run, 136 passed, 4 platform-dependent skips, zero failures**.
- Re-ran the actual Step 005 two-XMRig executable integration: fresh temporary `forged.exe --offline` node/data directory, two XMRig 6.26.0 processes (1 CPU thread each), native C++ RandomX verifier and loopback-only Stratum service. Over a bounded **24-second** test at difficulty 30, **2/2 miners generated independently native-verified shares, 98 submissions verified and 0 busy rejections**. Compared with Step 005's similarly bounded previous listener (**59 verified, 19 busy rejections**). This is a small-load observed difference, not a controlled throughput benchmark or production fairness proof.
- Test script reported `DISPOSABLE_DAEMON_STOPPED True` and `STEP006_CONCURRENT_XMRIG_SUCCESS`; no blocks were submitted or credited. The candidate daemon and tool binaries were inherited from earlier research (SHA-256 fingerprints in Step 005), **not** rebuilt reproducibly from current `main`.
- `git diff --cached --check` passed before implementation commit. The user's original local consensus worktree was not edited.

## Security constraints and unfulfilled release gates

- The queue remains **in-memory and single process**, with at most eight pending items plus one native verification in progress. Although FIFO prevents immediate busy drops in a two-miner run, the underlying C++ verifier remains serial and its subprocess/OS isolation has not received security review. A worker whose queued request times out is never credited, but CPU work already started in a thread may run to completion after cancellation. This is intentionally **not** a production isolation boundary.
- The listener is bound to `127.0.0.1` on a random ephemeral port. Authentication is a temporary session identity, not verified ownership of a native FRG payout address. No pool share-credit ledger, pool wallet, reward accounting or payout signer is connected.
- **No proactive miner-job refresh** on new tips/seeds/reorgs or on job expiry; miners must reconnect. No 100-worker load or Linux/ARM64 verification, canonical accepted block, network seed/identity attestation, maturity/PPLNS or robust restart/reorg support.
- Not an official deployable mining pool. Do not merge into production or credit any participant based on these research submissions.

**Next concrete step:** implement bounded per-session, daemon-tip-validated native job renewals with stale job rejection and XMRig-compatible `method: job` pushes; test a simulated network tip change and a real isolated miner reconnect/refresh. Then gate full serialized candidate-block validation and disposable `submit_block` under explicit isolated test protections, followed by crash-safe canonical share accounting and mature payouts. Number and commit each subsequent handoff.
