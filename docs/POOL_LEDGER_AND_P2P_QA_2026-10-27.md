# ForgeCoin payout ledger and two-node QA — 2026-10-27

**Engineering evidence: additional fail-closed checks passed, but PUBLIC MINING AND WALLET PAYOUTS ARE NOT AUTHORIZED.**

Source branch: feat/oracle-backend-prelaunch-20261027, base frozen 20261026 (genesis nonce 20261026, hash 4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c).

## Native 1% pool and ledger fixes

The jtgrassie-derived native C pool remains at 1% operator fee on eligible official-pool reward allocations; 99% is credited to miners. Solo mining has **no pool fee**. The operator fee address is the public address in config/mainnet.identity.json and native pool.conf; do not upload secret keys. A miner's balance is a uint64 atomic-unit total (100,000,000 atomic units per FRG).

- **Checked additions:** frg_checked_balance_add rejects UINT64 arithmetic overflow without changing the destination variable or an LMDB record. Called by the actual native balance_add function.
- **Write errors roll back:** balance_add now aborts its nested LMDB transaction and preserves the error when initial insert or update fails; never replaces the failure with a successful mdb_txn_commit.
- **Mature-block accounting:** process_blocks checks all orphan and maturity status mdb_cursor_put returns, aborts the **outer LMDB transaction** if a child PPLNS credit fails, and only commits the block's UNLOCKED status and miner/operator fee credits together. Incomplete PPLNS reward allocations stay locked.
- **Privacy:** wallet payment batch RPC body no longer logs full addresses and amounts.
- **Spend safety:** forcibly compiling with FRG_TESTED_WALLET_PAYOUTS is rejected at the C preprocessor. The current transfer_split callback still debits local balances immediately on wallet ACK and has no durable pending-journal, canonical transaction destination matching, confirmation threshold or crash/reorg recovery. **Do not override this compile error.** Replace the unsafe callback with an audited confirmed-settlement state machine first.

## Tests executed on Oracle ARM64

1. Native C pool recompiled/linked against the frozen 20261026 binaries after ledger changes. Final Oracle ARM64 native C pool SHA-256: `031d59d1df6152107e6bfa063efe6abed48d780801e1878e535343302731da3a`.
2. Compiled test_currency.c under -Wall -Wextra -Werror passed exact 8-decimal parsing, integer 1% fees, exact UINT64_MAX credits and overflow rejection.
3. Compiled test_lmdb_ledger_atomicity.c with the **real system liblmdb** under -Wall -Wextra -Werror passed:
   - Nested balance credit followed by outer abort leaves balance 0 and block LOCKED.
   - Successful credit and block UNLOCKED status commit as one transaction.
   - Duplicate local maturity processing does not credit twice **in this independently implemented fixture**.
   - Overflow attempt cannot wrap the account or unlock block; exact maximum remains bounded.
   These tests model the production transaction structure but **do not execute process_blocks in pool.c**, do not prove idempotent on-chain transfers, and cannot guarantee crash recovery after wallet broadcast.
4. 35 local Python source-contract/unit tests pass; an Oracle copy of the test subset also passes. Negative C compilation with -DFRG_TESTED_WALLET_PAYOUTS produces the required hard #error.
5. After previous core accounting edits, the combined offline daemon/wallet RPC/explorer/C pool/XMRig test passed actual verified RandomX share acceptance at QA share difficulty 10 with network difficulty 500,000. No winning block was submitted and no wallet transfer attempted.

## Two independent local P2P node instances

New tools/run_loopback_two_node_qa.py was executed on Oracle using two separately initialized clean blockchain databases and the exact 20261026 ARM64 native daemon binary.

- Node A: P2P 127.0.0.1:49580, RPC 127.0.0.1:49582, **0 outbound** slots.
- Node B: P2P 127.0.0.1:49581, RPC 127.0.0.1:49583, one **exclusive** peer 127.0.0.1:49580.
- Both used --hide-my-port, --no-igd, --disable-dns-checkpoints, --no-zmq, loopback binding, and no wallet or mining services.
- Verified A's incoming connection count 1, B's outgoing connection count 1, both at height 1 with the frozen 20261026 genesis hash and nonce. Two processes shut down cleanly.
- **Limits:** verifies network UUID/handshake and genesis agreement but **not consensus block propagation or cross-machine chain synchronization after block 1**. The intended first public solo-mined mainnet block still belongs to the user. No QA or public block was mined.

## Still blocking public pool deployment

- Actual winner share achieving BLOCK consensus difficulty and daemon submit_block canonical acceptance; mature 60-block reward, fee-wallet custody, pool/solo reward coinbase ownership and account reconciliation.
- A durable idempotent payout intent journal, reconciliation of destination/amount/hash with confirmed on-chain outgoing transfers, retry/restart recovery, reorg/doublespend handling and fee treatment.
- The separate pool reward wallet is currently unset and payouts remain disabled; proof of ownership of the operator fee wallet is pending.
- The Android APK is a read-only preview, not a native miner/wallet. Windows v0.6 remains build-gated/disabled for mining. No production release downloads are advertised.
- Oracle mainnet service remains DISABLED/inactive; the strict root-owned launch gate update was blocked for privileged installation and must be reviewed before release.

This evidence must not be presented as a guarantee of spendability, lossless payouts, or safe public pool operation. The inherited genesis 11.92092895 FRG output is documented as a presumed unspendable fork artifact, but independent cryptographic proof remains absent.
