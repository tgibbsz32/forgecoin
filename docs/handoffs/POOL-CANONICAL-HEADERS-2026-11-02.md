# Official pool canonical-header response safety — November 2, 2026

This source-only security fix addresses reward reconciliation in the
jtgrassie-derived ForgeCoin C pool. It does not enable public Stratum,
transfer any funds, alter Oracle, or authorize the locked native mainnet.

## Confirmed source defect

The pool requests ten mature block headers through
`get_block_headers_range(start_height, end_height)` but previously copied
however many headers the daemon returned into a **shared ten-entry array**
and invariably called `process_blocks(shared_array, 10)`.

A short response could therefore replay stale headers from the preceding
range, and an overlong response could write past the array's bound.
Response heights, parent links and field types were not validated before
the pool ran maturity, orphan-status and reward-crediting callbacks.
Concurrent/out-of-order responses shared this same mutable array.

## Source correction

- An RPC callback carries its **own expected start/end heights**; the normal
  callback destructor releases that allocation when the request completes.
- `frg_canonical_headers_valid` rejects missing, short, oversized, or
  out-of-order arrays; verifies every expected height and positive difficulty;
  validates typed timestamp/reward/orphan-status and exactly 64 hex digits
  in block/parent hashes; and checks the inter-header parent-hash chain.
- The only accepted response is converted into a **zero-initialized local
  block buffer**. Only the verified count is passed to `process_blocks`.
  No global stale header buffer remains. The compile-time window length is
  asserted to match the native C validator limit.
- Failed validation returns without changing any LMDB balance or block
  status. Errors during reconciliation are separately logged.

## Verification and release limits

The standalone `services/official_pool/tests/test_canonical_headers.c`
native json-c fixture tests a correct ten-header chain, exact ten-count
bounds, shorter/longer arrays, wrong requested start/end, repeated heights,
mismatched parent, malformed hash, negative reward, missing or mistyped
orphan-status and invalid difficulty or timestamp. It is wired into the
source compatibility preflight and native Linux x86_64 and ARM64 pool CI.

Local strict C compilation (`gcc -std=c11 -Wall -Wextra -Werror -pedantic`)
and Python pool source guards passed before review. Passing an isolated
header fixture does **not** prove daemon canonicality, live race resistance,
or block reward transfer correctness. Additional required gates include
a controlled 60+ block live-pool ledger fixture with orphan/reorg injection,
recorded hash/parent/height disagreement across daemon callbacks, exact
operator-fee ledger reconciliation, wallet transfer signing and external
security review. The selected mainnet remains disabled with P2P 39480,
daemon RPC 39481, ZMQ RPC 39482. Payouts and public Stratum stay locked.
