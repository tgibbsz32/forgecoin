# Native pool credited-block historical audit — November 2, 2026

**Status:** Prelaunch source-only hardening merged in [PR #196](https://github.com/tgibbsz32/forgecoin/pull/196), with x86_64 and ARM64 compile/link and standalone native fixtures passing. **Not deployed or runtime-accepted.** Does not activate FRG mining, Stratum, wallet transfers, Oracle infrastructure, or consensus. The frozen 20261026 mainnet remains locked.

## Why this is necessary

The pool previously reconciled mature rewards against a verified, contiguous ten-header daemon response. That protects recent maturation, but a previously credited block older than this window could be reorganized after the original credit and escape subsequent canonical checks. Pool payments must not proceed on a ledger with a known credited-chain conflict.

The existing [persistent LMDB reorganization quarantine](POOL-PERSISTENT-REORG-QUARANTINE-2026-11-02.md) holds accounting across restarts, but requires the pool to actually revisit the affected credited height before it can detect an older rewrite.

## This implementation

The native C pool now implements a **round-robin retrospective scan of every recorded `BLOCK_UNLOCKED` candidate in the actual LMDB blocks database**, including multiple candidates at a height. It validates each LMDB key, record size, matching height/status, 64-byte hash and parent fields, nonzero difficulty and reward before comparing historical evidence. A bounded timer dispatches one `get_block_header_by_height` request per period on the configured daemon RPC, and verifies the reply's structure, height, hash, parent, difficulty, reward, timestamp and orphan status.

- A matching canonical response advances the scan. A complete pass authorizes the *history audit gate* only; separate payouts, maturity, fees, canonical chain selection and wallet verification remain independent.
- A **valid but conflicting** canonical response freezes in-process reward accounting and writes the existing `frg.accounting.deep_reorg.quarantine.v1` LMDB marker. Mark persistence failure terminates the process.
- A malformed response, timeout, local LMDB error, allocation failure or in-flight ledger change keeps the audit unverified and the future payout path held. A transient invalid RPC reply is **not** mislabeled as a proven reorganization; no durable conflict marker is written from an unverified reply.
- The audit never assumes a previous process's scan results survived restart. It restarts after a newly credited candidate or a changed number of eligible entries.
- Late callbacks are rejected using a generation sequence, and a complete audit is required before the pool's already-compile-disabled wallet transfer path can consider payments.

## Limitations / risks to test

1. **Single daemon trust:** The current in-process scan uses the pool's configured daemon; independent observation from at least two separately operated nodes is still required to identify malicious or eclipsed RPC data. The separate [read-only chain watcher](../CHAIN_RISK_MONITORING_OPERATIONS.md) does not automatically authorize pool payouts.
2. **Throughput versus settlement availability:** One candidate is checked per two seconds. A sufficiently large ledger or rapidly accruing credits may cause audit restarts and delay payments indefinitely; this is intentionally fail-closed but requires scalability testing and potentially a reviewed batch/epoch mechanism.
3. **No automatic undo:** A conflict stops further crediting/payout consideration; it does not reverse previously signed transfers, repair miner balances, or select a canonical chain independently.
4. **No running pool validation yet:** Standalone json-c comparison tests are not equivalent to an actual LMDB + RPC + 61+-block restart/reorg fixture or dual-node security acceptance.
5. **Legacy daemon concerns:** The public `main` branch still does not contain the finalized frozen consensus integration. PR #185 remains distinct. No production network mutation is allowed.

## November 3, 2026: deeper synthetic acceptance and false-quarantine fix

[Merged PR #197](https://github.com/tgibbsz32/forgecoin/pull/197) extends historical replay using the **actual shared LMDB scanner, strict daemon JSON-RPC envelope evaluator, account payout-eligibility policy, and persistent LMDB hold**. The focused [native offline regression workflow](https://github.com/tgibbsz32/forgecoin/actions/runs/41657969800), [x86_64 native link](https://github.com/tgibbsz32/forgecoin/actions/runs/41657969712), and [ARM64 native link](https://github.com/tgibbsz32/forgecoin/actions/runs/41657969685) all passed.

The test creates a *synthetic* 240-height chain and 120 already matured credited records, preserving separate miner and 1% fee balances. It verifies normal historical sweep, malformed/wrong-height/error RPC handling, restart-required rescan, and a fork beginning at credited height 100 when the tip is 240 (**141-block deep**). It asserts the first conflict is preserved in durable LMDB quarantine across restart, no duplicate account changes occur, and the shared payout policy forbids payment while unverified or held.

**Important distinction:** the fixture uses fabricated block hashes and replayed JSON. It does **not** mine 240 valid RandomX blocks, run a daemon or Stratum process, verify actual fork-choice or RandomX seed rules, sign a wallet transfer, or demonstrate an end-to-end real-chain 61+ reorg. Those remain critical release gates.

Security correction: a structurally valid response for the **wrong height** or a hash-identical header with inconsistent difficulty/reward now returns `FRG_HISTORY_UNVERIFIED`, preventing wallet release but **not** writing a permanent reorg marker from inadequate evidence. Correct-height canonical hash/parent/orphan conflicts still trigger the durable quarantine. The shared JSON-RPC evaluator is used by both the live callback and the isolated fixture; explicit JSON `error: null` is treated as success, genuine errors as unverified.

## November 3 verified end-to-end historical credit quarantine — acceptance PASS

[GitHub native x86_64 full-stack CI 41731489643](https://github.com/tgibbsz32/forgecoin/actions/runs/41731489643) **PASSED** on the isolated frozen-consensus + pool-security validation branch. This supersedes earlier entries below that described this particular test as pending.

- Real C Stratum login, job and genuine native RandomX result submitted a difficulty-one block to the real localhost-only FAKECHAIN daemon; daemon accepted it at height 1 and the C pool durably recorded the block.
- 61 subsequent native FAKECHAIN blocks matured the reward. A **separate read-only LMDB inspector** verified the credited record and precise 8-decimal allocation: **2,384,185,222** reward atoms, **2,360,343,370** miner atoms and **23,841,852** fee atoms. A clean pool restart preserved these amounts without double credit.
- A second independently mined 70-block FAKECHAIN branch won a genuine native P2P reorganization, orphaning the previously credited block in a **62-deep rollback**.
- The running native pool's historical credited-block RPC audit observed the changed canonical height-1 hash and wrote the durable LMDB quarantine itself; the inspector verified held state and unchanged balances. The pool was then stopped and a new pool process **refused startup** on that quarantined LMDB.
- The CI run also passed the separate 66-vs-70 native fork convergence and prelaunch mainnet mining refusal. [Native ARM64 companion 41731489619](https://github.com/tgibbsz32/forgecoin/actions/runs/41731489619) passed.
- All test processes were loopback-only, used public test addresses, had wallet RPC unbound and payouts compile-disabled, and used disposable LMDB. No spendable wallet, live FRG network or Oracle deployment was touched.

**What this closes:** native Stratum block acceptance, actual mature credit, exact 99/1 split, restart invariance, genuine deep historical fork, persistent accounting quarantine and startup denial on the combined test branch.

**What remains:** adversarial signed genesis-output transaction exclusion, independent multi-node canonical-chain/RPC trust, wallet transaction creation and payout signing, live operational testing, public miner release gates, and review/merge of draft frozen-consensus PR #185. The separate single-daemon trust limitation remains. Passing this regtest is not launch authorization.

## November 3 verified native daemon–pool integration (after test correction)

[GitHub x86_64 full-stack CI 41676011529](https://github.com/tgibbsz32/forgecoin/actions/runs/41676011529) **PASSED** at combined test-only branch revision `8ccd3e4`. It compiled and linked both the *real* native C pool and `forged` daemon from a single frozen-consensus/pool-security source tree. It then started a genuine loopback-only FAKECHAIN daemon and a real localhost-restricted C pool with dummy public test destination, unavailable wallet-RPC endpoint, and payouts disabled. Pool HTTP statistics exposed the correct 1% fee and zero credited/pool-found blocks, and the pool consumed daemon block templates and reflected a newly mined FAKECHAIN block: pool zero-based `network_height 0→1` while daemon `get_info.height 1→2`. The same native job passed 66-vs-70-block deep fork convergence.

This **closes the native daemon↔C pool compile/link, startup and block-header-refresh interface milestone**. It does not establish share-submission acceptance, pool-found block maturity/fee distribution, historical credited-block quarantine triggered by a genuine network reorg, or a safe live payout wallet.

## Required acceptance before public operation## November 3: actual native C pool maturity and exact 1% ledger acceptance

[Native x86_64 GitHub full-stack run 41730254226](https://github.com/tgibbsz32/forgecoin/actions/runs/41730254226) **PASSED** a genuine payout-disabled localhost-only FAKECHAIN scenario using the real frozen/prelaunch-locked daemon and actual C Stratum pool. An actual native RandomX share was daemon-accepted as a pool-found block at height 1; 61 further genuine blocks matured it. The separately compiled **read-only LMDB inspector** checked the pool's *real* `blocks`, `balance` and `properties` databases, rather than trusting a mock or WebUI counter: block 1 recorded `BLOCK_UNLOCKED`, reward **2,384,185,222** atomic FRG, miner credit **2,360,343,370** atoms and separate public-only test operator fee **23,841,852** atoms. The integer miner+fee sum exactly matches the canonical reward. After a real C-pool process stop/restart the same independent inspector confirmed balances were unchanged (no double credit).

A prior run revealed an **unsafe shutdown** before the maturity test could start: the C pool called `exit()` inside an async SIGTERM handler while the detached WebUI had an independent libevent thread. Test-only integration commit [c8e8f1f](https://github.com/tgibbsz32/forgecoin/commit/c8e8f1ff98bec1ee40da02a6d355cab58e918a6c) moves SIGINT/SIGTERM handling onto the regular libevent dispatch thread and serves HTTP on the same C-pool event loop. The exact previous maturity/restart sequence then passed.

**Remaining:** true 61+-deep reorganization *after credit* must result in pool-detected persistent LMDB accounting hold and refusal to restart, not merely standalone synthetic evidence or a separate native reorg; this is staged in isolated commit [3599af6](https://github.com/tgibbsz32/forgecoin/commit/3599af696652b4bceded6d5015763f09122f203b) with native CI pending at [41731489643](https://github.com/tgibbsz32/forgecoin/actions/runs/41731489643). Independent-node controls, signed genesis-output exclusion, real wallet spending, payout recovery, cross-platform miner release and public mainnet cutover remain blocked. No production funds or public node services were involved.

## November 3 first genuine native Stratum-mined FAKECHAIN block

[GitHub x86_64 CI run 41726516379](https://github.com/tgibbsz32/forgecoin/actions/runs/41726516379) **PASSED** an end-to-end test that issued a genuine native C Stratum mining job, computed native RandomX using the real public seed and hashing blob, submitted the valid 8-character nonce/result through the C pool, and observed **one daemon-accepted pool-mined FAKECHAIN block**. Malformed and duplicate submissions were rejected. The native pool, daemon and proof helper were compiled from the same isolated frozen-consensus/pool-security source revision. The fixed native mainnet lock remained on, all listeners were localhost-only, and no wallet RPC signer or real funds were present.

The next acceptance extension introduces a separate read-only inspector of the pool's actual LMDB database (not just WebUI found-block counters), and then 61 additional genuine native FAKECHAIN confirmations with a test-only public fee destination and PPLNS multiplier 1.0 so a single valid share can account for one full block. The inspector requires exact integer-atomic 99% miner / 1% fee rewards and no duplicate allocation after a pool restart. **This maturity/restart result is not yet verified**, and even a pass would not establish a real-wallet transfer or post-credit 61+ network reorg quarantine.

## November 3 native FAKECHAIN deep fork — separately verified

A full native x86_64 daemon test on frozen/prelaunch-locked draft [PR #185](https://github.com/tgibbsz32/forgecoin/pull/185) has [passed](https://github.com/tgibbsz32/forgecoin/actions/runs/41674936417): two real loopback-only RandomX-regtest nodes independently mined 66 and 70 blocks. After P2P reconnection the 70-block fork won and displaced the 66 formerly canonical blocks. The test independently checked common genesis, winning chain tip and changed deep historical hashes. One short RPC timeout during alternative-chain synchronization was retried within a fixed deadline; all final assertions passed. This is **real native chain reorganization** on fakechain, rather than the separate synthetic LMDB fixture. The mainnet compiled prelaunch lock remained active.

For pool interoperability, [test-only combined integration branch](https://github.com/tgibbsz32/forgecoin/tree/integration/frozen-mainnet-prelaunch-validation-20261103) merges the consensus candidate with current native pool reorg protection **without changing public main**. A hosted native test compiled and linked a real C pool with a real daemon from exactly the same source revision and launched a localhost-only pool against FAKECHAIN (no wallet RPC service, no spending). Its first smoke run reached a valid pool header/template and HTTP `/stats` but the test incorrectly expected the pool's zero-based `network_height` to equal the daemon's genesis-inclusive `get_info.height`. That assertion was corrected on combined revision `8ccd3e4` and the updated smoke's native runtime result remains pending at this checkpoint.

**Still unresolved:** genuine Stratum share acceptance, recording and maturing 61+ pool-found blocks, then deep reorg, durable pool quarantine and payout refusal with the running native pool and after restart, independent-node trust, and wallet signing. Neither the genuine regtest fork proof nor source-only credited-history fixture establishes those results.



- Standalone native comparator tests reject changed height/hash/parent/reward/difficulty/orphan and malformed RPC.
- x86_64 and ARM64 compile and native link CI pass.
- Disposable LMDB-backed fixtures cover multiple credited candidates at one height, clean full sweep, changed counts, mid-flight new credit, timeout, restart, orphan and 61+ block deep reorg.
- A running isolated pool proves recognized native daemon header replies and demonstrates 1% fee allocation, mature payouts and zero transfers while the audit is unverified/held.
- Independent-operator nodes, alerting and manual incident workflow are reviewed. No key material is included in these tests.

See [security research](../SECURITY_51_PERCENT_AND_TARI_MERGE_MINING_2026-11-02.md), [port contract](../NETWORK_PORTS.md), [issue #194](https://github.com/tgibbsz32/forgecoin/issues/194).
