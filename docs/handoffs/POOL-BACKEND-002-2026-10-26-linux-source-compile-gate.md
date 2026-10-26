> **Historical archive — superseded for current configuration.** Original evidence and decisions below retain their original dates and network parameters. Do not use old ports, genesis, balances, token proposals or release claims as current instructions. See [current mainnet specification](../CURRENT_MAINNET.md) and the current roadmap.

# POOL-BACKEND-002 — 2026-10-26 — compile jtgrassie source against native FRG headers

## Repository, provenance and isolation

- Active project: **original** `tgibbsz32/forgecoin`, not the separate FCMP++/CARROT repository.
- Base original `main`: `b01f77feb3658c962c5ece6b24a4a3e3094c095a`. PR #107, the first licensed C pool fork and 8-decimal FRG money guard, was already merged by the beginning of this step.
- Isolated checkout/branch: `feat/pool-jtgrassie-linux-build-preflight-20261026` in `%TEMP%\forgecoin-jtgrassie-linux-build-20261026`. The user's original Windows Monero/FRG consensus checkout and unfinished native RandomX research branch were neither reset nor edited.
- **Implementation commit:** `fbd7c5504e4584cef3fe3e51b6025238a8efedcd`.
- Work was done through the authorized Remote Desktop Commander on the user's Windows workstation. No production Oracle node, mainnet, live pool, real wallet keys, block, miner funds or external pool endpoint was used.

## Exact work implemented

1. `services/official_pool/jtgrassie/Makefile`: add `compile-check` which compiles the complete native C pool, C++ ForgeCoin source bridge and bundled HTML into **nine Linux object files**, but **never links a pool executable**. Add explicit order-only dependencies ensuring directories exist before parallel compilation.
2. The same Makefile adds a `link-preflight` gate which checks every required native ForgeCoin static archive for the current target architecture, reports all missing paths, and aborts **before** running the linker if any are absent. A missing CMake cache no longer triggers unrelated noisy grep warnings during compile-only checks. This improves safe reproducibility; it does not implement a payout or mining backend.
3. `services/official_pool/tests/test_linux_build_guards.py`: three tests verify the non-linking compile-only target, missing-archives link gate, explicit source-root pin and continued public-listener/payout compile-time safeguards.
4. `.github/workflows/pool-native-linux-object-compile.yml`: Ubuntu 22.04 **x86_64** GitHub Actions job, installing native C dependency headers, running existing source tests and compiling all nine objects without linking or producing a working pool.
5. `services/official_pool/README.md`: compile instructions, link blockers and criteria for private Oracle ARM64 staging versus official public launch.

## Actually performed Linux build and tests

- Isolated build environment: **ForgeCoinBuild WSL Ubuntu 22.04 x86_64**, GCC/G++ 11.4.0, make. Installed **non-sensitive developer dependencies in this dedicated WSL distro** (libevent, LMDB, json-c, libsodium, unbound, uuid, OpenSSL, selected Boost libs, hidapi, USB and xxd). The apt cache was initially stale, returned 404 for obsolete updates; an `apt-get update` followed by installation resolved this.
- After dependencies were available, `make -C services/official_pool/jtgrassie -j2 release FORGECOIN_ROOT=<current isolated checkout> FORGECOIN_BUILD_ROOT=/tmp/frg-pool-missing-consensus-build`: **all nine sources compiled successfully**, including `src/pool.c`, `src/webui.c`, `src/xmr.cpp` and embedded UI. The **final executable link FAILED**, because eleven required ForgeCoin native static `.a` archives were not built in the supplied isolated Linux build directory. The existing prior Windows `.a` artifacts cannot serve as Linux-native link targets.
- A clean debug `make -j2 compile-check` succeeded; then a separate **release** `make -j2 compile-check TYPE=release FORGECOIN_ROOT=<isolated checkout> FORGECOIN_BUILD_ROOT=/tmp/frg-pool-missing-archives-20261026` succeeded and printed `PASS: compiled all ForgeCoin pool C/C++/web UI objects (NOT LINKED)`.
- `make link-preflight TYPE=release ...` was deliberately given the missing archive path and **correctly FAILED with names of all eleven missing archives** and an explicit instruction to build native FRG static libraries. No `build/release/forgecoin-pool` executable was created.
- `python -m unittest discover -s services/official_pool/tests -p 'test_*.py' -v`: **9 passed, 0 skipped/failures** on Windows Python. Existing FRG currency/1% fee C regression compiled under MinGW and passed **40 checks**. The 40 checks were also previously compiled under Ubuntu GCC; this change did not alter FRG currency code.
- `git diff --check`, staged author-file check: **passed**. No live blockchain activity, reward credits or payouts occurred.

## Outstanding release blockers — honest status

- **No linked ForgeCoin C pool binary has yet been built** (Linux static native daemon/cryptonote/wallet/RandomX libraries missing); therefore cannot install the jtgrassie pool on Oracle yet.
- The successful source compile was **x86_64**, whereas the Oracle Free Tier VM is **ARM64/aarch64**. A matching native ARM64 ForgeCoin static library build and ARM64 pool compile/link, startup tests and resource checks are prerequisites for **private Oracle staging**.
- This static backend has not passed real daemon RPC compatibility, accepted canonical native FRG block submission, new-block job renewal, worker authentication, PPLNS conservation, 1% fee and 8-decimal payout reconciliation, 60-block maturity, orphan/reorg and restart recovery, wallet-transfer failure/retry, external audit or 100-worker load testing.
- Payouts and public interfaces remain **disabled** by default and by code guards; this change does not authorize public operation or live wallet access.

## Next concrete action

Build current reviewed ForgeCoin source into native Linux static libraries in an isolated reproducible builder, and run `make release` against the matching library tree with all prelaunch safety macros intact. Reproduce the same build on **ARM64** before installation on the user's Oracle VM. Once ARM64 binary boots and tests with the native daemon via localhost, install **private staging only**; do not expose Stratum/payments until canonical accepted blocks, mature payouts, accounting security and operator review pass.

Continue to commit numbered dated handoffs for each actual implementation step. Do not mark the official pool or Oracle installation complete until the executable and on-target tests exist.
