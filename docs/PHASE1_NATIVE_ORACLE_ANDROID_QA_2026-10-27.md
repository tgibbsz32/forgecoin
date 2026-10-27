# ForgeCoin Phase 1 integration verification — 2026-10-27

**Engineering verification of a disposable OFFLINE mainnet-identity QA chain, not a public mining launch.** This document records observed tests, their scope and what remains incomplete. The intended first **public** solo-mined mainnet block is reserved for the network operator.

## Versions, topology and safeguards

- Source: feat/fresh-mainnet-identity-and-integration-gates-20261026 at 62fc0b875431d7fa64f887bb20b7b51d67abcdfa, with unmerged fixes from draft PR #119.
- Oracle ARM64 VM: Ubuntu, four Ampere CPU cores, 11 GiB RAM. QA daemon + native C pool + wallet RPC all bind **127.0.0.1 only**. Daemon uses --offline with a disposable empty LMDB. No public P2P, Stratum, daemon RPC or wallet RPC listener is enabled.
- Frozen native genesis nonce: 20261026; hash: 4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c. RPC port 39481; P2P port 39480; initial actual next-block difficulty 500,000; 120-second block target.
- Generated disposable QA wallet by forge-wallet-cli, with restricted storage and a separate password file; mnemonic and password were never printed to the tool output. **Never use this wallet for production deposits or operator fees.**
- QA Stratum binds 127.0.0.1:49442; QA aggregate stats on 127.0.0.1:49443; wallet RPC QA on 127.0.0.1:39483. Payouts permanently disabled in this research build; fee 1%; native RandomX share verification ENABLED.
- Pinned XMRig v6.26.0 ARM64 QA binary from the previously recorded synthetic research build; both donation constants zero, --donate-level=0, one CPU thread, light RandomX memory mode, local-only pool URL.

## Executed, verified acceptance checks

1. Native ARM64 daemon, wallet RPC, wallet CLI and C pool binaries compiled and linked.
2. Temporary daemon initialized the correct chain at height 1 with genesis hash and nonce verified. No public peers, mined blocks or submitted transactions.
3. The existing Oracle block explorer returned **HTTP 200** on /api/overview, /api/blocks and /api/block/0 against the temporary daemon; correct genesis and candidate difficulty. When the QA daemon stops, the explorer fails closed with HTTP 503.
4. Temporary FRG wallet RPC returned the exact independently generated native FRG public address and balances **0 / 0**; RPC process later stopped.
5. C pool connected to the native RPC server, got an actual block template at height 1, returned an rx/0 Stratum login job to a disposable miner address, with matching genesis RandomX seed and properly encoded blob/target.
6. Malformed nonce share **rejected**. Syntactically valid nonce with deliberately incorrect RandomX digest **rejected** as Invalid share.
7. The pinned actual XMRig CPU miner submitted a **genuine native RandomX share**, which the C pool accepted and recorded in round work. The QA-only pool start-share difficulty was deliberately lowered from 1000 to **10** for the test; actual network difficulty stayed **500,000**. Recorded accepted work was 10–20 depending on test run.
8. Pool /stats now reports mining height **1** and network target difficulty **500,000** from the NEXT block template. The previous wrong genesis tip difficulty of 1 is no longer used for mining-target stats.
9. 1% pool operator fee configured in both the frozen manifest and source; per-share fees use exact integer atomic units, with separately credited operator wallet. The pool reward wallet is a distinct, disposable QA receiving address; production reward wallet is **not yet configured**.
10. Pool source regression suite: **31 Python tests passed** after correcting difficulty/height reporting. Compiled receipt and PPLNS test executables also passed on Oracle ARM64. End-to-end block reward payouts were NOT attempted.
11. Process harness always terminates the offline daemon, wallet RPC, C pool and XMRig; accepted shares were test-only and created no public mining entitlement or FRG block.

Reproduce on the authorized Oracle QA environment (existing restricted QA wallet and build prerequisites required): run Python 3 **tools/run_offline_pool_qa.py --with-miner**. See tools/create_disposable_qa_wallet.py, tools/stage_isolated_pool_qa.py and tools/probe_pool_stratum_offline.py. The run intentionally aborts on wrong chain, wrong fee, invalid job, unrejected wrong RandomX hash, unaccepted real share, or unexpected block/payout.

## Live read-only infrastructure

- Oracle user-level **forgecoin-monitor.service**: enabled and active with linger enabled, loopback 127.0.0.1:19810, no secrets, no public mining or payout handlers. Nginx exposes GET-only /pool/api/monitor over HTTPS.
- Existing Oracle /pool/ remains the original **57-field detailed pool/observer website**. A small additive script connects verified node telemetry (only) to the 20261026 monitor; all unverified pool/worker/reward fields remain Unavailable. Existing index backed up; no statistics fabricated.
- Windows external TLS validation of https://150.136.209.227/pool/ succeeded; homepage and /pool/network-monitor.js returned HTTP 200. Monitor deliberately returns HTTP 503 with no daemon.
- Oracle explorer 127.0.0.1:19800 and public nginx remain active. It correctly returns missing-node status while the mainnet daemon is offline.

## Android and Windows packages

- Android preview source: apps/android, Java Android 26+ build using local Android SDK v36.1; release candidate package is **NOT a wallet or miner**.
- Debug-signed Android QA APK: C:\Users\tgibb\Downloads\ForgeCoin-Android-Monitor-QA-v0.1-20261027.apk
- SHA256: FD8732AD6046971F307FC0ECDBFC24B664AAAC5C2F7EF082664529366DCA14DD
- Android API 36.1 emulator smoke: APK installed and MainActivity launched, verified HTTPS GET to Oracle (HTTP 503 while daemon offline), correct offline status, all native FRG wallet functions disabled, no runtime crash. No physical handset tested.
- Updated Windows QA v0.6: `C:\Users\tgibb\Downloads\ForgeCoin-Windows-Prelaunch-QA-v0.6-20261027.zip` (SHA256 `5E44DCE16356235F26B9B0F702A90CF55FAB39CAA017586FA2F86C2E69478425`). Native FRG solo and pool mining buttons are greyed out, as are all Solana wallet controls. The new `apps/desktop/tests/test_release_gate.ps1` passed: editing QA JSON cannot unlock mining; a separate temporary simulated build allows it only with exact identity, release authorization and SHA256-pinned fake native fixture executables; wrong genesis and changed daemon hashes relock it. No miner or wallet was executed by these gate tests. **Not a public release.**

## Additional October 27 verification

- Persistent Oracle monitor's `normalized_pool` function successfully parsed the real native C pool `/stats` output from the complete offline daemon + native wallet RPC + explorer + C pool + pinned XMRig QA run. The harness recorded accepted work difficulty 30 with a QA-only share target of 10; canonical network difficulty remained 500,000. No actual block found.
- Dedicated Oracle `forgecoin-mainnet-20261026.service` was installed and systemd-verified, but is **disabled and inactive**. It references the verified fresh binary, unlike the obsolete October 20 staging service. Its launch preflight correctly rejects absent release authorization/marker. Eleven new launch-gate regression tests pass. The newest gate source with currency-term checks is staged on Oracle but privileged installation remains blocked; the installed gate is the preceding version. See `services/oracle_mainnet/README.md`.
- Combined local regression results: 11 Oracle release-gate tests, 31 C-pool Python tests, 8 monitor tests, and real XMRig native RandomX accepted-share QA passed. The Windows C# mining release-gate reflection test passed all four scenarios.

## Remaining public launch gates — not passed yet

1. A genuine, consensus-valid full block discovery and acceptance from native miner and daemon; height-1 synchronization on at least two independently initialized nodes and correct difficulty transition at height 16.
2. Pool block reorg/orphan/maturity tests and crash-safe end-to-end payout reconciliation against real chain-confirmed wallet transfers. **The pool's wallet spending build macro remains disabled.**
3. Operator-controlled independent pool reward wallet; owner verification of the configured fee wallet private-key recovery. Fee address is public only; no keys should ever appear in docs, logs or the pool site.
4. Production RPC authentication, TLS/reverse proxy firewall restrictions, worker capacity, account authentication, payout change reauthentication and security review.
5. Production Windows miner/full node/wallet release packaging, install/uninstall, offline seed backup and recovery, and a repeatable independent user test.
6. Android native FRG wallet + RandomX CPU engine via a reviewed mobile implementation, foreground mining service and thermal controls. Debug-signed read-only QA APK must never be promoted as a functional release.
7. Release manifest authorization, signed release assets, actual public P2P synchronization and controlled activation. No production Stratum or network mining is currently open.

**Genesis note:** the inherited height-0 transaction has an 11.92092895 FRG output and is described by the project as a fork/genesis artifact intended to be unspendable. Independent cryptographic proof of irreversible unspendability was not supplied; never claim a formally verified zero-premine genesis without qualification.

Future independent 50M mFRG SPL (5M reserved potential USDC trade/sale; 45M future), FCMP++/CARROT, native L1/L2/L3 proposals are **roadmap-only**, not part of this release.
