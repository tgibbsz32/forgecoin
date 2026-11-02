# ForgeCoin local development preservation — 2026-11-02

**Status: source and evidence preservation only. FRG mining, payout signing, public pool deployment, and mainnet activation are NOT authorized by this change.**

This directory is the recovery entry point if the development workstation becomes unavailable. The original working copies were inspected on `TREYS_DELL_RTX` on 2026-11-02, and source was incorporated into the current public `main` without replacing newer production code. Generated binaries, wallet files, seeds, passwords, chain LMDB databases, and private captures were NOT uploaded.

## GitHub source of truth

- GitHub repository: https://github.com/tgibbsz32/forgecoin
- The current main preservation change starts from `e6238f91a628d19ce77750b7448458ad7fcecdaf` (2026-11-02). Preserve all main commits after this base.
- **Exact locally recovered working branch, including all previously uncommitted source:** [`feat/solana-wallet-devnet-20261027`](https://github.com/tgibbsz32/forgecoin/tree/feat/solana-wallet-devnet-20261027), commit [`384a457b238834205779cd547a7ceaab416b2263`](https://github.com/tgibbsz32/forgecoin/commit/384a457b238834205779cd547a7ceaab416b2263). This is a development snapshot, not an approved release.
- Other already published source and mining research: [`codex/mining-preflight-pe-validation`](https://github.com/tgibbsz32/forgecoin/tree/codex/mining-preflight-pe-validation), commit `d8d3ce7549e979d1a9478ac03da170206d0fc9ea`, with genuine disposable XMRig-derived block reconstruction and offline PPLNS research.
- New-chain draft integration: [PR #111](https://github.com/tgibbsz32/forgecoin/pull/111); packaging audit: [PR #114](https://github.com/tgibbsz32/forgecoin/pull/114); prelaunch consensus guards: [PR #116](https://github.com/tgibbsz32/forgecoin/pull/116); isolated two-miner research: [PR #105](https://github.com/tgibbsz32/forgecoin/pull/105).

## Safely copied into main source tree

1. `services/pool_settlement/ledger.py`, `verify_rpc.py`, README and tests: SQLite WAL settlement state-machine **prototype**, a read-only localhost wallet/daemon verifier, immutable signed-transaction metadata, duplicate/reorg/confirmation guards. **Not integrated** with the authoritative native pool LMDB and **no real transfer signing or relay**.
2. `services/official_pool/jtgrassie/src/frg_block_submit_receipt.h` and `services/official_pool/tests/test_block_submit_receipt.c`: proof-of-concept defensive daemon RPC acknowledgment parser. The header is copied for future integration; it is **not wired into the main branch pool.c callback** by this preservation commit.
3. `tools/run_isolated_windows_full_block_qa.py` and `tools/inspect_local_full_block_qa.py`: bounded localhost-only **lab scripts**, dependent on private local files and an exact prelaunch executable SHA-256. They are **not to be run against production**, and the mining-capable script is not a public launch gate or permission to create mainnet blocks.
4. This directory's `local-uncommitted-2026-10-27.patch.gz` saves a lossless gzip copy of the original diffs for the Windows GUI blue appearance, the local native pool block-submission callback, the source guard regression tests, and the new-mainnet prelaunch workflow. **Do not apply blindly** to current `main`: its pool and website files have moved on, and the actual mainnet source branch requires separate integration and review.

## Archived research (not active main code)

- `ISOLATED_NATIVE_BLOCK_ACCEPTANCE_2026-10-27.md` and `ISOLATED_XMRIG_NATIVE_BLOCK_ACCEPTANCE_2026-10-27.md`: historical Windows source-matched disposable-chain acceptance, including the difficulty-1 miner-derived reconstructed block on legacy prefix 90.
- `pool-research-pplns/pplns.py` and `test_pplns.py`: the original offline PPLNS model, preserved as-is. The full source is also committed on the research branch. The archived test expects a different `services/pool_research/ledger.py` API than current `main`, so it is intentionally **not installed as active main tests**.
- `legacy-wallet-tools/*.ps1`: two locally recovered *legacy-prefix-90 disposable test wallet* scripts, retained as source references only. They are not appropriate for creating or restoring a production mainnet wallet.

## Actual evidence and limitations

- Read-only inspection of the preserved Windows lab log on 2026-11-02 found a genuine native daemon `Found block` message at height 1 with difficulty **500,000**, private block hash `9755a4f129f97b7865e5897e79abf5fea89dec2ba776d53fb9d01942b9f7ba9e`; the QA node database remained on the workstation and was **not uploaded**. A matching prelaunch `forged.exe` was SHA-256 checked against the frozen manifest: `3efaf014c7fdfcea167630f1884abee2defd40f28f1e725b6c0a8fcede5b5c37`. The saved script checks peer propagation, but its full assertions were **not rerun** during preservation.
- Frozen selected network identity remains nonce **20261026**, genesis hash `4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c`, P2P/RPC/ZMQ **39480/39481/39482**, prefixes **190/191/192**. This is selected **future mainnet identity**, not proof the public network has launched.
- On 2026-11-02, `py -m unittest discover -s services/pool_settlement/tests -p 'test_*.py' -q` passed **45 tests** against both the source checkout and new main worktree. The local source checkout also passed **11 pool payout safety source tests**. These are synthetic/isolated tests, not real mature payouts.
- The archived PPLNS tests had **7 passes and 1 API-mismatch error** when run in the newer `main` tree; preserve these files for later porting rather than claiming a pass.
- The local Windows v0.6 ZIP and Android ARM64 development APK are **prelaunch previews**, not signed working public mining releases. They were intentionally not committed.

## Critical unresolved integration work

1. **Do not mistake main for a fresh-genesis runtime.** At this preservation point, main `src/cryptonote_config.h` still contains *legacy* nonce 10000, address prefix 90 and P2P port 19480. The frozen 20261026 implementation lives in the development branch and draft integration PR. Audit and integrate consensus without changing the agreed frozen identity; prove genesis-output permanent unspendability and controlled launch authorization.
2. Reconcile the new branch pool callback with the more recent `main` safety commits (including November 1 fail-closed identity and payout checks). A mere daemon `status=OK` is not independent canonical-chain proof.
3. Complete the canonical accepted-block, 60-block reward maturity, payout signing/relay, confirmed native wallet transfers, orphan/reorg and crash-recovery acceptance tests on **disposable isolated networks**. Pool payout and public Stratum remain disabled.
4. Verify independent matching Windows/ARM64 consensus, clean-machine Windows app, Android native wallet/mining hardware tests, infrastructure/HTTPS/monitoring, and external security review before an approved public release.

**Next continuation:** begin at this file, compare GitHub `main` to commit `384a457` and PRs #111/#114/#116, run the safe offline tests, then plan reviewed incremental integration. No private wallet, fee-wallet seed or signing key is required to perform this work.
