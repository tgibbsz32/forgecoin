# Native FRG recipient restart/reconciliation acceptance — November 4, 2026

**Test-only milestone; no mainnet activation or payout authorization.**

## Verified prerequisite

[Draft PR #203](https://github.com/tgibbsz32/forgecoin/pull/203) incorporated [PR #204](https://github.com/tgibbsz32/forgecoin/pull/204) at `3fa0ec0110c9e1157d1d139e1d265e8ccde64d6b`, on the **isolated prelaunch validation branch**, not public main.

The [native x86_64 acceptance run 41792342842](https://github.com/tgibbsz32/forgecoin/actions/runs/41792342842) and [ARM64 run 41792342746](https://github.com/tgibbsz32/forgecoin/actions/runs/41792342746) PASSED on PR #204's head `c3db545851e52b7db6f7d675a786f27ee134e397`. The actual x86_64 native runtime log confirms a distinct empty recipient wallet, a genuine signed 16-member-ring FAKECHAIN transfer accepted exactly once in the local daemon mempool, then a genuine block containing that transaction and **exactly 100,000,000 FRG atomic units** recorded as one incoming transfer by the separate wallet.

## New next gate: durable recipient history across wallet RPC restart

The `--verify-restart` switch requires `--confirm-transfer`, `--validate-mempool` and `--signed-transfer`. Following a successful confirmed transfer on the same isolated offline FAKECHAIN:

1. Ask the separate recipient's real native wallet RPC to close and save its wallet (`close_wallet`).
2. Terminate its native wallet RPC subprocess, wait for exit and start a **new native wallet RPC process** from the same exact reviewed binary with unchanged localhost-only daemon and RPC bindings, private wallet directory, and `--no-dns`.
3. Reopen the exact same wallet with its previously generated password (never print that password, wallet address or seed).
4. Require the recipient public address to equal the pre-restart address; refresh to chain length 82, verify same canonical confirming block and frozen genesis.
5. Require **exactly one** inbound entry for the original signed transaction hash and 100,000,000 atomic FRG, the exact same balance, and an identical confirmed incoming transaction history as before restart.
6. Shut down every native test process and remove the private temporary wallet, daemon, chain and log directory.

An offline unit guard rejects restart assertions if confirmation has not already been required. Neither a successful unit test nor a signed mempool transaction alone counts as a durable recipient credit.

## Evidence standard and remaining blockers

**New native CI pending.** Do not claim wallet RPC restart persistence accepted until the exact x86_64 native job passes and prints its `PASS: separate payee wallet closed, native RPC process restarted` line.

Still P0 for public mainnet: reviewer-approved full signed genesis-output ring attempt rejection in MAINNET consensus input validation; independently operated node comparison/eclipsing safeguards; genuine native C-pool payer wallet, payout/retry/journal, confirmed recipient/1% fee/reorganization reconciliation; formal mainnet draft #185 review; Windows and Android release builds plus install validation; Oracle network-ports/firewall/health cutover. Public mining and pool payouts remain disabled.
