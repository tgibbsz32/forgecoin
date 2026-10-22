# Native FRG unlock behavior: read-only source review

**Reviewed baseline:** ForgeCoin main after PR #11 (2026-10-22). **No changes** to consensus, wallet, RPC, or funded locking. This is a source inspection, not a successful end-to-end lock demonstration.

## Observed in source

- `src/cryptonote_core/cryptonote_tx_utils.cpp:260`: the inspected transaction-construction path initializes `tx.unlock_time = 0`. This does not establish an exposed, safe user-selected governance bond path.
- `src/wallet/wallet2.cpp:10049,10403`: two wallet transaction-construction data paths set `unlock_time = 0`.
- `src/cryptonote_core/blockchain.cpp:3848-3870`: `is_tx_spendtime_unlocked` applies distinct height- and timestamp-based unlock conditions. Height-based spend eligibility uses an **allowed early delta**; using the displayed target unlock height as a guaranteed nonspendability deadline is unsafe.
- `src/cryptonote_config.h:90`: the configured allowed height delta is **1 block**. Lines 88-89 derive allowed timestamp deltas from difficulty targets.
- `src/wallet/wallet2.cpp:7329-7350`: wallet-side unlock checks also apply timing/height leeway.

## Findings and decisions

**No launch-ready native FRG bond exists.** The existence of `unlock_time` in consensus verification does not demonstrate that ordinary wallet transactions can construct an independently verifiable, privacy-preserving FRG bond. The intended lock, unique proof, private amount, independent non-spend attestation, recovery, and long-term reorg handling remain open.

Do not change wallet or consensus unlock-time restrictions to enable deposits without a separate source review and isolated network acceptance experiment. A wallet-local freeze, signed pledge or screenshot is not an enforceable lock.

Even if testnet transactions with a custom `unlock_time` are eventually accepted, an independent reviewer must verify that the *same specific bond* remains reserved and cannot be reused, without revealing unrelated private outputs. That privacy/unspent proof is a separate and currently unsolved gate.

## Proposed next isolated tests

1. Establish a disposable FRG testnet with distinct genesis and chain identity, independent from production, and compare two fully validating nodes.
2. Generate only testnet funds/keys. Inspect supported transaction constructors without modifying production code.
3. Validate target-height and actual earliest-spend behavior across the allowed one-block height leeway.
4. Evaluate timestamp leeway, fork version, chain rewinds, deep reorganizations, daemon restart and wallet restoration.
5. Separately investigate amount, ownership, uniqueness and ongoing unspent proof construction with private RingCT outputs and key images.
6. Do not connect any result to membership authorization until independent security, governance and privacy review.

**Decision gate:** Until an enforceable lock **and** privacy-safe independent proof of continuing lock can both be demonstrated, miner FRG bonds remain design research only and binding miner representative authority stays disabled.
