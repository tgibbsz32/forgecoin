# Isolated native fresh-mainnet mining recheck â€” 2026-10-23

Read-only production scope; newly cloned local LMDB for test mining, no Oracle/live dev chain access.

- Test source: archived `isolated-fresh-mainnet-smoke/data` cloned into separate `isolated-height16-recheck-20261023/data`. Preserved archived original.
- Native Windows candidate binary: archived `builds/consensus-candidate-win64/bin/forged.exe` (preexisting candidate, not a fresh compile).
- Runtime: `--offline`, loopback P2P `39580`, RPC `39581`, `--no-zmq`; six CPU mining threads. No fixed-difficulty bypass.
- START: RPC height **8**, next difficulty **500000**, tip `783797eb386fd65f0d069b434a7838ab55e3535d97b21cf851b713c30b6091e4`.
- Mining RPC result: `OK`.
- Accepted block: RPC height **9**, next difficulty **500000**, tip `645fd0e92e4529731da52d0571fd55d7a81e3c3787fad1fa347b135033221dad`.
- Accepted block: RPC height **10**, next difficulty **500000**, tip `67e75b730e3982a69b4929845681d0981400b42e6764edd7e35971645931907b`.
- FINAL: RPC height **10**, next difficulty **500000**; test reported `TEST_STOPPED` and exit **0**.

**Important limitations:** Bounded mining did **not** reach consensus height 16; no startup-to-progressive-LWMA acceptance was tested. No actual fork competition or ARM64 cross-check occurred. The test regenerated no production chain data and did not change source or consensus parameters. Genesis spendability is still unverified.

Test script and log copy retained in local archived workspace's `isolated-height16-recheck-20261023` directory. Do not mistake this report for a mainnet release approval.
## Continued bounded mining — 2026-10-23

A second local offline run resumed the preserved disposable candidate chain from **RPC height 10** using the existing archived Windows candidate daemon and six CPU mining threads. It used `127.0.0.1:39581` RPC, loopback P2P port `39580`, `--offline`, `--no-zmq`, and no fixed-difficulty override.

- Start: height **10**, next difficulty **500000**, hash `67e75b730e3982a69b4929845681d0981400b42e6764edd7e35971645931907b`.
- Mining command: `OK`.
- One accepted new block: height **11**, next difficulty **500000**, hash `ab6fc7301a8fd95ae557d9a86f4babed723497ad1e5e1d62671083fa882d2edf`.
- Final: height **11**, exit **0**, daemon stopped via script's `finally` block.

**Not passed:** chain height 16 transition, full-window LWMA, genuine divergent-branch reorg, ARM64 agreement. No production/network changes; local isolated database retained as checkpoint.

## Native startup-to-LWMA boundary — 2026-10-23

This isolated offline Windows candidate was resumed from the preserved local checkpoint using the existing candidate `forged.exe` (no rebuild), native six-thread RandomX mining, loopback P2P/RPC 39580/39581, and no fixed-difficulty override. The daemon mined from RPC height 11 to 15 in one bounded run and was stopped (exit 0). It then resumed at height 15 and successfully crossed the difficulty boundary.

- At RPC height 15, next-block difficulty remained **500000**, tip `71e9293a2f1c20ee859e4c69fa72f56db78019a5067c7310dfdf916555828580`.
- At RPC height 16, **next-block difficulty became 400000**, tip `29026cf0805b1005a53d7452f34574584808b569b2dc9fbbed88803aa2c01952`.
- The next mined block was **accepted at RPC height 17**, new next-block difficulty **400000**, tip `c07de734589d73a92a018ae722a5056ca2323654f49b8294d0ee89709b8b8dfa`.
- Test emitted `TRANSITION_MINED_AND_ACCEPTED`, `TEST_STOPPED` and **exit code 0**; daemon process was stopped.
- Unlike a synthetic constant-interval test yielding 495000 at height 16, observed mined-block timestamps drove the real candidate to the **400000 floor**. The observation does not independently prove all timestamp and difficulty formulas correct.

**New evidence:** Real candidate block mining crossed the first progressive-LWMA boundary, and a subsequent block was accepted using the post-transition difficulty on isolated Windows x64. **Still untested:** full-window 90-92, malicious timestamps, truly competing PoW branch and reorganization, ARM64 consensus agreement at height 16-17, and genesis spendability. Not a public-mainnet release signoff.
