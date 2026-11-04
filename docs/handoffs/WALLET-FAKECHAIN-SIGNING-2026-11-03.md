# ForgeCoin disposable native wallet signing acceptance — 2026-11-03

**Status:** Research-only native CI candidate, [draft PR #203](https://github.com/tgibbsz32/forgecoin/pull/203). This is **not** launch authorization or a wallet payout release.

## Problem and test boundary

The native C pool has demonstrated real isolated Stratum block finding, 61 additional-block maturity, accurate 99/1 LMDB credit accounting, a genuine deep fork, durable quarantine and blocked restart. Those results **do not prove** that the native FRG wallet can derive owned mined outputs, build transaction signatures, relay valid transactions or settle wallet transfers.

A genuinely valid full-signed transaction containing the *real* frozen genesis coinbase as a ring member cannot currently be exercised on locked mainnet. That chain is restricted to height 0, with no other confirmed ring members, and the genesis private spend key is unknown. The previous signed-genesis native crypto regression and `/get_outs` height-zero readback demonstrate the actual exclusion predicate, but not full mempool/block admission. Do not manufacture nonexistent ring members and present a general rejection as evidence of the genesis-specific check.

## Test procedure

`tools/smoke_native_wallet_regtest.py` uses only temporary, disposable local state. It:

1. Checks the selected 20261026 genesis and compiled mainnet no-mining/no-payout manifest.
2. Launches native `forged` in **FAKECHAIN regtest** with offline mode, fixed difficulty 1 and loopback P2P/RPC listeners; refuses a wrong genesis/nettype.
3. Starts native `forge-wallet-rpc` compiled at the **same source revision**, bound only to `127.0.0.1`. The wallet RPC uses an inaccessible temp wallet directory; all keys, wallet password and signed transaction bytes remain private and are wiped with the directory when the process ends.
4. Creates a **new** wallet with a generated password, confirms a valid public address and zero starting balance.
5. Mines 80 **FAKECHAIN** blocks to that wallet using bounded RPC batches. Refreshes the actual wallet and requires a positive *unlocked* coinbase balance, not just a daemon tip counter.
6. Creates a fresh subaddress, asks the native wallet to construct a signed 16-member-ring transaction for 1.00000000 FRG with `do_not_relay=true`, and checks the serialized transaction, transaction hash and positive fee without writing any secret/raw tx to the CI log.
7. Stops wallet and daemon, deletes keys and chain data; no native mainnet listener, wallet signer for production fees, Stratum payout or public RPC is started.

CI adds a native build of the **actual** `wallet_rpc_server` target to the existing frozen, prelaunch-locked x86_64 full-stack run. Source/unit safety checks run offline on Windows WSL (41 passed as of this handoff). Native wallet runtime result must be verified from the *exact* GitHub run before marking the transaction construction milestone passed.

## Important compatibility caveat

The current Monero-derived `wallet_rpc_server` exposes `--testnet` and `--stagenet`, but no `--regtest`. FAKECHAIN returns the selected mainnet network address prefixes. **Do not assume** wallet daemon compatibility because an RPC port is reachable. The smoke fails closed on wallet-RPC error, refresh failure, missing unlocked funds or failure to construct a transaction. Any future regression-only network-mode support must be isolated from production and reviewed.

## Outstanding separate gates

- Native wallet's signed bytes accepted by the **real FAKECHAIN daemon mempool** and decoded/reconciled to a recipient balance after mined confirmation. Current script explicitly does not relay or submit the signed transaction.
- Complete valid signed transaction with a genesis ring reference rejected specifically inside the native `Blockchain::scan_outputkeys_for_indexes` MAINNET path, under a reviewer-approved *test-only* state setup. A prelaunch-height-1 block check is not equivalent.
- Full wallet payout integration to the running C pool, with isolated real wallet RPC transfer/fee accounting, error/timeout handling, restart/double-spend protection, and durable credited-history audit before enabling any production payout compile flag.
- Independently administered, authenticated node observation; draft consensus PR #185 review; release authorization and public network deployment. These remain unapproved.
