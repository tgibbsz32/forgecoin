# MAINNET-005 — frozen 20261026 consensus integration candidate (2026-11-02)

**Status:** isolated source integration in progress, not an approved release. The owner reserves the first public solo-mined FRG block. Public mining, Stratum, payout signing, and Oracle chain activation remain DISABLED.

## Recovery and provenance

This integration branch starts at main commit `1046255e1c99bc4f9579ea763ad61d2ed7bf5d0e` after the pool safety/preservation changes. It imports the frozen identity, startup difficulty logic, timestamp and alternative-chain history handling, and v19-at-height-1 hardfork schedule from PR #111, then layers the prelaunch core, miner, blockchain and genesis-output guards from draft PR #116. Files not required for native consensus are deliberately NOT copied from old PR #111 to avoid overwriting newer Windows wallet, pool and website developments.

Frozen identity: native mainnet nonce `20261026`, expected genesis hash `4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c`, prefixes `190/191/192`, P2P/RPC/ZMQ `39480/39481/39482`, RandomX 120s, first mined-block difficulty 500000, minimum 400000, fixed startup through height 15 and variable-window LWMA beginning at height 16.

## Explicit prelaunch locking

- Mainnet block templates are denied by core APIs; the native miner refuses to start on MAINNET.
- Both the main-chain and alternative-chain block acceptance paths deny any incoming mined mainnet block while the prelaunch policy is active.
- Existing mainnet chain data past genesis is rejected at initialization.
- The transaction input ring scanner rejects references to outputs created at height zero, independently of normal coinbase maturity. This is a consensus policy proposal that still requires independent review and genuine spending/witness tests to establish the intended permanently unspendable genesis output.
- The JSON manifest retains `release_authorized=false`, `consensus_guard_stage=draft-unbuilt`, `pool.payouts_enabled=false`, and `pool.stratum_public=false`. A JSON edit alone cannot override the compiled lock.

The prelaunch compilation intentionally makes the previously observed isolated height-1 mining acceptance impossible on this integration build. Those earlier test results were on an **older candidate binary**, not an authorized live network.

## Local evidence

Source-level tests on this isolated worktree: 7 frozen consensus/prelaunch tests PASS, 24 pool source tests PASS, and 45 synthetic settlement journal tests PASS. The standalone C++ policy `tests/mainnet/prelaunch_policy.cpp` compiled and ran on `ForgeCoinBuild` WSL with warnings as errors. These checks do NOT prove the full daemon compiles or that a native node will reject hostile blocks after startup.

The original local checkout is Windows Git sparse-checkout and lacked multiple upstream headers. Only the isolated integration worktree was expanded to the complete tracked tree. No work in another checkout was overwritten.

## Required before merge into main

1. GitHub CI must compile/link the **entire** native `forged` executable from the integrated source; source/wiring and C++ policy checks alone are insufficient.
2. Conduct a disposable genesis-only daemon startup with frozen hash/identity, attempt `start_mining`, `get_block_template`, `submit_block`, alternative blocks, and reject a pre-existing height-2 database.
3. Audit the permanent genesis-output exclusion against every spend validation path and independently test forged spends/rings. A maturity lock is **not** a cryptographic burn.
4. Validate new-mainnet height 1–17 difficulty transitions, LWMA90 behavior near heights 90–92, reorg and network synchronization in a **separately controlled test-enabled build**, never by overriding the proposed release lock in production.
5. Reconcile the full desktop/Android/explorer/pool/Oracle integration, wallet identity and payout acceptance separately. PR #111's older broad UI tests remain on that draft; they are not imported as passing consensus tests here.

Keep production deployment unauthorized until these gates are met. Do not change the frozen genesis, launch configuration or production wallets to manufacture green tests.

## New offline genesis RPC acceptance gate (2026-11-02)

The original PR #185 native x86_64 daemon compile/link CI passed (run [41400808001](https://github.com/tgibbsz32/forgecoin/actions/runs/41400808001)); ARM64 and x86_64 pool link CI also passed. This proves binary compilation but not correct behavior at genesis.

The integration now includes `tools/smoke_frozen_prelaunch_daemon.py` and a post-build runner step. The script refuses any manifest that enables mainnet release, pool payouts, public Stratum, or prelaunch mining. It launches the linked `forged` on fresh disposable data, with offline mode, no ZMQ, loopback-only P2P/RPC, randomly chosen localhost ports and bounded process lifetime. It reads `get_info` and genesis `get_block_header_by_height` and asserts frozen hash/nonce/height, calls `getblocktemplate` and `start_mining` without expecting success, verifies the chain still has only genesis, and always terminates the process.

**Evidence is pending for the new runtime smoke until its revised CI run completes.** RPC failure alone is not proof of hostile, fully valid submitted blocks being rejected, and this smoke does not test alternative branches, real mining, coinbase spend exclusions, persistence or payout maturity. Those remain mandatory integration gates.
