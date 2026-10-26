> **Historical archive — superseded for current configuration.** Original evidence and decisions below retain their original dates and network parameters. Do not use old ports, genesis, balances, token proposals or release claims as current instructions. See [current mainnet specification](../CURRENT_MAINNET.md) and the current roadmap.

# POOL-BACKEND-003 — 2026-10-26 — first real native x86_64 pool link and ARM64 flag preflight

## Repo scope and exact implementation

- Original FRG repo only: `https://github.com/tgibbsz32/forgecoin`, main baseline `cf76794731c2d4bc310b7f4d4b744173809e308f` (PR #108 already merged).
- Branch: `feat/pool-low-memory-native-static-20261026` in a **new, isolated Windows checkout**. All WSL builds used a separate fresh Linux Git clone at commit `cf76794731c2d4bc310b7f4d4b744173809e308f`.
- Source implementation commit: `19306bc12cc0f91c48487a436f557ba3d8616d17`.
- Neither the user's existing uncommitted consensus checkout, separate FCMP++/CARROT repo, unfinished mining-job research worktree, nor public Oracle VM was edited or reset.
- **No production pool, daemon, wallet RPC, Stratum, payouts, blocks or FRG funds were touched.**

## Actual changes

- `services/official_pool/tools/build-native-static.sh`: a pinned Linux native-library builder that requires an exact 40-character Git commit, a clean tracked source tree and a build directory underneath it. Refuses mismatched CMake caches, non-FRG source trees, or unsupported architectures. Uses `FRG_BUILD_JOBS=1` by default; fails closed on >1 job with <4 GiB physical RAM and >2 with <8 GiB. Builds eleven native ForgeCoin static-library targets and asserts all output archives are nonempty before printing success. **Does not link or run a mining pool**.
- `services/official_pool/jtgrassie/Makefile`: fixes Intel-only `-maes` compiler flag being unconditionally passed to native ARM64. Flags now use `-fPIC` on both platforms and `-maes` only for x86_64/amd64; aarch64 is explicitly supported, other unknown CPUs refused.
- `.github/workflows/pool-native-static-link-ci.yml`: a separate ephemeral Ubuntu 22.04 x86_64 runner builds the libraries, links the C pool, verifies 64-bit x86 ELF PIE and checks runtime shared libraries; **does not start or publish** its executable, deploy to Oracle or enable payouts.
- `services/official_pool/tests/test_native_static_gate.py`: 5 source-level tests for provenance, low-memory bounds, eleven library targets, ARM-safe flags and CI never launching/publishing the pool.
- `services/official_pool/README.md`: concrete reproducible build procedure, SHA evidence, resource and launch warnings.

## Actually executed evidence

1. A fresh original ForgeCoin clone at `cf76794731c2d4bc310b7f4d4b744173809e308f` configured successfully with CMake 3.22.1/GCC 11.4.0 on the separately owned `ForgeCoinBuild` WSL Ubuntu 22.04 x86_64 environment. Installed missing developer libraries `libboost-locale-dev`, `libzmq3-dev`, and `libreadline-dev` in that isolated WSL distro. These installs **did not** modify the Oracle VM.
2. An initial `cmake --build ... --parallel 8` caused the dedicated WSL environment to become temporarily unresponsive. The specific `ForgeCoinBuild` distro alone was terminated and restarted successfully (**no global `wsl --shutdown`**). On restart WSL reported **1.9 GiB RAM, 1 GiB swap**. No existing user repo worktree was modified.
3. Repeated at `--parallel 1`: **all eleven pinned native cryptonote, wallet-crypto, RandomX, epee and related static targets built**; compiler exit code 0. The new `build-native-static.sh` was subsequently invoked against the same **exact commit**. It rejected `FRG_BUILD_JOBS=8` on the low-RAM host, then passed at `FRG_BUILD_JOBS=1`, confirming eleven real nonempty static archives.
4. `make link-preflight TYPE=release FORGECOIN_ROOT=<isolated source> FORGECOIN_BUILD_ROOT=<current built lib directory>`: **passed**. `make -j1 release` compiled the C pool and C++ bridge and **linked `build/release/forgecoin-pool` successfully** against those exact native static libraries (exit code 0). Binary **never executed**.
5. `file` reports **ELF 64-bit LSB PIE executable, x86-64**, GNU/Linux; `readelf -h` reports ELF64, DYN position-independent executable. `ldd` found all shared dependencies locally, with **no missing libraries**. The isolated linked binary's SHA-256 is:
   `c9d6654998f71918d88247e4baac49fb6c9cba6b2ea512cc66e8aeca1089b05b`.
   It was not copied to any production host, committed, uploaded, run, or released.
6. Full Windows Python source preflight suite: **14 tests passed**. Native MinGW FRG monetary parser + exact 1% fee: **40 checks passed**. WSL Bash syntax: passed. A native build script safe-default test rejected eight jobs, then completed eleven targets. Make dry-run `ARCH=aarch64` confirmed **no Intel `-maes` in compilation commands**, and `ARCH=x86_64` retained it. **This is a compiler-flags dry run, NOT an ARM64 compile.**
7. `git diff --cached --check`: passed before code commit.

## Unresolved release-critical findings

- **No ARM64/aarch64 build or link has yet been executed**. A Linux x86_64 executable is architecturally incompatible with the existing Oracle Ubuntu ARM64 Free Tier VM. ARM64 toolchain, native source archives, C pool executable, dependency linking and resource/startup checks still require on-target or equivalent isolated ARM64 validation before private staging.
- The C pool executable was **never launched**, therefore real daemon RPC, native RandomX Stratum/XMRig share acceptance and canonical block submission **are not proven by this step**. Successful native linking is not evidence of operational mining.
- Public listeners and wallet payouts are still disabled by research-build guards, with no real pool wallet setup or address enrollment.
- No accepted native block, canonical PPLNS conservation, 1% operator-fee settlement, 8-decimal mature payout signing, 60-block maturity/reorg/restart recovery or security/load tests yet.
- Inherited warning: upstream Supercop `sc25519_window4` has a declared `signed char[85]` versus implementation `signed char[64]` and the compiler emits potential overflow warnings. Deprecated OpenSSL 3.0 RSA/EC APIs were also warned. These must be independently assessed; do not silently mark security gates passed.
- The user's Windows WSL config warned of duplicate `wsl2.memory` keys. We did **not** change `.wslconfig` or other global WSL settings. Use one-job builds on the current 1.9 GiB builder.

## Next task — directly gated by this result

Obtain an isolated aarch64 Ubuntu builder (or carefully use the already running Oracle VM without affecting its existing daemon/explorer), reproduce this source-pinned native library build with conservative concurrency, compile and link the jtgrassie C pool on ARM64 **without running it on the live node**, then verify ELF machine/ABI/dependencies and self-contained localhost startup tests with empty wallets/payouts disabled. Do not install a persistent Oracle service or expose ports until the ARM64 binary and private integration tests pass. Public mainnet requires much more: canonical accepted-block proof, durable PPLNS, mature payouts, signer isolation and security review.

No automatic background work is scheduled; this handoff records only work directly performed and verified.
