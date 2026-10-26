> **Historical archive — superseded for current configuration.** Original evidence and decisions below retain their original dates and network parameters. Do not use old ports, genesis, balances, token proposals or release claims as current instructions. See [current mainnet specification](../CURRENT_MAINNET.md) and the current roadmap.

# POOL-BACKEND-004 — 2026-10-26 — native ARM64 C pool link CI gate

## Original ForgeCoin scope and repository state

- Original repository: `https://github.com/tgibbsz32/forgecoin` only.
- Base `main`: `32c9a38fd73270cdd65f119fa5c3a2dab87ab435`. PR #109 Linux x86_64 full static-library + C pool link already merged.
- Isolated checkout/branch: `feat/pool-native-arm64-link-ci-20261026`, created without touching the user's original local uncommitted consensus files, prior PR #105 native RandomX research worktree, or separate FCMP++/CARROT repository.
- Implementation commit: `19043c6bbe6be52e070041f23068b64128b15e62`.
- GitHub draft PR #110: https://github.com/tgibbsz32/forgecoin/pull/110.

## Work actually authored and executed

1. Added `.github/workflows/pool-native-arm64-link-ci.yml`, which uses the actual **native ARM64** runner `ubuntu-24.04-arm`, verifies `uname -m=aarch64`, installs development dependencies on a throwaway GitHub runner, tests strict FRG 8-decimal amounts, and validates the native research guards. Before building, a Makefile dry-run verifies Intel x86 `-maes` is absent from native ARM64 compiler flags.
2. The workflow runs the existing commit-pinned and RAM-bounded `services/official_pool/tools/build-native-static.sh` to produce the eleven ForgeCoin cryptonote/wallet-crypto/RandomX native static archives. It then links the jtgrassie-derived C pool **without running it** and validates ELF64, `Machine: AArch64`, PIE and shared library resolution. Computes a build hash but does not upload/expose the executable.
3. Added four source-contract tests to `services/official_pool/tests/test_arm64_workflow_gate.py` and documented the exact staging restrictions in `services/official_pool/README.md`.
4. Ran the complete Windows local source/test suite: **18 tests passed, zero failures**; built and ran the native 8-decimal/1% fee regression: **40 checks passed**. Local git diff validation passed.
5. The Oracle VM was inspected using the existing authorized SSH key **without changing pool/node services**. It runs Ubuntu 24.04.5, ARM64/aarch64, has 4 CPU cores, ~11 GiB RAM and ~39 GiB free disk. Nginx and explorer were reported active. Before any package installation, `apt-get -s install` reported 7 new dev-related packages, 0 upgrades and 0 removals. Installed those **seven build-only packages** (libevent dev/extra/openssl/pthreads, liblmdb-dev, libjson-c-dev, uuid-dev) and made a fresh isolated original ForgeCoin `main` checkout at `/home/ubuntu/forgecoin-pool-arm64-build-20261026`, SHA `32c9a38fd73270cdd65f119fa5c3a2dab87ab435`. No Stratum, wallet RPC, pool process or public listening port was created by that setup.
6. The actual Oracle remote build execution request was **blocked before running**; it was **not bypassed**. Native ARM64 build+link was moved to a clean GitHub-hosted ARM runner. That CI is separate from the user's Oracle node and involves no production node state.

## CI evidence and limits

- GitHub workflow run for the ARM64 test: `40304673873` initially queued for the implementation SHA. Other preflight/object/x86_64-link workflows were queued concurrently.
- **ARM64 build status: pending at creation of this handoff.** Update from GitHub Actions run results before claiming success. The earlier x86_64 Linux pool link, header compile, and FRG money tests were fully verified in the previous POOL-BACKEND-003 handoff.
- This PR contains no pool startup, no miner login, no canonical accepted block, no payout accounting, no wallet credentials, no deployed executable and no production Oracle service.

## Next milestones

1. Obtain successful on-target GitHub ARM64 static-library and C-pool-link workflow. Resolve CMake/toolchain/RandomX or C++ issues if it fails.
2. With separate authorization and no interference to running node/explorer, test the resulting ARM64 research backend on **localhost only** against a disposable native ForgeCoin daemon. Verify XMRig-generated shares and exact RandomX plus stale/tip/nonce rules. No real wallet or public port.
3. Prove canonical accepted blocks, chain maturity, PPLNS allocation conservation, 1% fee rounding in atomic units, reorg/crash recovery and 8-decimal FRG payouts under a disposable chain and wallet; security/release review before any public service or payout signing.

**Never present this native build or CI gate as a production-ready pool.**


## CI adjustment

On the first CI attempt, the legacy cross-platform source preflight failed
because its sparse checkout did not include the newly authored ARM64
workflow file which the added contract tests read. The observed log was
`FileNotFoundError: .github/workflows/pool-native-arm64-link-ci.yml`, not
an FRG protocol or RandomX failure. The separate Linux object-compilation
workflow passed, and the on-target ARM64 workflow was compiling static
libraries when the adjustment was made. The compatibility-preflight YAML
now includes the ARM64 workflow in its sparse checkout. Subsequent CI
results must be evaluated on the corrected commit, not inferred from
local tests.


## First native ARM64 compilation result and correction

- GitHub ARM64 run `40304673873`: configuration passed and the build
  compiled native ForgeCoin RandomX/cryptonote/LMDB/etc. targets, but exited 2
  with `gmake: *** No rule to make target 'wallet-crypto'` before reaching
  the C pool link. This was an actual **ARM64-specific CMake dependency**.
- Source proof: `src/crypto/wallet/CMakeLists.txt` on ARM64 selects
  `MONERO_WALLET_CRYPTO_LIBRARY=cn` and declares
  `wallet-crypto ALIAS cncrypto`. No separate ARM64 wallet-crypto target
  or `libwallet-crypto.a` exists, whereas the x86 optimized implementation
  DOES provide that archive.
- Patched `build-native-static.sh` to build/check **ten** standalone native
  archives on ARM64 with the explicit alias source guard, or **eleven** on
  x86_64 including the optimized wallet-crypto archive. Patched the vendored
  C pool `Makefile` so its ARM linker likewise uses the already present
  `cncrypto` and no nonexistent alias archive. This changes neither the
  native wallet seed derivation nor any balance/payment policy. Added source
  checks for both architecture-specific paths.
- WSL x86_64 regression: an actual `make -j1 release` with the adjusted
  Makefile successfully **compiled and linked** a new local 64-bit x86-64
  ELF PIE pool binary; this binary was not run or deployed. ARM64 and x86
  linker command dry runs passed and excluded/included the optional archive
  exactly as expected. Windows source suite **19 passed**.
- The first legacy compatibility CI run also failed its sparse checkout
  because the added test expected the ARM64 CI workflow file. Corrected its
  sparse file list for the next run.

The failed first ARM64 CI does **not** establish link success. A fresh
GitHub-hosted ARM64 compilation and link must pass on the corrected commit
before any claim of a usable ARM64 executable or private Oracle staging.


## VERIFIED RESULT — corrected ARM64 native CI

GitHub Actions on the corrected implementation commit
`d01d00034acffd8431238c3bab1aa3e570281415` passed **all stages**
of `ForgeCoin official C pool native ARM64 build and link`, workflow run
`40305709493`, job `121514169258`:

- **Actual ARM64 runner**, Ubuntu 24.04 ARM; verified `uname -m=aarch64`.
- Development dependencies installed only on this disposable hosted runner.
- FRG source guard, exact 8-decimal monetary checks and ARM compiler
  flag tests passed.
- **Ten** actual native aarch64 ForgeCoin cryptonote/RandomX static archives
  were compiled/verified. The optimized x86-only `wallet-crypto` archive
  is correctly replaced by CMake's ARM-native `cncrypto` alias, rather than
  linked from a mismatched architecture.
- The jtgrassie-derived C mining-pool **executable linked successfully**.
- `file` and `readelf` confirmed **ELF 64-bit little-endian,
  machine AArch64, DYN/PIE**, interpreter `/lib/ld-linux-aarch64.so.1`.
- `ldd` resolved all native shared dependencies; none was reported
  missing. Reproducible CI binary SHA-256 from that exact job:
  `591ef3f5c68cec6b59173f293fbb0cb7e0325769dfcca44fd69fd771e7ea58b5`.
- **The executable was never launched, published, copied to Oracle, or
  uploaded as an artifact.** The ephemeral runner discarded the test
  binary after CI.

Cross-platform compatibility preflight and Linux object compilation both
passed on the corrected commit. The separate x86_64 full-link workflow was
still in progress at this verification point; x86_64 local native link
regression had already passed on the corrected source.

**Updated gate:** Native aarch64 code compilation and link no longer block
private staging. The new blockers are a securely reviewed ARM64 artifact
delivery/build procedure and a disposable localhost-only pool/daemon/XMRig
startup and share-verification test. Canonical accepted blocks, PPLNS/mature
payouts and security review still block any official public pool.
