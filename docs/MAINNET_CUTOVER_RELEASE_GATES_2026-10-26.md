# ForgeCoin 20261026 — single authoritative new-mainnet cutover

**Release classification: PRELAUNCH / NOT AUTHORIZED.** No public miner
connections, block-1 PoW, pool payouts or treasury transfers are permitted
until all below gates pass. This repository branch is source for a candidate
**new mainnet**, not a public announcement or completed release.

## Decision and evidence

The original development chain ran on Oracle at RPC `19481` with genesis
nonce `10000`, 518 mined blocks (RPC height `519`) and zero peers at
final inspection. The prior fresh candidate with genesis nonce `20261020`
ran a private/offline smoke chain whose saved RPC height was `3`
(genesis + **two** mined blocks). Both are **disqualified** from launch.
The new mainnet MUST NOT reuse the same genesis hash or network UUID.
Two previously developed chains are not migrated into this new network.

**On October 26, 2026**, the two Oracle services
`forgecoin.service` and `forgecoin-mainnet-staging.service` were
stopped and disabled. Their original LMDB data were moved out of the
active paths into private archives under:

```text
/home/ubuntu/forgecoin-chain-archives-20261026/development-lmdb
/home/ubuntu/forgecoin-chain-archives-20261026/candidate-20261020-smoke-lmdb
```

Integrity-checked tar backups, retained privately on Oracle:
- development tar SHA-256:
  `878fbdc36aa5553af5df583e8ffdc5c72df0efcf9f6021554e6b45b9b2826df6`;
- candidate tar SHA-256:
  `9778a453e6506ed6ea04aa9c1d8dfe1e036771634b50e304f9dccd66a191998d`.

This is a **reversible archive**, not data destruction. Do not restart either
old service or copy old LMDB/peer state into the new network. Existing
development balances do not migrate by default. Owner's old encrypted
wallet files and recovery information must not be deleted.

## Single authoritative chain configuration

The machine-readable source of truth is `config/mainnet.identity.json`.
Release tooling and components MUST validate it. These are deliberate
differences from the rejected candidate:

| Field | Fresh mainnet PRELAUNCH |
| --- | --- |
| Genesis nonce | `20261026` |
| Network UUID | `bd936359-09e4-4fdb-8ec0-12fa9d6ef090` |
| Primary/integrated/subaddress prefix | `190 / 191 / 192` |
| P2P / daemon RPC / ZMQ RPC | `39480 / 39481 / 39482` |
| Genesis hash | `4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c` verified at offline RPC height 1 |
| Starting difficulty | `500000` |
| Minimum difficulty | `400000` |
| Fixed difficulty | Mineable heights 1–15 |
| LWMA adjustment | Height 16, window 90 |
| Target block time | 120 seconds |
| Emission constant | 50,000,000 FRG (matching candidate) |
| Atomic units | 100,000,000 per FRG |
| Genesis coinbase output | 1,192,092,895 atomic units = 11.92092895 FRG |

The source restores the **actual consensus implementations** from the
preserved 20261020 candidate rather than only switching a port. The new
nonce and UUID make it a distinct network. The genesis transaction bytes
remain equal to those in the prior candidate, deliberately preserving the
agreed emission schedule. **Permanent unspendability of the genesis output
has NOT been proven**. A 60-block coinbase unlock is insufficient proof.
This remains a release blocker and requires independent transaction
traceability/unspendability analysis or a consensus-level explicit
restriction before describing issuance as zero-premine.

## Components and isolation

- **forged / wallet-cli / wallet-rpc:** must be rebuilt from this exact source
  commit, not borrowed from the old Windows binaries. No legacy peers or
  checkpoints. Start only with fresh, isolated new-mainnet data directories.
- **Windows Forms desktop:** RPC `39481`, P2P `39480`, separate
  blockchain/wallet/ring data directories tagged `mainnet-20261026`.
  The Windows UI can create wallets; **solo and pool mining are prelaunch-locked**.
  No public fresh-mainnet peer is configured before launch.
- **Tauri desktop:** same new node endpoints, isolated chain and wallets,
  reject settings that still select old RPC/P2P ports. Mining remains
  prelaunch-locked until the new network is explicitly approved.
- **Explorer:** RPC `127.0.0.1:39481`, rejects an upstream daemon with
  genesis nonce other than `20261026` or non-mainnet nettype. Upgrade the
  identity check to the **exact genesis hash** before public deployment.
- **C pool:** only use address prefix `190` and daemon RPC `39481`.
  Missing, wrong-network or duplicate operator fee wallet is fatal; miner
  fees must never vanish into an unassigned address. All research payout,
  public-listener, and hash-bypass safeguards stay enabled.
- **Pool dashboard:** must not show the old chain as active or invent stats;
  the current static readiness site stays in prelaunch mode.
- **Governance:** FRG staking remains unimplemented; no on-chain voting
  eligibility or wallet locking is launched by this cutover.

## Non-negotiable release tests

1. **Genesis-only test:** build actual matching Windows + ARM64 binaries,
   create an isolated NEW data dir, run daemon with `--offline`, no miner,
   localhost P2P/RPC only. RPC `height == 1`; block 0 header nonce matches
   `20261026`; freeze and publish full unique SHA256 genesis hash.
2. **No unintended mining:** no `start_mining` or block submission on the
   launch genesis. Consensus/fork tests run on FAKECHAIN/testnet or explicitly
   separate throwaway networks with different genesis/UUID.
3. **Genesis preallocation:** prove 11.92092895 FRG unspendable or implement
   and independently verify a rule that prevents spending it.
4. **Diff/PoW:** preserve validated candidate difficulty 500k/400k,
   transition at 16 and LWMA N=90; independently confirm there is no
   changed reward or mining allocation compared with previous candidate.
5. **Client safety:** Windows/Tauri/CLI/wallet/installer all use the same
   approved genesis binary and distinct fresh directories; reject old
   peers, wallet network mismatches, and old genesis.
6. **Pool:** genuine Stratum/RandomX canonical accepted-block processing,
   integer fee reconciliation, maturity, reorg and crash recovery, and
   wallet payout validation on a distinct disposable test chain.
7. **Website:** explorer verifies full genesis hash and does not serve
   development blocks as live; pool metrics are real and fail closed.
8. **Release:** transparent genesis disclosure, signed SHA-256 checksums,
   operator's locally owned treasury wallet and separate pool hot wallet,
   ARM64 and Windows binaries, owner approval, and coordinated public
   announcement before allowing the **first mined block 1**.

A real mainnet once launched can advance past height 1 normally. The
restriction above is only to prevent **premature mining during
development**, not to forbid legitimate mining after official launch.

Use `python tools/verify_mainnet.py --allow-unfrozen-prelaunch` for
READ-ONLY genesis validation against localhost `39481`. It will refuse
a mined chain during this stage. This flag never authorizes mining.
