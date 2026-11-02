# POOL-BACKEND-006 — 2026-11-02 — fail-closed daemon block acknowledgment

**Status: source hardening only. No production Stratum, public pool, native mainnet activation, wallet spending, or payout authorization.**

## Change
- Integrate the previously archived `frg_block_submit_receipt.h` parser into the native jtgrassie-derived `rpc_on_block_submitted` callback.
- Reject malformed, null, non-object, errored, and non-`OK` daemon responses before touching the candidate block ledger or statistics.
- Reject missing callback block metadata.
- Persist a candidate block to LMDB **before** incrementing the pool's candidate-count statistics, changing the last-block time, or resetting round effort. Failed LMDB writes leave those counters unchanged.
- Log the distinction between daemon acknowledgment and **canonical-chain confirmation**. Acknowledgment is not proof of reward eligibility, block maturity, or an approved payout.
- Add source-contract ordering checks in `test_source_guards.py`.
- Make the official-pool preflight and Linux compile-only workflows run on relevant pushes to `main`. The preflight also compiles/runs the native JSON-C acknowledgment rejection fixtures.

## Evidence recorded on Windows development workstation
- `py -m unittest discover -s services/official_pool/tests -p 'test_*.py' -v`: **24 tests passed**.
- `py -m unittest discover -s services/pool_settlement/tests -p 'test_*.py' -q`: **45 tests passed** (synthetic prototype only).
- WSL `ForgeCoinBuild`: `gcc -std=c11 -Wall -Wextra -Werror -O2 services/official_pool/tests/test_block_submit_receipt.c -ljson-c ...` and standalone fixture execution **passed**: error-free OK acceptance and 17 malformed/rejected response cases.
- A full compile-only attempt of the C pool on the existing Windows-created Git worktree did **not** pass due to its Windows absolute `.git` worktree reference and unresolvable `serialization/variant.h` include under the WSL mount. Do not claim a successful native pool link/build from this run. GitHub's clean Linux checkout is configured to repeat the compile-only check.
- All operations were limited to source, static tests, and isolated C parsing. **No daemon, mining job, wallet, pool service, blockchain, key or public endpoint was started.**

## Remaining risks and release gates
1. The `main` checkout's native consensus still has **legacy** nonce/address/port values. The frozen 20261026 mainnet source is separate and must be reconciled, peer-tested and independently reviewed.
2. Candidate block acknowledgment is provisional. The canonical-chain lookup, orphan/reorg recovery and 60-block maturity logic require integration tests; the current public dashboard must not present provisional candidates as mature or paid rewards.
3. The upstream/trusted downstream callback and candidate ledger are not a complete idempotent block-recording and financial settlement design. A repeated acknowledgment can still encounter duplicate LMDB entries; review this independently before production.
4. The SQLite settlement journal is **not connected** to authoritative pool LMDB, and wallet payouts remain deliberately compile-disabled.
5. The independent source/ABI security review, actual native mature transfer and payout tests, and matching Windows/ARM64 release builds are still pending.

Continue by evaluating the clean Linux GitHub Actions results, then reconcile the frozen consensus branch and independently test canonical block state transitions. Do not disable safeguards merely to obtain a green build.
