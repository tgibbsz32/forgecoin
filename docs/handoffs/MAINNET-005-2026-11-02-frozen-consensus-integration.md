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

## Historical block replay fixture

The QA workstation retained a pre-guard *isolated* MAINNET-identity chain with an accepted height-1 block, and the original Windows daemon binary previously matched SHA-256 `3efaf014c7fdfcea167630f1884abee2defd40f28f1e725b6c0a8fcede5b5c37`. On November 2, a disposable LMDB **copy** was opened through localhost RPC using that prior binary; `get_block` exported the serialized public block. The untouched original QA database was not modified for export and no wallet file, seed or private key was included. The block was independently checked via height/hash/parent/reward/difficulty header queries.

- Fixture: `tests/mainnet/fixtures/isolated_20261026_block1.json`
- Previously accepted block hash: `9755a4f129f97b7865e5897e79abf5fea89dec2ba776d53fb9d01942b9f7ba9e`
- Genesis parent: `4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c`
- Recorded difficulty: `500000`; reward: `2384185222` atomic FRG; serialized length: 124 bytes
- Serialized block SHA-256: `9031680cf33d31fa484033ee1f0a23ceaab390e5f5004b0149a263b37efcc4d8`

The isolated daemon smoke test now submits this **historically accepted, correctly formatted block** to a fresh prelaunch-locked genesis-only daemon. The expected result is the RPC error `Block not accepted` and a chain remaining at height 1; an error claiming the payload is malformed does **not** satisfy the gate. This is a meaningful main-chain rejection check but does not test alternative forks, real coinbase spending rings, reorgs, payout maturity, or public synchronization. The revised CI job must pass before claiming this runtime behavior is verified.

**Source of truth:** draft PR #185, branch `integration/frozen-mainnet-prelaunch-20261102`. Merge into main only after the full runtime and consensus acceptance requirements are met; never bypass the lock to make the public chain accept this old test block.

## Native difficulty transition regression (November 2 continuation)

`tests/mainnet/frozen_difficulty_policy.cpp` compiles and runs the *real* `src/cryptonote_basic/forgecoin_difficulty.h` code, linked only to a sentinel for the preexisting non-mainnet `next_difficulty` function. It does not run PoW or modify blockchain data.

- Height 1–15: fixed 500000 independent of ancestor data.
- Height 16: progressive LWMA starts using 15 ancestor intervals; at 120-second spacing and 500000 historical work, expected difficulty 495000 (the intentional 0.99 bias).
- Heights 17, 32, 90, 91, 92 and 150: at matching 120-second intervals, expected 495000; height 91 and beyond exercise the full 90-interval suffix.
- 30-second solves: expected 1980000; 480-second solves: floor to 400000.
- Missing history, mismatched vector sizes, wrong target, invalid or non-growing cumulative work, and invalid height reject with zero. Timestamp normalization and the non-mainnet passthrough are also tested.
- C++17 with `-pedantic -Wall -Wextra -Werror` was compiled and run on `ForgeCoinBuild` Linux WSL: **PASS**.
- CI now independently compiles and runs this executable on Ubuntu for every integration push and PR. Its CI result must be confirmed separately.

This regression increases numerical coverage, **but it is not proof of an actual multi-node synchronized 90+ block chain**. The launch-lock build intentionally cannot mine such a chain; a separately reviewed disposable test-enabled binary and independent consensus tests are required before unlocking public network mining. No change to the agreed frozen consensus parameters was made.

## Mainnet fixed-difficulty override hardening

Code review identified an inherited daemon `--fixed-difficulty` testing option that could reach `Blockchain::init` while the network type is MAINNET. Nonzero fixed difficulty bypasses the normal height-based difficulty selector. It must not be accepted on real FRG MAINNET, including once the separate prelaunch mining lock is lifted.

A new fail-closed `core::init` check refuses `--fixed-difficulty` when `m_nettype == MAINNET` and the requested value is nonzero, **before** blockchain storage initializes. Existing FAKECHAIN/test-network behavior is unchanged. The source regression verifies this ordering, and the isolated daemon smoke starts a second loopback-only disposable process using `--fixed-difficulty 1`. It requires a nonzero exit and the explicit native error `Mainnet consensus forbids --fixed-difficulty`. A mere parse error or unrelated failed start is not sufficient.

The local Dell test run passed 8 mainnet source tests and 24 native pool source tests, and Python syntax checks passed. The new full daemon build and runtime denial must independently pass CI before this safeguard is considered verified.

### Independent difficulty-test CI dependencies

The numerical `frozen_difficulty_policy.cpp` test passed in the WSL ForgeCoinBuild environment. Clean GitHub policy runners first lacked Boost multiprecision headers, then libsodium crypto headers; both are needed by the actual production `cryptonote_basic/difficulty.h` header dependency chain. The policy CI explicitly installs `libboost-dev` and `libsodium-dev` prior to compiling the native regression. These initial CI failures are build-environment dependencies, not a change to the frozen difficulty parameters. Check the latest run for confirmation.

## Previously mined height-2 LMDB rejection gate

The earlier 20261026 Windows native block QA preserved a valid public chain with genesis at height 0 and one accepted block at height 1. A new CI fixture was built by compressing **only** `node-0/lmdb/data.mdb` from that offline experiment; the original database remained untouched. The fixture is **2,613 bytes** (`tests/mainnet/fixtures/pre_guard_20261026_height2_data.mdb.gz`) and extracts to 126,976 bytes. It contains public chain state, **not** wallet files, keys, RPC certificates, node logs, or signing material. The adjacent JSON metadata pins frozen genesis hash, accepted block hash, chain height, compressed/uncompressed byte counts, and SHA-256 checksums.

The updated `tools/smoke_frozen_prelaunch_daemon.py` now has a third independent runtime phase: verify both fixture digests, extract the old database into a fresh temporary directory, start the newly built Linux daemon with mainnet identity and offline/localhost-only flags, and require both a nonzero exit and the exact `PRELAUNCH: refusing a mainnet database containing blocks beyond genesis` error. A generic LMDB parser error does not satisfy the test. The daemon cannot join a public network or touch the original QA database. This supplements the successful previously accepted block-replay rejection.

Read-only QA regression `tools/inspect_local_full_block_qa.py` was also repaired: an inner `import sys` shadowed module-level `sys` before the daemon could start. After removing it, the historical binary's read-only RPC inspection returned the original height-1 block hash, difficulty 500000, reward 2384185222 atomic units, and succeeded with `ReadOnlyRPCVerifier` against the native node (no wallet RPC, mining, or payment).

At the time this gate was authored, **9 mainnet source/fixture tests, 24 pool source tests, 45 settlement tests and Python syntax checks passed locally.** The new height-2 database rejection requires independent GitHub CI runtime confirmation before claiming an acceptance pass. This test does not establish genesis ring-spend rejection, multi-node reorg agreement, mature pool payouts, or release authorization.

## Genesis-output provenance against native LMDB (read-only QA)

The existing historical Windows daemon verifier was extended to call its native `/get_outs` JSON RPC for the genesis output amount `1192092895` atomic FRG at output index zero. The returned public output record reported `height=0`, verifying that the database's `output_data_t.height` field uses the intended height-zero value. The verifier also passed its independent height-1 block/difficulty/hash inspection and read-only pool canonicality observer. No wallet key, mining action, publicly exposed port, or production data directory was used.

This provides concrete provenance for the proposed mainnet `forgecoin_prelaunch::output_allowed(mainnet, creation_height)` exclusion in `scan_outputkeys_for_indexes`. It does NOT constitute an adversarial spend proof; independent crafted ring/input validation, bypass-path audit and reorg tests remain required before authorizing launch.

## Genesis ring-member regression (2026-11-02, 04:xx America/New_York)

`tests/mainnet/genesis_ring_policy.cpp` executes the **exact same production C++ predicate**, `forgecoin_prelaunch::output_allowed(mainnet, creation_height)`, used in the native blockchain's output-resolution scanner. It constructs output-creation-height arrays of 1, 2, 11, 16, 64 and 256 members; for **each** position it inserts the known genesis height 0 and asserts MAINNET rejects the ring (including when genesis is only a decoy). It verifies non-genesis heights and other networks are unaffected. This explicitly tests consensus policy independent of maturity time.

The companion Python source regression `test_genesis_output_rejected_in_cached_and_direct_ring_scan` checks both cached output resolution and direct LMDB fallback in `scan_outputkeys_for_indexes`, then verifies the per-member height-zero exclusion occurs **before** `vis.handle_output`, which feeds the ring-signature code. The native historical `/get_outs` inspection already confirmed that the real frozen genesis output is assigned height 0 in LMDB.

Local evidence: C++17 native policy compiled/runs with warnings as errors on ForgeCoinBuild WSL; 10 mainnet source/fixture tests, 24 official-pool source tests and 45 settlement journal tests passed. The source integration's Ubuntu CI now runs the native C++ ring test. Its updated CI pass is to be verified separately.

**Security boundary:** This is a native predicate + source-path test, **not** an actual signed genesis-output transaction injected into a fully mature 60+ block chain. It cannot prove that alternative transaction serialization/verification routes, checkpoints, or RPCs cannot bypass the exclusion. An adversarial spend/decoy transaction and native full-path validation remain mandatory before launch. The height-2 database rejection was independently confirmed in the earlier [GitHub CI 41417150053](https://github.com/tgibbsz32/forgecoin/actions/runs/41417150053).

## Two-node mainnet P2P handshake regression (2026-11-02)

The native CI daemon build now runs `tools/smoke_frozen_prelaunch_peers.py` after its existing locked-genesis, historical block submission, old database, and fixed-difficulty tests. The new test creates **two entirely fresh temporary LMDB directories** on an isolated Linux runner. Both daemons run the *real frozen MAINNET identity* with P2P/RPC explicitly bound to `127.0.0.1`, random loopback ports, no ZMQ, no IGD, DNS checkpoints disabled, and update checking disabled. Node A has `--out-peers 0`; node B has **one exclusive peer** `127.0.0.1:<A-p2p-port>`, `--out-peers 1`, `--in-peers 0`. Neither process starts mining or has a wallet.

The test checks native `get_info` on both nodes (MAINNET, height=1), node A's incoming peer count and node B's outgoing peer count, their identical frozen hash and genesis nonce, and that no unexpected in/out peer counts appear. It submits the already proven real, pre-guard height-1 mined block to node A, demands the *specific* native `Block not accepted` error, and verifies both nodes remain at height=1 after a short propagation window. All spawned daemons are stopped and temporary chain data cleaned, including on failure. Running this test does **not** unlock the native mainnet miner or start production infrastructure.

**Claim limit:** A successful test establishes 2-node loopback P2P handshake/identity and rejection of one known mined block under the prelaunch lock. It does **not** demonstrate synchronization of a valid post-genesis chain, reorg behavior, interop with Oracle, or settlement/payout safety. The locked build intentionally cannot produce blocks; those require a separate controlled test network. The GitHub CI result for this test must be checked before claiming it passed.

## Native ARM64 independent consensus acceptance

A separate `.github/workflows/frozen-mainnet-arm64-consensus-ci.yml` job runs on GitHub's native `ubuntu-24.04-arm` AArch64 runner, using a different architecture and OS distribution than the already-green x86_64 daemon acceptance. The job verifies `uname -m=aarch64`, frozen 20261026 genesis, assigned P2P/RPC/ZMQ 39480/39481/39482, and fail-closed prelaunch/payout/Stratum flags. It compiles and executes production C++ genesis membership, prelaunch policy and LWMA90 numeric regression vectors with warnings as errors.

The next gates compile/link the real native `forged` AArch64 executable (separate temporary CI build tree, **not** the Android executable), verify native ELF/ldd fingerprints, run the existing isolated daemon/startup/historical-block/retired-chain/fixed-difficulty refusal checks, then two real AArch64 daemons connected only over loopback refusing the known preguard height-1 block. No mining/payout is authorized, no usable APK sidecar is produced, no release/upload is done, and no public node is connected. This is an independent **CPU-architecture and consensus-path confidence test**, not proof of Android Bionic ABI compatibility or signed genesis output spending.

ARM64 CI must pass before marking this gate verified; [GitHub Actions ARM64 run 41458111738](https://github.com/tgibbsz32/forgecoin/actions/runs/41458111738) was queued at creation. Native x86_64 validation already passed in [run 41450727192](https://github.com/tgibbsz32/forgecoin/actions/runs/41450727192). Independent post-genesis signing/reorg and payout acceptance remain mandatory launch gates.
