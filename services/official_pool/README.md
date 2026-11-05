> **Current specification — identity selected 2026-10-26; consensus integrated 2026-11-04:** [Frozen mainnet parameters, tokenomics and release status](../../docs/CURRENT_MAINNET.md). Consensus PR #185 is merged into source `main`, **but mainnet mining/block acceptance remains locked** and public launch is not authorized. This research pool has not been approved for production Stratum or payout signing; matching consensus source alone does not prove production readiness.

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
  avoids an embedded third-party pool wallet, uses FRG daemon RPC port 39481,
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


## POOL-BACKEND-003 — pinned native archive build and x86_64 link proof (2026-10-26)

`tools/build-native-static.sh` now builds the **11 expected native ForgeCoin
static archives** from an exact, clean, 40-character Git commit on Linux.
It refuses another checkout's CMake cache, rejects unsupported architectures,
and enforces low-memory compiler limits: under 4 GiB RAM only one parallel job;
under 8 GiB at most two. This is critical on the user's dedicated ForgeCoinBuild
WSL distro, which has **1.9 GiB RAM and 1 GiB swap**. An initial eight-worker
build rendered the dedicated WSL distro unresponsive and was safely
terminated without shutting down other distros. Repeating with
`FRG_BUILD_JOBS=1` **succeeded**.

From a *separate, trusted, clean* Linux checkout of this original ForgeCoin
repository (do not run in the user's local consensus worktree):

```sh
cd /path/to/isolated/forgecoin
FRG_BUILD_JOBS=1 bash services/official_pool/tools/build-native-static.sh \
  "$PWD" "$PWD/build/official-pool-static/release" "$(git rev-parse HEAD)"
make -C services/official_pool/jtgrassie -j1 release TYPE=release \
  FORGECOIN_ROOT="$PWD" \
  FORGECOIN_BUILD_ROOT="$PWD/build/official-pool-static/release"
```

This procedure has now **successfully linked** a Linux **x86_64** research
`forgecoin-pool` binary against ForgeCoin commit
`cf76794731c2d4bc310b7f4d4b744173809e308f`. ELF inspection
confirmed a 64-bit x86-64 PIE executable; local dynamic dependencies resolved
without missing libraries. Example SHA-256 for that isolated **test binary**
(never published as a release):
`c9d6654998f71918d88247e4baac49fb6c9cba6b2ea512cc66e8aeca1089b05b`.
The executable was **not started**. It did not open mining, wallet or network
ports or process shares, blocks or payments.

The jtgrassie Makefile previously supplied x86-specific `-maes` flags on
*every* architecture. It now passes that option only on x86_64/amd64, accepts
native `aarch64` without it, and fails closed on unreviewed architectures.
Dedicated tests checked ARM64 and x86 compiler command-line dry-runs: the
former contained **no** Intel `-maes`, the latter retained it. This is **not
an ARM64 compile or executable**.

`.github/workflows/pool-native-static-link-ci.yml` independently configures,
builds, and links the Linux x86_64 pool in an ephemeral Ubuntu 22.04 CI
runner, verifying ELF/PIE and runtime library dependencies. The CI job
**never launches** the resulting binary, publishes no release assets, and
cannot submit blocks or pay miners. Existing native source guards, 8-decimal
amount tests and the new archive/architecture safeguards are also run.

**Security and Oracle deployment gates remain:** verify an actual aarch64
native build/link on a disposable ARM64 builder; validate startup with
research guards intact; prove real FRG daemon/XMRig Stratum interoperability,
accepted blocks, PPLNS conservation, 1% fee, 8-decimal reward maturity and
payout recovery. No public Stratum, wallet keys or payouts should be enabled,
and this unexecuted x86 binary must **never be installed on the ARM64
Oracle VM**. Inherited cryptographic warnings (including an upstream
Supercop `sc25519_window4` declared/output array-width mismatch and
OpenSSL 3.0 deprecated APIs) require review before final release.


## Native ARM64 compile-and-link verification — POOL-BACKEND-004 (2026-10-26)

The experimental pool now has an **ephemeral, on-target** native ARM64
link-validation workflow:
`.github/workflows/pool-native-arm64-link-ci.yml`.

This workflow uses GitHub's `ubuntu-24.04-arm` host, asserts that
`uname -m` is `aarch64`, installs compile-only dependencies inside the
ephemeral runner, runs the existing exact 8-decimal FRG currency checks,
builds the eleven static ForgeCoin cryptonote/RandomX archives from the exact
current checkout SHA, links the vendored jtgrassie C pool against those
archives and validates the resulting ELF machine type and dependencies.
The build script caps concurrency based on real host RAM. A Makefile dry run
rejects x86-only `-maes` on ARM64.

**The binary is never executed, uploaded, deployed or published by CI.**
GitHub CI is not a replacement for network correctness, pool accounting,
wallet payout, or a real miner submitting an accepted block. The production
pool daemon, wallet RPC, public ports and payout signing remain disabled.

The Oracle Free Tier VM was inspected read-only over the user's authorized
SSH key: Ubuntu 24.04.5, ARM64, 4 CPUs, ~11 GiB RAM and 39 GiB disk free,
with nginx/explorer running. The missing build-only packages (libevent,
LMDB, json-c and uuid development headers, plus three libevent components)
were installed after an `apt-get -s` dry-run confirmed **zero existing
package upgrades/removals**. An isolated source clone of original main,
commit `32c9a38fd73270cdd65f119fa5c3a2dab87ab435`, was created at
`/home/ubuntu/forgecoin-pool-arm64-build-20261026`. No daemon or pool service
was started or modified. An attempt to execute the native build there
was blocked before execution; the remaining ARM64 compile/link check was
therefore moved to an ephemeral GitHub-hosted runner instead.

**Private Oracle staging gate:** A completed native ARM64 binary link and
hash/dependency verification are necessary but insufficient. A separate
approved step must prove isolated localhost startup with no real wallet,
FRG daemon RPC, native XMRig/RandomX and accepted-block behavior before
installing a persistent private pool process on Oracle. Public Stratum and
payouts need additional canonical-chain, maturity, reorg, PPLNS and signing
review. Do not treat an ARM64 CI success as permission to enable public pool
ports or touch custody.


### ARM64 crypto-link correction found in first CI attempt

The first hosted ARM64 run at workflow `40304673873` reached **all the way
through most native ForgeCoin library compilation** and then failed at
`gmake: No rule to make target 'wallet-crypto'`. This was an actual
architecture-specific assumption inherited from the x86 build, **not a
failed RandomX test or bad consensus block**. In
`src/crypto/wallet/CMakeLists.txt`, on native ARM64 the optimized
wallet crypto engine is unavailable and CMake uses
`add_library(wallet-crypto ALIAS cncrypto)`. This alias has **no
standalone** `libwallet-crypto.a` or directly buildable target.

`build-native-static.sh` and the pool's `Makefile` now retain the
separate optimized archive for x86_64, but on aarch64 use `cncrypto`
instead, with a fail-closed source assertion ensuring the CMake alias
remains present. The expected archive count is **11 on x86_64, 10 on
aarch64**, without skipping any native crypto function. Both native
architecture-specific link inputs were tested by Makefile dry runs.

The first legacy preflight also failed because the CI sparse checkout
did not include the new ARM64 workflow source; the sparse list has been
updated. The failed CI run therefore **does not establish a passing
ARM64 binary**. Await a fresh on-target ARM64 CI result on the corrected
commit before advancing the Oracle private-staging gate.


## November 1, 2026 — runtime identity and callback guards (POOL-BACKEND-005)

At this historical November 1 checkpoint, the frozen mainnet required address prefixes **190/191/192** and ports **39480/39481/39482**, while the then-current native consensus header on `main` still used legacy **90/91/92** and **19480/19481/19482**. **Superseded November 4:** PR #185 integrated the frozen identity into `main` without releasing the mining/block lock. The pool's fail-closed startup identity check remains mandatory; this code merge does **not** authorize a public Stratum listener, pool wallet or production payout signer. No port change alone makes the node mainnet-ready.

Source-level defenses were added for strict eight-digit nonce parsing, rejection of unconfirmed block callbacks, avoiding low-difficulty hashrate credit, and avoiding balance debit after a malformed, unsuccessful or ambiguous wallet response. A wallet success response must include a nonempty transaction-hash list. These safeguards are not complete settlement safety: the inherited payout code still has separate LMDB balance and payment transactions, without a durable idempotent payout-attempt state machine or verified replay recovery. Therefore the compile-time payout barrier, localhost research bind and public-release block remain fully in effect.

These are reviewable source changes only. Neither a running Oracle pool nor canonical native FRG accepted block, maturation/reorg reversal, payout to two test wallets, nor load/stress testing is established by this handoff. Run source guards, currency conversion tests, native ARM64/x86 link workflows, disposable daemon integration, payout recovery and independent security review before any public mining authorization.


## November 4, 2026 — Stratum job ingress hardening (POOL-BACKEND-006)

The source-only native pool acceptance review identified independent
Stratum ingress defects in the inherited C implementation. The pool
previously permitted multiple `login` requests on one client connection,
which could increment worker/account counts repeatedly without matching
disconnect accounting; `client_id` also had **32 characters of storage
for a 32-hex-character UUID without a C string terminator**, despite
being consumed as a string by job formatting.

The private research backend now rejects repeat login requests after
client authentication, rejects unauthenticated job/template/share requests,
rejects non-hexadecimal job IDs, stores the client ID in 33 bytes with an
explicit trailing NUL, and validates both the block nonce span
(offset 39, four bytes) and the daemon's reserved nonce span (eight
bytes normally; sixteen for proxy mode) **before writing to or hashing a
native block buffer**. Native job generation now verifies its template
before adding a job to the client's stack, and drops failed hashing-blob
jobs rather than advertising invalid work.

**Actual tests on connected Windows/WSL:** all **39 Python pool source
guards**, **20 compiled native C nonce/reserved-offset boundary assertions**
(including `SIZE_MAX` overflow cases), and **the full nine-object C/C++
native pool compile-only target** passed in the disposable checkout.
No Linux pool executable was linked or started in this step.

**Unchanged release blocker:** current `main` still contains native
consensus parameters not matching the frozen 20261026 identity. The
pool's existing `frg_matches_frozen_mainnet()` fail-closed gate is
preserved. **No live Stratum login, accepted share, pool block, payout,
or wallet signing has been proven by this change.** Canonical daemon
identity and frozen genesis must be reviewed independently before
private loopback end-to-end Stratum/RandomX acceptance, and Oracle/public
activation remains a separate final owner-controlled step.


## November 4, 2026 — source-credit payout batch reservation (test-only)

The native pool now includes `frg_payout_batch_reservation.h`, a dormant
full-sync LMDB safety coordinator that **joins the existing deterministic
source-credit manifest to the durable payout-intent journal** without any
wallet RPC. It accepts only the approved frozen chain UUID; canonicalizes
the caller-supplied source-credit digest and ordered recipient amounts into
a stable source-bound batch ID and a separate manifest hash; then performs a
**serial, single-transaction check that no prior payout intent exists and
inserts the new immutable PREPARED record**. After commit, it forces an LMDB
sync and verifies the stored record before returning the batch ID, commitment
and atomic amount to the caller. Any previous intent, corruption, disabled
durability mode, conflicting batch or restart refuses a new reservation.
The journal has **no settlement, removal or retry API**.

This is a **necessary pre-send invariant, not an authorized payout path**.
The input source-credit digest, chain anchor, maturity, recipient address
checksum and fee budget must still be validated independently against the
canonical native chain and LMDB accounting; the manifest itself only
commits to caller-supplied bytes. No wallet keys, transfer signatures, miners,
explorers, payments, debit from `db_balance` or live network are involved.
The native legacy `transfer_split` sender still has an unconditional
`#error` if `FRG_TESTED_WALLET_PAYOUTS` is defined, and public pool
payouts remain disabled. Never promote a journaled candidate transaction ID
to a settled payout without separate canonical confirmation and idempotent
LMDB debit/payment commit under a reviewed crash/reorg protocol.

**Executed QA on authorized Windows/WSL checkout:** 42 Python native pool
source/safety tests; 87 C assertions against real temporary full-sync LMDB,
including flush, restart, duplicate sources, mutated sources, timeout ambiguity,
unverified tx candidate, corruption and `MDB_NOSYNC` refusal; and the prior
native manifest and intent-journal tests. The GitHub payout-intent workflow
also compiles and executes this integration fixture. No ZIP/APK was created,
no production host or wallet was accessed, and the frozen consensus prelaunch
lock remains in place.


## November 4 — source commitment derived from native credited LMDB history

The research-only native pool now includes
`frg_payout_credited_sources.h`. Its read-only scanner computes a
domain-separated SHA-256 commitment from actual **unlocked and matured**
saved pool block records, rather than trusting a caller-provided opaque
source digest. It uses the frozen chain UUID, the block height, binary
hash/parent hashes, difficulty, reward and a source count, encoded in
stable order. A later anchor height does not create a different source
identity for an unchanged set of credited blocks. Duplicate unlocked
heights, invalid records, height mismatch, an unlocked genesis record,
immature sources, zero reward/work, integer overflow, unsorted source
heights and an empty source set fail closed. Locked and orphaned records
are scanned and structurally checked, but do not create payout credits.

The separate **offline**
`frg_payout_batch_reserve_from_credited_lmdb` operation scans blocks
and prepares the canonical intent **inside one serialized LMDB write
transaction**. A concurrent pool writer cannot alter those block rows
between computing the source digest and committing that intent; existing
prepared/ambiguous candidates still block all further batches. It
requires normal synchronous LMDB durability, then flushes and checks
the committed intent. The existing direct-digest reservation API remains
available only as research/test infrastructure; neither variant is wired
to any wallet sender.

**Native verification:** 101 successful C assertions using temporary
real LMDB, including maturity boundary, deterministic identity across
tip changes/restart, unrelated locked blocks, mutated source reward,
malformed status, same-height duplicate credits and held intent/replay.
The native pool also compiled all C/C++/web objects in SourceOnly mode,
and 46 Python pool source/safety checks passed in the isolated Windows
QA worktree. The dedicated payout CI compiles and runs this C fixture.

**These results do not authorize a payment.** A local pool `unlocked`
flag is NOT proof that a block is canonical, that its miner PPLNS
amount is correct, that outputs are unspent/available, or that a payout
satisfies wallet fees, native address checks and finality. An independently
validated chain anchor/header audit, verified balances and a fully
crash-safe signed-transaction reconciliation and atomic debit remain
mandatory. The legacy wallet sender is still compile-time blocked,
public Stratum and payouts remain disabled, and the merged consensus
continues to reject mainnet mining beyond genesis. No public server,
real wallet, ZIP or APK was used.


## November 4 — two-observer canonical header consistency gate (test-only)

The dormant native payout research path now compiles
`frg_payout_header_crosscheck.h`. It checks the **entire set of unlocked
pool-LMDB source credits** against two separately supplied snapshots
containing the exact native block headers and a common chain-tip header.
The scanner requires all credited heights, matching hash, parent hash,
reward, difficulty and height against BOTH snapshots, an identical
non-orphaned anchor with matching frozen-tip hash and height, complete
witness arrays, structurally valid stored LMDB rows, and 60-block reward
maturity. Malformed, missing, conflicting or immature evidence prevents
an intent from being prepared.

The **offline** `frg_payout_batch_reserve_crosschecked` research function
performs the full dual-snapshot comparison and durable immutable payout
intent preparation under the SAME LMDB write transaction, avoiding a
local source-credit TOCTOU window. The sender is still compiled out.
LMDB reopen/retry holds an already prepared batch indefinitely until
a separately reviewed settlement engine exists. No payout may be
signed, broadcast, credited as final, automatically retried or debited
based on this check.

**Critical scope limitation:** the module does not connect to, authenticate,
or independently operate two nodes. Two serialized JSON objects could
have been fabricated by one process. A claimed header hash does not
prove RandomX proof-of-work, accumulated chain difficulty, finality,
genesis identity or peer agreement; one can also construct matching
noncanonical headers. Therefore this code is a **provisional
cross-check**, not independent canonicality proof or authorization to
send real FRG. Actual production adoption requires secure dual-node
collection, network/genesis verification, complete range and PoW work
validation, a reorg window/anchor policy, a proven PPLNS credit and
available-balance audit, native recipient address checks, fee cap,
transaction signing/recovery and an idempotent atomic settlement path.

**Executed QA:** 130 C assertions with real temporary LMDB and synthetic
native-header JSON, covering missing or conflicting witnesses, changed
hash/height/reward/difficulty, incorrect/orphaned anchor, maturity,
corrupted local block history, unchanged outputs on errors, and
reservation persistence across restart. Fifty Python source-safety
tests passed and the native pool compiled all C/C++/web UI objects
without linking or starting a mining service. The dedicated payout
workflow runs the same C test. The prelaunch consensus lock, public
Stratum disablement and wallet payout compile-time refusal remain
in force; no Oracle service, real wallet, mined coins, ZIP or APK
were involved.
