# ForgeCoin isolated native coinbase-reserve cross-check

**Date:** 2026-10-27. **Scope:** offline research; not production pool code.

The opt-in `FORGE_BUILD_ISOLATED_POOL_TOOLS=ON` CMake target
`forge-isolated-block-reconstruct` uses ForgeCoin's native
`parse_and_validate_block_from_blob`, `block_to_blob`, and
`get_block_hashing_blob` consensus functions. The helper first proves that
the original complete block and hashing blob agree with native consensus.
It locates an eight-byte miner-transaction extra reserve within the exact
native block serialization, modifies only those bytes, invalidates native
cached hashes, reserializes the block, and recomputes the transaction tree
root. It does not run a daemon, query RPC, mine, credit shares or pay anyone.
The CMake option is OFF by default and the executable is never installed.

`services/pool_research/reserve_candidate.py` requires the exact SHA-256
digest of the supplied local helper executable, limits input/output sizes,
uses a bounded subprocess and checks that only the reserved region changed
in the complete block. There is no silent fallback on native verification
failure. `tools/build_isolated_reserve_candidate.py` writes a private
reconstructed reserve-only candidate; `tools/verify_isolated_native_reserve.py`
then applies the same nonce as the independently generated test candidate.

**Observed verification:** The native helper built successfully against the
source-matched MinGW compilation. On the privately captured height-1,
difficulty-1 ForgeCoin block template from the disposable-chain test,
`tools/verify_isolated_native_reserve.py` reported
`PASS: source-matched C++ consensus root and Python reserve+nonce candidate agree`.
The original block was 134 bytes and its hashing blob was 76 bytes.
The compiled local test-helper SHA-256 was
`C7968C748DECA79D546E8D2D14DBD8BAC7776927B38567E3F3C405B0A46D20A4`.
This binary hash is evidence for this disposable build only, not a release
signature. Private captured block files and the helper executable are
excluded from Git.

**Separate chain acceptance:** The independent reserve-and-nonce candidate
was accepted by a fresh offline daemon with canonical chain advancement to
height 2 on isolated ports 49880–49882. See
`ISOLATED_NATIVE_BLOCK_ACCEPTANCE_2026-10-27.md` for details.

**Limits:** The test exercised a single-transaction, easy-difficulty
disposable chain. It did not submit a share discovered by XMRig through a
production Stratum job, verify nontrivial difficulty, demonstrate multi-tx
block lifecycle, or validate pool rewards, maturity, reorgs or payouts.
No public chain or spending wallet was contacted.
