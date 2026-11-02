# ForgeCoin: XMRig-derived native block acceptance (disposable chain)

**Date:** 2026-10-27. **Status:** observed PASS on source-matched local test
artifacts. This is **not** a production pool launch, a mainnet block, or a
payout test.

## What was exercised

1. `capture_isolated_native_template.ps1 -SubmitMinerDerivedBlock` launched a
   fresh `forged.exe` with `--offline`, an empty data directory and loopback
   ports **49980–49982**, then captured the genuine height-1, difficulty-1
   `get_block_template` response to a private LocalAppData directory.
2. `run_isolated_xmrig_native_template.sh` verified the pinned XMRig and
   RandomX worker SHA-256 hashes and launched the client **unprivileged** in a
   Linux network namespace with loopback as its only interface and no external
   route or capabilities.
3. `run_xmrig_native_template.py` changed the eight-byte coinbase reservation,
   computed a correct matching transaction-tree root, and issued the resulting
   native `rx/0` job to the **actual XMRig v6.26.0 client**.
4. XMRig submitted a nonce and digest. `IsolatedMinerJob` checked its
   session-bound job, independently recomputed RandomX using the pinned native
   worker, checked the claimed digest and network target, then reconstructed
   the full block with the submitted nonce and reservation. The new candidate
   was written only to a private file, with `credited=false`.
5. A separately compiled source-matched C++ consensus helper independently
   reconstructed the miner-transaction extra and CryptoNote tree root. The
   Python candidate and C++ native serialization/hashing results agreed.
6. **Only then**, the PowerShell wrapper submitted that full block to its
   own disposable daemon. The daemon returned `status=OK`; its canonical
   height advanced from 1 to 2, with block hash:

   `9d0969e1846e14f6c04439ef82a2726a9980313cc4b38c8a266c94d7347b208a`

   The wrapper terminated the isolated daemon and left no test service running.

## Reproducibility and provenance

- Local source-matched `forged.exe` SHA-256:
  `600a76d02fbf9f46825ca989daf1c74187aa3bf524d651c35cfe6fbbc1fd2836`
- Pinned XMRig v6.26.0: `b2ca72480c58d197e18c885d9fc1a0c8d517e60a`;
  Linux test executable SHA-256:
  `391f766cadc49f4cb349e680b363994147af54651235fb51d5b1219f33fbd24e`
- Linux native RandomX test worker SHA-256:
  `5be16e696e17f6214c07243522672d905945ec01990b5baa0b29e0e8a363a77b`
- Windows native consensus reconstruction helper SHA-256:
  `C7968C748DECA79D546E8D2D14DBD8BAC7776927B38567E3F3C405B0A46D20A4`
- Template, candidate and daemon logs stay under private
  `%LOCALAPPDATA%\ForgeCoin\IsolatedTemplateCaptures\<unique-run-id>` and
  are **not committed**. The wallet used was the previously documented
  disposable **legacy-prefix90** test wallet. No keys or recovery phrase
  reached a miner or RPC.
- Run the PowerShell capture script explicitly with a trusted disposable
  wallet address file and `-SubmitMinerDerivedBlock -PortBase 49980`.
  The WSL `ForgeCoinBuild` image and the pinned local binaries are required.
- Regression test result: **116 tests run, 112 passed, 4 skipped** across 23
  `services.pool_research.test_*` modules (Python unittest).
- A genuine miner may submit nonce `00000000` at difficulty 1. The independent
  native verifier initially rejected that valid case because its helper
  required the nonce to differ from the original template. Fixed by
  `apply_miner_nonce`, with a dedicated regression case; the fresh-chain
  submission then passed.

## Non-claims and remaining gates

This test checks a **single-worker, single-transaction, difficulty-1**, new
offline chain. It is not an end-to-end test of the production mining pool.
It does **not** test real network difficulty, sustained mining, concurrent
worker sessions, stale/reorg share races, authenticated production Stratum,
arbitrary multi-transaction blocks, nontrivial coinbase/merkle variants,
reward maturity, fee accounting, PPLNS, signed payouts, or reconciliation.
The source-network identity and proposed address-prefix change remain
separate release blockers.

Do not turn on production mining or use the disposable wallet as a mainnet
receiving wallet on the strength of this test.
