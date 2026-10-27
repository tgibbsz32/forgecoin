# ForgeCoin native coinbase-reserve cross-validation (isolated research)

**Date:** 2026-10-27. **Scope:** fresh, disposable offline chain; not a public
mining pool, mainnet launch, reward allocation, or wallet payout.

## Confirmed findings

A source-matched MinGW `forged.exe` (SHA-256
`600a76d02fbf9f46825ca989daf1c74187aa3bf524d651c35cfe6fbbc1fd2836`)
was run using `--offline`, fresh chain storage and loopback-only isolated ports
49780–49782. The captured daemon template was height 1, difficulty 1 and had
a 76-byte hashing blob.

The isolated test changed the four-byte block nonce to `01020304` and eight
reserved coinbase bytes to `1122334455667788`, updating the miner transaction
tree root in the hashing blob. The daemon's `submit_block` returned success,
the canonical chain advanced to height 2 and height-1 hash was:

`84b7e2628d253ee9cc2b2c84e9644bd9844c7e936c6c021be7b958ec59dddbe6`

The wrapper stopped the temporary daemon and returned exit code 0.
The private captured blobs remain outside Git.

Independently, `forgecoin-block-hashing-oracle`, a newly compiled opt-in C++
utility using ForgeCoin's native `parse_and_validate_block_from_blob`,
`block_to_blob` and `get_block_hashing_blob`, verified the daemon's original
hashing blob and the changed-reserve candidate. The Python
`build_reserved_candidate` result matched the native hashing blob exactly.
The verification reported header nonce offset **39** and reserved-byte offset
**124**. No wallet secrets or block-template contents were included in logs
or commits.

Focused offline tests: **14 passed**. These cover native-helper round trips,
malformed responses, noncanonical changes, timeout/failure behavior, reserve
reconstruction and nonce reconstruction.

## Explicit reproduction

For an existing source-matched native build with the normal toolchain:

```text
cmake -S . -B build-disposable -DFORGECOIN_BUILD_RESEARCH_ORACLE=ON
cmake --build build-disposable --target forgecoin-block-hashing-oracle --parallel 2
python -m unittest services.pool_research.test_native_block_oracle services.pool_research.test_reserved_candidate services.pool_research.test_nonce_candidate
python -m tools.verify_isolated_reserved_consensus --capture <private-template.json> --oracle <offline-native-oracle.exe>
```

This oracle is optional, is not installed with release binaries, accepts
bounded block data on stdin, performs no RPC and produces no wallet transactions.

## Still unverified

The accepted block was constructed from a native daemon template at **difficulty
1**, not discovered by XMRig and not processed by the actual pool Stratum
job-to-share-to-block pipeline. The test does not prove a production share
target, real network difficulty, pool-side duplicate handling, block maturity,
PPLNS accounting, coinbase spendability, or payout broadcast/reconciliation.
Source-network identity and address-prefix reconciliation remain separate
release blockers. Do not use any disposable wallet for production funds.
