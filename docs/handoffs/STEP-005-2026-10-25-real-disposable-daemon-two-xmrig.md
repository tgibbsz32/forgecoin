# STEP-005 — 2026-10-25 — genuine daemon jobs consumed by two XMRig clients

## Scope, implementation commit and isolation

- Active source: the **original** `tgibbsz32/forgecoin` native FRG project, NOT the separate FCMP/CARROT repo.
- Base `main` at `7140606fdc26c7c4ca745d4fbb520a51631bacd0`. Research branch `feat/pool-xmrig-loopback-20261025` builds on Step 004's XMRig nonce-layout fix.
- **Implementation commit:** `579f102deb3974fee8839ed82f50dd314d5e4a79`.
- No production network, daemon instance, mainnet wallet, active mining account, treasury, explorer or public pool modified. The original Windows source worktree's uncommitted consensus changes remain intact.

## Delivered files

- `services/pool_research/tests/run_disposable_daemon_two_xmrig.py`: isolated manual research harness. Explicitly selects existing reviewed daemon/wallet/XMRig/native helper executables and **disposable** wallet files. Copies the wallet into a fresh temporary directory, uses `forge-wallet-cli --offline` for its public mining address (never printed), starts `forged --offline --no-igd` with a fresh temporary data dir and loopback P2P/RPC/ZMQ binds, fetches real `get_block_template` jobs through `DaemonJobSource`, and runs **two independent XMRig 6.26.0 processes** (one thread each, zero donations, RandomX light mode) against the bounded loopback Stratum research listener. Shares are independently recomputed through the compiled persistent C++ RandomX worker. All are **uncredited**, never submitted as a block, never sent to a wallet or paid out. The script enforces bounded test duration, two distinct worker sessions with native-verified submissions, cleanup of miner/daemon processes and temporary wallet copies. It refuses wallet filenames not clearly marked disposable.
- `services/pool_research/README.md`: summary of observed tests, source provenance, safety boundary, and remaining gaps.

## Executed evidence

- **First controlled run:** two XMRig processes connected and received independently generated real ForgeCoin daemon templates from a fresh offline chain at height 1; seven matching native RandomX submissions were observed, but only one miner contributed. This **did not** meet the two-miner completion gate.
- **Extended controlled run (24 seconds, worker difficulty 30):** 2 distinct worker sessions, **2 sessions with independently native-verified shares, 59 native-verified submissions**, and **19 expected busy-verifier rejections** (research listener intentionally serializes its single persistent native verifier). No fabricated, credited, submitted or paid shares.
- The actual daemon was stopped; the script confirmed `DISPOSABLE_DAEMON_STOPPED True`. Chain RPC, Stratum and mining were restricted to numeric localhost ports. Temporary chain/wallet artifacts were cleaned. No production mining or block search continued.
- Python syntax check on the new harness: passed.
- `python -m unittest discover -s services/pool_research -t . -q`: **136 run, 132 passed, 4 platform skips, no failures**.
- `git diff --cached --check` passed before implementation commit.

## Binary provenance (SHA-256 for reproduced local test)

These are local binaries supplied from earlier ForgeCoin work, **not** reproducible release artifacts built from the current source revision:

| Binary | SHA-256 |
| --- | --- |
| Existing consensus-candidate `forged.exe` | `C51BA96BDB32136CD07C681E09D966790F258EA22B7F6ABB280F45A4BEF4C463` |
| Offline `forge-wallet-cli.exe` | `AB81CAB8842C90F54D57113023D63F0EF0CA363F06C3D090C210A853230E6A98` |
| Existing XMRig 6.26.0 `xmrig.exe` | `6FA80698D7268F6E88AA88C06FB27EE99E1BCEE747C2E76911E6206A5B1AEEB3` |
| Locally compiled persistent native `randomx_worker.exe` | `0C83014D3101C076D35F50B84BBBABF0EFF6E649D3B0F023D6AC16224FE28519` |

The disposable node identifies its *own* genesis hash, so this remains **self-observed, not independently pinned chain identity evidence**. It is an offline, mainnet-typed genesis clone, NOT a real active network.

## Launch blockers and next engineering step

1. The research listener has **one global busy native verifier**, producing 19 rejected submissions during the 24-second, two-miner test. Proper bounded scheduling/fairness, crash-safe worker state, privacy controls and denial-of-service performance remain release blockers. Two light-mode miners are not a 100-worker load test.
2. Jobs are issued only once on login; new heights, reorgs or RandomX seed changes require authenticated per-session job renewal/rebroadcast. No actual long-running pool/Stratum service is installed or exposed.
3. No independent mainnet genesis/network identity attestation, reproducible official daemon build, actual network block difficulty validation, serialized candidate `submit_block` tests, canonical accepted-block evidence or mature rewards.
4. No durable accepted share accounting, chosen PPLNS window policy, exact 1% pool fee recovery, safe pool wallet payout signing, orphan/reorg recovery or reliable restart path; no pool statistics read-only API and website wired to verified canonical activity.
5. Windows desktop wallet/miner integration and robust Linux/ARM64 builds and external security review are still required. Neither FCMP/CARROT nor Solana work belongs in this branch.

**Next step:** design/test a bounded fair verifier work scheduler and per-worker template refresh on real daemon tip changes, with stale job rejection. Then prove an isolated accepted block against the disposable daemon and only later connect auditable canonical share/reward/payout accounting. Maintain numbered dated handoffs, never merge as a production pool without review.
