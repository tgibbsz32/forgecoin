> **Historical archive — superseded for current configuration.** Original evidence and decisions below retain their original dates and network parameters. Do not use old ports, genesis, balances, token proposals or release claims as current instructions. See [current mainnet specification](../CURRENT_MAINNET.md) and the current roadmap.

# STEP-003 — 2026-10-25 — local native-template Stratum research socket

## Scope

- Active repo: `tgibbsz32/forgecoin` (original FRG, **not** the separate FCMP/CARROT repo).
- Branch: `feat/pool-native-job-boundary-20261025`; existing draft PR #104.
- Depends on Step 002 native daemon-template job issuer (implementation `7aba00fd19d66c1397b09461a855e5795db784c8`, handoff `686efe1818d72d79065d17daf73989c9d94c0e59`).
- **Implementation commit:** `eaa88fb58aef0c6dcfed357caf04b1fe179b8281`.
- No original project user working tree, unrelated worktrees, live network, treasury or pool payout service modified.

## Changes actually implemented

- `services/pool_research/native_stratum_research.py`: bounded TCP listener only on `127.0.0.1` and ephemeral port. JSON-RPC `login` + `submit` + `keepalived` frames are checked by the existing strict session validator. Every worker gets its own `DaemonJobSource` instance and daemon-produced coinbase `extra_nonce` from Step 002. The listener verifies session/job binding, real supplied RandomX digest, duplicate/stale failures and caps active sockets at eight research sessions. It serializes native verifier use by immediately rejecting extra requests while busy. Responses explicitly say **uncredited and no block submitted**.
- `services/pool_research/test_native_stratum_research.py`: 8 socket-level asyncio tests: login, native callback, duplicate, foreign job, stale chain tip, bad digest, wrong-network refusal, invalid algorithms/methods, busy verifier, bounded connections and oversized frames. Uses a fake daemon and deterministic digest callbacks; does **not** establish public miner compatibility.
- `services/pool_research/tests/run_native_stratum_socket_offline.py`: separately runnable loopback TCP round trip with actual native C++ RandomX worker, from login through nonce submission and replay rejection, while using a fake daemon. No funds or chain submission.
- `services/pool_research/README.md`: new research-only integration instructions and explicit limitations.

## Tests performed

- Windows/Python 3.13: `python -m unittest services.pool_research.test_native_stratum_research -v` → **8 passed**, 0 failed.
- `python -m unittest discover -s services/pool_research -t . -q` → **135 tests run, 131 passed, 4 skipped, no failures**.
- Native worker: MSYS2 C++ RandomX helper compiled in Step 002 against an existing fork library, with MSYS2 runtime on `PATH`. `python -m services.pool_research.tests.run_native_stratum_socket_offline --executable PATH` → **pass** for a genuine native RandomX digest over a real localhost Stratum-shaped TCP connection; repeat nonce was rejected and no block/credit was reported.
- `git diff --cached --check` → passed before the implementation commit.
- No external XMRig binary was connected. No production network ports, mining RPC, block-submission or wallet RPC were used.

## Limits and blockers

This is **not** an official mining pool. The listener has no production endpoint, TLS, authentication tied to payout ownership, automatic job broadcasts/difficulty adjustments, client address verification, chain accepted-block checks, durable verified shares, round accounting, PPLNS, 1% fee settlement or payout signing. Four local capacity connections by default (up to eight) do not establish the 100-worker performance target. Every result is intentionally uncredited.

A worker whose template is stale must reconnect; proactive rotating miner job lifecycle is still missing. The synthetic daemon fixture cannot attest real native network identity or solve replay across processes. The research adapter has no independent production security audit. Real native C++ digest verification alone is not a successful network block or monetary obligation.

**Next step:** use a fresh isolated offline ForgeCoin daemon and a genuine XMRig binary to test actual Stratum job acceptance, difficulty target encoding, supported RandomX seed, invalid/stale share handling and connection rotation; independently review a safe candidate block serialization/submission path before even disposable accepted-block tests. Then implement reorg-safe durable share credits and auditable mature payouts. Do not open a public endpoint or declare this service production-ready.
