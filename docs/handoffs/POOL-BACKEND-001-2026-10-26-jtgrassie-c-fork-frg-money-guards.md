> **Historical archive — superseded for current configuration.** Original evidence and decisions below retain their original dates and network parameters. Do not use old ports, genesis, balances, token proposals or release claims as current instructions. See [current mainnet specification](../CURRENT_MAINNET.md) and the current roadmap.

# POOL-BACKEND-001 — 2026-10-26 — first isolated jtgrassie C pool fork for native FRG

## Scope and provenance

- **Original repository only:** `https://github.com/tgibbsz32/forgecoin`.
- Baseline `main`: `0fa67adac0bf213bfcdd42311950043d99245844`, containing the merged read-only pool dashboard PR #106. PR #105 continues separately as draft with unfinished native miner/job-refresh research. No files in that working branch, the user's original development checkout or the separate FCMP++/CARROT repository were modified.
- New isolated branch: `feat/pool-jtgrassie-native-money-preflight-20261026`.
- **Implementation commit:** `908cb9bd6c5be9a40145a26979dc95bab30def6f`.
- Imported exactly **28 tracked files** from `https://github.com/jtgrassie/monero-pool`, upstream `master` at `db16e73fcc587a873050a946214f63b6e1bed22a`, into `services/official_pool/jtgrassie/`, retaining all original source headers, `LICENSE`, `rxi/log/LICENSE`, `README.md`, original `Makefile` structure, and other attribution. License is BSD-3-Clause; jtgrassie is **not** presented as endorsing ForgeCoin. This derivative includes our own clearly scoped C changes.

## Actual engineering work completed

1. Added `src/frg_currency.h`: exact strict decimal-text parsing to uint64 atomic units at **8 decimal places** (native FRG `COIN=100000000`), rejecting sign, whitespace, trailing dots, exponent, >8 decimals and overflow. Exact 1% fee uses `amount / 100` integer arithmetic.
2. Modified vendored C `src/pool.c`: native mainnet address prefix **90** (not Monero's 18); payment threshold is a strict parsed **uint64 atomic value**, not `1000000000000 * payment_threshold`; 1% operator fee deduction does not multiply balances by a floating-point `config.pool_fee`; incoming non-1% fee policy is refused. Pool and statistics listeners default to loopback and native FRG RPC port 19481.
3. Modified vendored `src/webui.c` to render personal balances from atomic units with integer division/remainder and **exactly eight decimal places**. The production-facing Python dashboard bridge added in PR #106 continues to **suppress all personal balances**, since native wallet/payout provenance is still unreviewed.
4. Research startup fail-closes on non-loopback listeners, hash-check bypass, enabled payouts or enabled self-select. Wallet execution is independently gated out by default at `send_payments()` unless a deliberately reviewed build path opts in. No active pool wallet address is included; the sample `pool.conf` requires an explicitly configured disposable pool address and sets wallet RPC port **0**.
5. Pinned the build to an explicit `FORGECOIN_ROOT` path, optionally `FORGECOIN_BUILD_ROOT`, and renamed the binary target `forgecoin-pool`. This does not yet establish successful linking or daemon/wallet ABI compatibility.
6. Added `services/official_pool/README.md`, stand-alone C regression `tests/test_currency.c`, six offline source/preflight tests `tests/test_source_guards.py`, and a GitHub Actions workflow for Ubuntu/Windows source guards plus native C testing on Ubuntu.

## Reproducible tests and exact results

- Windows MSYS2 MinGW64 GCC compiled the standalone C helper with `-std=c11 -pedantic -Wall -Wextra -Werror -O2`; **40 strict amount/fee checks passed**. Included zero, 1 atomic FRG unit, 0.33 FRG, 50 million FRG, `UINT64_MAX`, malformed text, overflow, and amount/fee rounding.
- Ubuntu WSL GCC separately compiled and ran the **same 40 native tests**, with the same strict warning/error settings: **40 passed**.
- `python -m unittest discover -s services/official_pool/tests -p 'test_*.py' -v` on Windows Python 3.13: **6 passed, zero failures**. These verify this checkout's consensus units/prefix and block target, FRG fee threshold and guard wiring, localhost/no-wallet config, upstream license, and explicit build source pin.
- All newly authored files passed `git diff --cached --check`. Whole vendored source retains inherited upstream trailing spaces and blank end-of-file lines, so a plain all-files whitespace check flags **original upstream formatting**; a check disabling those two inherited whitespace classes passed, preserving upstream source attribution without unnecessary normalization.
- **No full C/C++ pool build or link was completed.** Ubuntu's available WSL environment lacked `libevent`, `json-c`, `LMDB` developer headers and a reviewed matching ForgeCoin release library tree. No MinGW or Windows full backend build was attempted. No block was mined, submitted or credited. No wallets/funds/mature payouts, existing node installations or public network were touched.

## Significant unresolved correctness and security blockers

- The native C backend is a **research fork and currently cannot be regarded as production-functional**. jtgrassie C++/RPC/RandomX interfaces still require an actual end-to-end port/build/link against reviewed ForgeCoin daemon and wallet revisions. All transfer and address validation paths need security testing.
- Native mainnet prefix 90 is reflected in source but validated native base58 address handling, testnet/stagenet prefixes, and independent genesis/nettype identity are not yet proven.
- The PPLNS allocation formula in upstream `src/pool.c` still uses floating-point `floor(...)` and has not been checked for exact conservation, fees over rounding boundaries, orphan/reorg maturity, LMDB crash/recovery or final payouts. A deterministic 1% per-allocation fee helper alone **does not prove correct pool economics**.
- There has been **no accepted-block test** using this C backend, nor a test with external XMRig miners against this fork. Existing Python/native RandomX research under PR #105 does not substitute for testing the C daemon, Stratum and block submission path.
- No official pool signer, 100-worker load test, user statistics/payout API, audited production TLS configuration or operator approval exists. Prelaunch pool website still must show no live mining or balances.

## Next exact task

Create a reproducible isolated Linux build against the **matching ForgeCoin** source commit, installing the non-sensitive C dependency libraries in a disposable builder; resolve Monero-version C++ ABI and C header incompatibilities; test all signed/unsigned amounts and FRG address/nettype handling; then test actual daemon-generated Stratum jobs and canonical accepted-block submission on a disposable chain. After native payout reconciliation and 60-block maturity tests, connect verified aggregate stats to the already merged frontend. Do not remove compile-time payout safeguards, enable public listeners, or create a production miner endpoint without independent release authorization.

Commit a new numbered dated handoff after each subsequent completed step. This handoff records only work confirmed by commands, tests, and Git commits.
