# FCMP++ migration: pinned-source engineering baseline

**Status (2026-10-25): RESEARCH / INTEGRATION INCOMPLETE. DO NOT ACTIVATE.**
This document is an implementation handoff and read-only source audit, **not an
FCMP++ port, security certification or mainnet upgrade announcement**.

## Why the request cannot be implemented by deleting ring signatures

ForgeCoin currently uses Monero-derived CLSAG and related historical
ring-signature verification. The new protocol must both:

1. Validate **historical** pre-activation transactions and signatures, including
   during synchronization, pruning, chain reorganizations and wallet rescans.
2. From a separately reviewed activation rule, correctly serialize and validate
   **FCMP++** transactions using Full-Chain Membership Proofs, spend authorization
   and linkability, its curve-tree commitments, and its supporting wallet/output
   format (CARROT as in upstream beta).

Deleting legacy verifier code would invalidate history; accepting new FCMP
transactions without complete membership, nullifier/linkability and amount
conservation checks can permit double-spends or **undetected inflation**.

**Precise privacy property:** a valid proof shows membership in the eligible
output history without revealing the consumed output. Because outputs are
confidentially spent, this is **not merely a public list of currently unspent
outputs**. Ring-size-16 exclusion and some ring-member statistical attacks
are addressed, but no mathematical guarantee defeats network metadata, wallet
compromise, side-channel leakage, low anonymity on a young chain, exchange
records, or cross-chain deposit/withdrawal correlation. Avoid claiming
absolute 'untraceability'.

## Source pinned for comparison

- **Repository:** https://github.com/seraphis-migration/monero
- **Tag:** `v0.19.0.0-beta.3.1`
- **Resolved source commit:** `d80596ad18110390b6ca97a77e29aba36f4644c9`
- **Monero upstream consensus PR under review:** https://github.com/monero-project/monero/pull/11440
- **Research/milestone:** https://github.com/monero-project/monero/milestone/1
- **ForgeCoin baseline used in initial survey:** `1b1d35292ffda1dad86305001d13c71bc0a1fcb8`

On the owner's authorized Windows device, a disposable clone of beta v3.1
was checked out and compared to a disposable ForgeCoin clone.
The pinned 11-surface source inventory found **11/11 upstream**,
**0/11 ForgeCoin**. It is deliberately a **source-presence** check, not a
completeness proof. See `tools/fcmp_port_preflight.py`.

The survey found approximately **255 upstream-only paths** in the tracked
CMake/src/external/tests selection, including roughly **113 privacy-related
paths** (substring filter for FCMP, CARROT, curve tree, and Rust). It is
not an exact patch-size estimate; widespread changes to common files are
not counted as additions.

## Mandatory implementation workstreams

| Surface | Upstream reference | ForgeCoin integration requirement |
| --- | --- | --- |
| Cryptography / Rust FFI | `src/fcmp_pp/` and `fcmp_pp_rust/` | Pin provenance/dependencies; verify builds, ABI, exact proof verification and consensus-failure behavior |
| Curve-tree root/state | `src/fcmp_pp/curve_trees.cpp`, `src/blockchain_db/lmdb/` | Deterministic output ordering, root calculation, historical backfill, alternate chain rollback, durable rescan and pruning |
| Serialization and fork rules | `src/ringct/rctTypes.h`, `src/cryptonote_basic/cryptonote_basic.h` | Canonical new transaction formats, version dispatch, output age and header commitments |
| Spend verification | `src/cryptonote_core/blockchain.cpp` | Correct FCMP membership + spend authorization/linkability + key image/nullifier uniqueness + output/value checks |
| CARROT wallets | `src/carrot_core/`, `src/carrot_impl/`, `src/wallet/wallet2.cpp` | Scanning, view-only behavior, outgoing proofs, restore, offline signing, subaddresses and old wallet migration |
| Mempool / reorg / P2P | `src/cryptonote_core/`, daemon/protocol | Full validation, caches, alt branches, relaying, block templates and sync on same consensus hash |
| Native fork economics | ForgeCoin `src/cryptonote_config.h`, `src/cryptonote_core/` | Preserve owner-approved 50M emission reference, 0.20 FRG tail, 100% native PoW block subsidy, 8 decimals, difficulty schedule and correct genesis handling |
| Full integration tests | `tests/core_tests/fcmp_pp.cpp`, `tests/unit_tests/` | Independent vectors, native block acceptance, incorrect proofs, inflation attempts, forged tree roots, duplicate spends, malformed data, historical wallet restores |

**Critical version collision:** ForgeCoin's isolated fresh-chain candidate has
already used protocol **v19 from height 1**, while upstream FCMP++ beta has its
own v17/v18 activation path. **Do not transplant hardfork constants/heights
or Monero network identities blindly**. Design an explicit ForgeCoin
fork/version mapping after reviewing genesis and network history. An
FCMP-from-genesis candidate is possible to *study* while fresh mainnet is
unlaunched, but requires end-to-end history/serialization tests and approval.

**Genesis is independently blocked:** existing candidate genesis includes
an indexed **11.92092895 FRG** output without proof of permanent
unspendability. FCMP++ does not resolve that risk.

## Reproduction (local audit only)

From a separate disposable ForgeCoin clone:

```powershell
git clone --depth 1 --branch v0.19.0.0-beta.3.1 --single-branch https://github.com/seraphis-migration/monero.git ..\monero-fcmp-reference
python tools/fcmp_port_preflight.py --fork-root . --upstream-root ..\monero-fcmp-reference
python -m unittest tools.test_fcmp_port_preflight -v
python tools/fcmp_port_preflight.py --fork-root . --require-integrated
```

The last check is **expected to exit 2** on the current unported fork.
An upstream mismatch or missing upstream reference marker exits **3**.
Even if all 11 markers appear, no cryptographic or runtime security
claim follows. No daemon, miner, wallet, or service is launched by this tool.

## Required completion and activation gates

1. Port the pinned upstream implementation **coherently**, with clean licensed
   source dependencies, fork-specific consensus mapping, build flags and exact
   reproducible upstream diff.
2. Compile daemon, wallet, tests and desktop-facing RPC on Windows x64,
   Linux x86-64 and Linux ARM64; cross-check deterministic FCMP vectors.
3. Verify native proof membership, double-spend rejection, value conservation,
   malformed proofs, replay, adversarial alternate chains, reorg rollback,
   state persistence, pruning, block limits and worst-case denial-of-service.
4. Validate all historical transactions still verify, and verify CARROT
   scanning, recovery, change outputs, legacy-address handling and wallet RPC.
5. Independently audit ForgeCoin-specific port changes. Upstream reviews do
   not automatically apply to modified code or altered native chain rules.
6. Run disposable multi-node sync and mined-block acceptance at relevant
   ForgeCoin heights, including local difficulty activation and tree states.
7. Publish precise release formats, upgrade compatibility, hash-verified
   binaries, rollback strategy and community activation timeline. Require
   explicit owner authorization before merging consensus changes or operating
   new production rules.

**Never use this document or the preflight script as permission to deploy,
fork a live chain, start mining, move funds or replace historical signatures.**

## Verified outcome of this first stage

- Upstream source downloaded at pinned beta v3.1 commit.
- Local source-diff inventory created and executed.
- Five offline source-preflight tests passed on owner's Windows device.
- Deliberate release gate blocked because ForgeCoin has not integrated FCMP++.
- **No C++/Rust consensus cryptography has been transplanted, compiled or audited.**
