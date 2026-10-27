# Oracle backend build evidence — 2026-10-27

**PRELAUNCH. Public mining, block submission, pool payouts and financial custody are not authorized by the results below.**

## Proven source/build results

- Source: tgibbsz32/forgecoin commit 62fc0b875431d7fa64f887bb20b7b51d67abcdfa (frozen 20261026 mainnet branch), isolated Oracle ARM64 worktree at /home/ubuntu/forgecoin-mainnet-20261026.
- CMake Release daemon target **built successfully** on Oracle aarch64. Binary: build-release/bin/forged; SHA256: 3dd3d0c10f41ef2f887314221e0b9adec9571b98a83c9783a78a6290156506bd.
- jtgrassie-derived ForgeCoin native C pool **compiled and linked** on Oracle aarch64 against that exact source/build. Binary: services/official_pool/jtgrassie/build/release/forgecoin-pool. SHA256: 3b5bc62675413a4514faff0f1b4dde87f63f1796001c831c51d764a08dace69c.
- Native pool source-contract tests on Oracle: **20 passed**.
- Isolated QA daemon: started under a 24-second timeout with --offline and P2P/RPC bound to 127.0.0.1, unique fresh database, no mining; checked using the repo's read-only tools/verify_mainnet.py. Identity matches nonce 20261026 and genesis 4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c, height=1, launch_authorized=false.
- The QA daemon then timed out; public forgecoin and new-mainnet-staging services remain inactive. Existing public explorer and nginx remain active. No mainnet mining port is listening.
- Read-only monitoring Python module: **8 tests passed** on Windows. Files were copied to Oracle home for staging but the systemd installation was blocked; no monitor service was started.

## Outstanding mandatory release gates

1. **Genesis coinbase uncertainty:** height 0 contains 11.92092895 FRG output; outputs are indexed by BlockchainDB; permanent unspendability has NOT been demonstrated. Valid-looking Ed25519 output point and 60-block unlock are NOT burn proofs. Resolve explicitly or re-freeze a new genesis and recompile all artifacts BEFORE the first mined block.
2. Native RandomX template-to-actual-share tests, accepted canonical blocks, mature PPLNS accounting, reorg/crash recovery and payout reconciliation have NOT passed end-to-end.
3. Pool has no live public Stratum listener, approved separate pool reward wallet, authenticated miner accounts, verified payout engine or operating worker-stat collector. Build success is not operating readiness.
4. Windows wallet and Linux node interoperability and live funded transactions require isolated adversarial QA; do not entrust real funds yet.
5. Follow security audit, monitoring, TLS/firewall, peer bootstrap, separately signed release artifacts and explicit owner launch authorization.
6. Existing explorer intentionally serves unavailable while daemon is offline; it should never display retired-chain balances or fabricated pool hashrates.

**Decision: NO-GO for mainnet public mining on current evidence.** No production services were enabled and no blocks were mined.

The independent mFRG SPL token, FCMP++/CARROT, and proposed L1/L2/L3 protocols are future plans, not implemented capabilities.
