# Native FAKECHAIN confirmed transfer acceptance — November 4, 2026

**Scope:** Draft and test-only. Extension of the verified wallet-mempool integration in [PR #203](https://github.com/tgibbsz32/forgecoin/pull/203). No mainnet activation, production payout authorization, public Stratum, Oracle deployment, or seed/key handling is allowed.

## Verified prerequisite — November 4

- [Native x86_64 workflow 41775386686](https://github.com/tgibbsz32/forgecoin/actions/runs/41775386686) and [ARM64 workflow 41775386697](https://github.com/tgibbsz32/forgecoin/actions/runs/41775386697) passed on PR #203 revision `ab9c4219b5a47afc823f380709f336a273b24b94`.
- The x86_64 runner log explicitly shows: distinct native wallet and daemon built from the same revision, empty new wallet, 80 mined FAKECHAIN blocks with unlocked funds, a signed native 16-member-ring transaction, then **daemon mempool acceptance** with `do_not_relay=true` and exactly one matching transaction hash.
- A mempool entry is neither confirmed recipient credit nor a production payment.

## New proposed acceptance: separate payee and mined confirmation

The `--confirm-transfer` gate in `tools/smoke_native_wallet_regtest.py` is invoked *only* with `--signed-transfer --validate-mempool`. It extends the isolated native wallet test:

1. Require the prelaunch, payout-locked manifest and frozen 20261026 genesis. Run one **offline, loopback-only FAKECHAIN** daemon at fixed regtest difficulty 1, with isolated temporary chain data and random local ports. No public peer or mainnet listener.
2. Build and launch **two genuinely distinct native wallet RPC processes**, each with a fresh password-protected wallet and private temporary directory. RPC listens on localhost only, has `--no-dns`, and all generated secrets and raw transaction bytes are excluded from logs.
3. Mine 80 valid FAKECHAIN blocks solely into the sender wallet and require unlocked owned coinbase funds. Require the recipient's wallet to start empty.
4. Sign a **1.00000000 FRG** 16-member-ring transfer addressed to the *other* wallet, `do_not_relay=true`; require the same ephemeral daemon to accept it into its mempool once with sanity checks enabled.
5. Mine exactly one extra local-only FAKECHAIN block. Verify the daemon's canonical block at height 81 contains exactly the signed hash once, and verify the receiver wallet refreshes through chain length 82.
6. Require the receiver to show **exactly 100,000,000 atomic FRG** in its balance and **exactly one confirmed incoming wallet transfer** with the correct tx hash and amount. Reject unknown hashes, absent block inclusions, duplicates, mismatched amounts, or missing credit.
7. Stop both wallet processes and daemon, delete all temporary wallets/keys/chain data. This integration test does **not** create pool payouts or change the release lock.

The source/unit regression checks forbid enabling confirmation without the signer+mempool gates and reject fabricated or contradictory block, receipt, and amount evidence.

## Interpreting results

**Pending native CI on this new branch.** Do not mark confirmed recipient settlement accepted until the exact workflow head runs green and the log includes the independent-wallet credit PASS line. A Python source/unit success does not substitute for native runtime.

Still P0 before any public launch:

- Actual signed genesis-output ring-spend rejection through MAINNET native full transaction input/mempool validation, reviewed in a controlled test-only context.
- Independent operator/provider chain consensus and independently authenticated observer RPCs.
- C-pool payout integration, recipient confirmation, restart/idempotency and deep-reorg quarantine before spend, fee reconciliation and owner-reviewed signing paths.
- Frozen consensus draft PR #185 approval; port/Oracle/firewall auditing; x86_64 Windows and Android ARM64 wallet/miner shipping and installation validation.

**Non-negotiable lock:** `release_authorized=false`, `mined_blocks_permitted_before_launch=0`, `stratum_public=false`, `payouts_enabled=false`; no static/mainnet consensus lock change in this PR.
