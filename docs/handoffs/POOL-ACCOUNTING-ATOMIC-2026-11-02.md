# ForgeCoin research-pool PPLNS accounting safety — November 2, 2026

**Scope:** Source-level hardening of the actual jtgrassie-derived C pool, without starting
the pool, connecting to a wallet, enabling Stratum, spending FRG or changing Oracle.

## Risks found in original native allocation path

1. Share allocation used a floating-point expression converted directly to
   `uint64_t`, followed by `total_paid + amount > block->reward`. For extreme
   values this can invoke out-of-range conversion behavior or 64-bit addition overflow.
2. The required 1% fee was deducted even when `pool_fee_wallet` was absent,
   silently stranding the deducted fee.
3. A failed fee `balance_add` only logged the error, allowing subsequent miner
   credits to proceed before committing the ledger.
4. The block could be marked `BLOCK_UNLOCKED` even after its share walk ended
   without accounting for the full canonical reward. Some PPLNS rounding
   combinations can leave dust, which needs deliberate future handling.

## Changes

`frg_pplns_accounting.h` provides bounded share allocation based on positive
finite difficulty and share multiplier. The remaining reward is calculated by
**subtraction**; proposed amounts are capped **before** conversion to a 64-bit
atomic value. Source `pool.c:payout_block` calls this helper and uses the
existing exact `frg_pool_fee_atomic(amount)` (integer divide by 100).
A configured and previously validated operator fee wallet is mandatory for
accounting; failure to credit even one fee immediately aborts the same nested
LMDB transaction as miner balances. Incomplete reward allocation aborts that
transaction and returns `EPROTO`, leaving the candidate locked for explicit
reconciliation. The cursor is closed on all new failure paths and on success.

The fallback is deliberately **fail closed**, not a dust-redistribution algorithm.
It may defer a previously partly allocated reward until a reviewed exact
reconciliation solution is implemented. The pool already disables actual
wallet transfers at compile time (`FRG_TESTED_WALLET_PAYOUTS`) and by
configuration (`disable-payouts=1`, wallet RPC port 0).

## Test evidence and remaining work

- The native C regression `test_pplns_accounting.c` checks quarter-share
  allocations, exact 99% miner / 1% operator ledger conservation, clamps near
  `UINT64_MAX`, all-zero balances, NaN/Inf, invalid difficulty, and refusal
  to mark incomplete allocation as settled.
- The source regression asserts that `payout_block` actually calls the helper,
  requires a fee wallet, aborts LMDB on fee errors, and does not unlock partial
  share allocations.
- Local `gcc -std=c11 -O2 -Wall -Wextra -Werror -pedantic` tests and 26 Python
  pool source checks passed. Independent x86_64 and AArch64 native pool
  link/compatibility CI must pass before merging.
- **Still required for production:** deterministic share rounding/dust policy,
  actual LMDB failure injection and rollback verification, canonical 60-block
  orphan/reorg reconciliation, tested native wallet `transfer_split`, treasury
  address verification and payout-ledger audit. There is **no funded/tested
  real FRG payout**; do not relax compile-time or network guards.

This PR is NOT public pool activation or release authorization. The frozen
FRG network ports remain P2P 39480, daemon RPC 39481, ZMQ RPC 39482.
