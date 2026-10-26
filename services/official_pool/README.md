# ForgeCoin native mining-pool backend — isolated C fork (RESEARCH ONLY)

This directory contains the **initial native-FRG compatibility port** of
[jtgrassie/monero-pool](https://github.com/jtgrassie/monero-pool). It is
**NOT a launch-ready pool**, and must not be installed on a public host, given
real wallet keys, or used for payout decisions.

## Source provenance and notices

- Upstream repository: https://github.com/jtgrassie/monero-pool
- Upstream pinned commit: `db16e73fcc587a873050a946214f63b6e1bed22a`
- Original tracked files copied into `jtgrassie/`, preserving their complete
  original headers, `LICENSE`, `README.md`, and BSD-3-Clause conditions.
- Changes made here are ForgeCoin-specific research modifications; there is no
  claim that jtgrassie endorses or supports ForgeCoin.
- The main public ForgeCoin repo retains its existing license and Monero fork
  notice. Any shipped derivative must retain both upstream license notices.

The official website is independently implemented under `apps/pool-site/`,
with the read-only aggregator `services/pool_stats_bridge/`. Those do not
imply a backend is accepting shares or sending payments.

## What the first source patch actually changes

- Introduces `src/frg_currency.h` with FRG **100,000,000 atomic units per coin**
  (8 decimal places), matching `src/cryptonote_config.h` at this repo HEAD.
- Strictly parses payment thresholds from decimal strings into uint64 atomic
  units; never floats a decimal threshold to make a wallet transfer. Rejects
  signs, whitespace, exponent notation, invalid precision and overflow.
- Normalizes the original `/stats` miner-balance numeric JSON emission to
  exactly eight decimal places using integer division and modulus.
- Calculates the proposed **1% operator deduction** as `amount / 100` for
  each eligible allocated share; the exact fee remains a proposed policy,
  not proof of correct PPLNS/reorg behavior. The research config rejects
  fee settings other than `0.01`.
- Uses FRG's mainnet address prefix **90** and two-minute target, instead
  of retaining Monero's prefix 18. Independent address parsing tests are
  still needed.
- Changes the build binary to `forgecoin-pool`; requires the explicit
  `FORGECOIN_ROOT` source location, optionally `FORGECOIN_BUILD_ROOT`.
  The pool's original Makefile still refers internally to Monero library
  names because ForgeCoin is a Monero fork; that naming is **not** proof of
  a valid build against current FRG.
- Research config binds the Stratum and statistics sockets to **127.0.0.1**,
  avoids an embedded third-party pool wallet, uses FRG daemon RPC port 19481,
  deliberately leaves wallet RPC port **0**, and disables self-select,
  payouts and any option to bypass native proof-of-work checks.
- Research builds fail closed if the operator enables public interfaces,
  disables share hashing or enables payouts. In addition, wallet payout
  execution is compiled out unless a separate `FRG_TESTED_WALLET_PAYOUTS`
  build macro is explicitly enabled **after** independent review. These
  guard macros are **not** authorization to remove safety barriers.

**Important:** The original C source still has upstream assumptions in its
RPC integration, miner authentication, job serialization, LMDB database
payout accounting, PPLNS share arithmetic, reorg handling and wallet
`transfer_split` recovery. Those are unreviewed. Even with this patch, DO
NOT RUN an active pool or connect a spending wallet.

## Local offline verification

From repo root:

```sh
python -m unittest discover -s services/official_pool/tests -p 'test_*.py' -v
gcc -std=c11 -pedantic -Wall -Wextra -Werror -O2 \
    -o /tmp/frg-pool-money-test services/official_pool/tests/test_currency.c
/tmp/frg-pool-money-test
```

Tests compile the standalone monetary converter and validate source/config
gates without starting any pool, daemon, wallet or network listener.
Windows MSYS2 GCC and Ubuntu Linux GCC have both been used for this
standalone code. The full upstream C/C++ pool has **not** been compiled or
linked in this step.

## Build preflight and remaining dependencies

An actual Linux pool build requires an approved matching ForgeCoin source
checkout already built with its native C++ libraries, plus libevent, LMDB,
json-c, uuid, libsodium, openssl, boost, unbound and other optional
dependencies listed in the inherited upstream Makefile.

A prospective future isolated build command (once dependencies and security
review are complete) is:

```sh
cd services/official_pool/jtgrassie
FORGECOIN_ROOT=/trusted/forgecoin \
FORGECOIN_BUILD_ROOT=/trusted/forgecoin/build/release \
make release
```

At the time of this handoff, the available Ubuntu WSL environment lacked
libevent/json-c/LMDB development packages and no accepted build against
the current repository's Linux libcryptonote or RandomX has been verified.
**Do not interpret a money-unit test passing as a runnable pool binary.**

## Mandatory next release gates

1. Reproducible Linux x86_64 and ARM64 builds against exactly the reviewed
   ForgeCoin source revision, including full native daemon and wallet ABI.
2. Test native address prefixes and XMRig/Stratum jobs using genuine FRG
   templates and native RandomX seed epochs. Preserve the already passing
   isolated XMRig tests from draft PR #105.
3. Test an actual canonical **accepted mined block** only on a fresh,
   disposable, authorized test chain. Rejected/invalid/stale block,
   reorg and daemon restart cases must be covered.
4. Independently verify the complete PPLNS reward split, pool fee rounding,
   reward maturity (60 blocks on this baseline), LMDB recovery, payee
   ownership, transfer_split failure/retry and 8-decimal wallet outcomes.
5. Only then implement an authenticated production operator procedure,
   audited signing compartment, TLS/public endpoint and 100-worker stress
   test. No automatic production deployment, wallet custody or public
   mining launch is authorized.

Each development step must have a separate dated committed handoff.


## POOL-BACKEND-002 — Linux compile-only staging gate

As of October 26, 2026, all nine C, C++, and HTML-derived native jtgrassie pool object files **successfully compile on Linux x86_64** using ForgeCoin's current `main` source headers. The resulting pool executable **does not link**, because no native Linux ForgeCoin static-archive build exists in this isolated checkout. The available prior Windows static libraries are unsuitable for Linux linking.

The upstream Makefile now exposes an explicit, reproducible **compile-only** target that never invokes a daemon, starts Stratum, connects wallet RPC, or signs payouts:

```sh
cd services/official_pool/jtgrassie
make -j2 compile-check TYPE=release \
  FORGECOIN_ROOT=/reviewed/forgecoin/source \
  FORGECOIN_BUILD_ROOT=/path/to/native/frg/build
```

Use `make link-preflight TYPE=release ...` before attempting the entire `make release` target: every required native static archive must exist or the build **fails closed with the exact missing paths**. Passing `compile-check` is **not** proof of a runnable pool or payout safety.

The new `.github/workflows/pool-native-linux-object-compile.yml` runs this source compilation on **Ubuntu 22.04 x86_64**, without a link or executable artifact. Native FRG mainnet deployment is still prohibited.

For **private Oracle ARM64 staging**, build/review the native ForgeCoin static libraries for the exact ARM64 target, compile and link the C backend on ARM64, and exercise local-only Stratum daemon template handling and RandomX job validation before installation. Public pool access additionally requires accepted-block and mature payout verification, reorg/restart recovery, production security review and explicit launch approval. Do not copy or run this compile-only result on Oracle.
