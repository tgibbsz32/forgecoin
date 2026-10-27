# Oracle backend build evidence — 2026-10-27

**PRELAUNCH. Public mining, block submission, pool payouts and financial custody are not authorized by the results below.**

## Proven source/build results

- Source: tgibbsz32/forgecoin commit 62fc0b875431d7fa64f887bb20b7b51d67abcdfa (frozen 20261026 mainnet branch), isolated Oracle ARM64 worktree at /home/ubuntu/forgecoin-mainnet-20261026.
- CMake Release daemon target **built successfully** on Oracle aarch64. Binary: build-release/bin/forged; SHA256: 3dd3d0c10f41ef2f887314221e0b9adec9571b98a83c9783a78a6290156506bd.
- jtgrassie-derived ForgeCoin native C pool **compiled and linked** on Oracle aarch64 against that exact source/build. The later patched binary (integer PPLNS and rejected-transfer ledger safeguards, correct next-template mining difficulty) SHA256: `95db01862e682513753c1022c6656139216d1030963967072da4ac5990e7d9a8`.
- Native pool source-contract tests initially 20 passed; subsequently **31 Python tests passed** on Windows (26 on Oracle when last synchronized), plus compiled C money/receipt checks on Oracle.
- Isolated QA daemon: started under a 24-second timeout with --offline and P2P/RPC bound to 127.0.0.1, unique fresh database, no mining; checked using the repo's read-only tools/verify_mainnet.py. Identity matches nonce 20261026 and genesis 4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c, height=1, launch_authorized=false.
- Read-only get_block_template probe against the same offline QA chain succeeded: template height 1, difficulty 500000, expected_reward_atomic 2384185222, RandomX seed hash present, 134-byte serialized block template. No share, block, transaction, miner or pool was submitted. Script: tools/probe_mainnet_template_readonly.py.
- The QA daemon then timed out; public forgecoin and new-mainnet-staging services remain inactive. Existing public explorer and nginx remain active. No mainnet mining port is listening.
- Read-only monitoring Python module: **8 tests passed**. Initial system-unit installation was blocked, then an enabled, persistent and loopback-only **user-level systemd service** was successfully installed with lingering. Nginx's HTTPS `/pool/api/monitor` now forwards GET-only queries; returns 503 on daemon downtime and 200 for a verified temporary QA daemon.

## Outstanding mandatory release gates

1. **Genesis fork artifact disclosure:** height 0 contains an inherited 11.92092895 FRG output; permanent unspendability is NOT independently demonstrated. The owner has chosen to retain the genesis and disclose the uncertain spendability instead of re-freezing. Do not describe it as proven burned/unspendable or claim an independently verified zero-premine supply.
2. Native XMRig 6.26.0 actual RandomX share accepted at disposable QA share difficulty 10, while consensus next-block difficulty remained 500000. Invalid digests rejected. Still no accepted **full block**, matured PPLNS payouts, reorg/crash recovery or chain-confirmed wallet payout reconciliation.
3. Pool has no live public Stratum listener, approved separate pool reward wallet, authenticated miner accounts, verified payout engine or operating worker-stat collector. Build success is not operating readiness.
4. Windows wallet and Linux node interoperability and live funded transactions require isolated adversarial QA; do not entrust real funds yet.
5. Follow security audit, monitoring, TLS/firewall, peer bootstrap, separately signed release artifacts and explicit owner launch authorization.
6. Existing explorer succeeded on actual genesis overview, block list and block-0 detail against an isolated offline daemon, and intentionally serves unavailable while daemon is offline. No retired-chain balances or fabricated pool hashrates.

**Decision: NO-GO for mainnet public mining on current evidence.** No production services were enabled and no blocks were mined.

The independent mFRG SPL token, FCMP++/CARROT, and proposed L1/L2/L3 protocols are future plans, not implemented capabilities.
