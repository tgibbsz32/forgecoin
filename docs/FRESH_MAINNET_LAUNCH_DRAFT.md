> [Current mainnet specification, tokenomics and release status](CURRENT_MAINNET.md) — October 26, 2026; prelaunch.

# Fresh-mainnet launch: difficulty specification (draft)

> **Planning document, not an activation announcement.** The existing ForgeCoin development chain is unchanged. No chain reset, genesis replacement, or new-mainnet deployment is authorized by this document.

## Intended consensus parameters

| Parameter | Fresh-mainnet target |
| --- | --- |
| Initial mining difficulty | **500,000** |
| Minimum difficulty floor | **400,000** |
| Target block interval | **120 seconds** |
| Proof of work | RandomX (current ForgeCoin implementation) |
| Difficulty adjustment | ForgeCoin's integer LWMA variant after sufficient history |
| LWMA historical window | 90 solve intervals (91 samples) |
| Public launch status | Not launched |

The floor is a **minimum permitted difficulty**, not a maximum. Difficulty may rise above the 500,000 starting value as network hash power increases. The floor must apply to all consensus validation paths once enabled.

## Open consensus design: first blocks

The current ForgeCoin LWMA routine requires **91 timestamps/cumulative-work samples**. A new chain does not have that history at genesis. Before implementation, specify deterministic behavior for every height from genesis through the first LWMA calculation. One candidate is fixed 500,000 difficulty for the warm-up period followed by LWMA, with the 400,000 floor, but **that warm-up schedule has not been finalized or tested**. Confirm the exact first eligible height against block-height and sample-index semantics.

## Do not copy the development-chain schedule

The local development branch currently defines these distinct rules:

- At height 500: 500,000 difficulty floor (v17).
- At height 600: 1,000,000 difficulty floor (v18).
- At height 700: 90-interval LWMA (v19).

These **are not** the proposed fresh-mainnet activation parameters. The fresh-network configuration must explicitly replace the old schedule, not silently inherit its 1,000,000 floor.

## Required validation before launch

1. Implement a network-specific genesis, network identity, activation table, and difficulty parameters; prevent accidental peering with the old chain.
2. Test startup heights, LWMA activation, floor enforcement, exact 120-second target behavior, malicious timestamps, reorganizations, and alternate-chain verification.
3. Confirm deterministic consensus results across supported Windows x64 and Linux ARM64 builds.
4. Audit existing development-chain mining, any distributed balances, independent users, and checkpoint obligations. Do not reset or invalidate balances without an explicit public transition decision.
5. Produce verified reproducible release candidates and publish their hashes, limitations, and clear migration instructions.
6. Announce a fair public start time and give independent miners and node operators adequate notice.

## Transparency and network status

ForgeCoin remains an **experimental development network** at the time of this draft, without an independent security audit. No public-mainnet reset or migration has been performed. The current explorer is [available over HTTPS](https://150.136.209.227/), but reflects the **existing development chain**, not a new launch.

The proposed economics and difficulty settings do not guarantee security, stable mining profitability, or fair distribution; these require testing and transparent public participation.


## Preliminary launch simulations — October 20, 2026

A **Python reproduction of the current integer LWMA formula**, parameterized for 60, 90, or 120 intervals and a 400,000 floor, ran 624 seeded trials (13 scenarios × 3 windows × 16 random seeds) across **386,880 simulated blocks**. Each trial simulated 620 blocks with a possible hash-rate transition after 220 blocks. Startup used a provisional **fixed difficulty of 500,000 until N+1 history entries**, before LWMA. This is **not approved consensus bootstrap logic**.

| Scenario, first 100 blocks after transition (seconds) | LWMA 60 | LWMA 90 | LWMA 120 |
| --- | ---: | ---: | ---: |
| One 6,500 H/s miner, steady | 119.52 | 118.58 | 117.38 |
| Large miner joins, 6,500 → 33,500 H/s | 78.71 | 63.77 | 53.22 |
| Large miner leaves, 33,500 → 6,500 H/s | 218.34 | 250.67 | 262.30 |
| Pool exit removes 70%, 65,000 → 19,500 H/s | 179.97 | 198.35 | 201.65 |
| Network at 2,000 H/s, last 200 blocks | 200.08 | 200.05 | 200.05 |

The 400,000 floor imposes a minimum expected block interval of 200 seconds at 2,000 H/s (difficulty / hash rate), irrespective of window. LWMA 60 reacts faster to large departures; 120 is slower; **90 remains a practical compromise, not a proven optimum**. Results are means over seeded trials, not deterministic guarantees, and rare long block gaps occur.

**Validation limits:** Python models the integer formula but does not link or execute the compiled ForgeCoin consensus implementation; it does not validate RandomX proofs, alternate chains, adversarial timestamps, propagation, or real pool payout behavior. The short warm-up period and sample indexing remain consensus design issues. Reproduce using the locally saved `simulate_fresh_mainnet.py` and CSV/JSON results in the project's `final-respository-and-builds/consensus-specs` folder. Do **not** treat these results as release authorization.

## Future development: optional XMR/XTM merged-mining integration

After ForgeCoin's own mainnet launch and stabilization, research an optional **Monero (XMR) + Tari (XTM)** merged-mining setup within ForgeCoin Desktop, including compatible external mining infrastructure, separate wallet support, secure key isolation, and pool integration. This roadmap item is *not* a plan to make ForgeCoin itself an auxiliary-POW chain, and it does **not** change ForgeCoin's existing consensus, block rewards, or launch scope.


## Startup adjustment proposal and test — October 20, 2026

A second exploratory Python simulation compared **fixed 500,000 difficulty for 90 blocks** against **fixed 500,000 for the first 10 mineable blocks, then a growing LWMA window from 10 to 90 history intervals**. The floor remains 400,000. Each of seven network scenarios ran 50 randomized trials, for 700 runs, measuring the first 90 block intervals.

| Launch scenario | Fixed 90 (s/block) | Growing LWMA 10→90 (s/block) |
| --- | ---: | ---: |
| One 6.5 kH/s miner | 76.01 | 111.02 |
| One 2 kH/s miner | 247.03 | 203.55 |
| 6.5 kH/s, then 27 kH/s miner joins at block index 15 | 24.82 | 78.28 |
| Ten 6.5 kH/s miners from genesis | 7.60 | 88.20 |
| 250 kH/s miner from genesis | 1.98 | 81.48 |

This supports investigating **adaptive 10→90 bootstrap** instead of a long fixed period, particularly to avoid extremely rapid early blocks with strong miners. **Not a security proof or final activation rule.** Exact genesis indexing, minimum usable samples, integer overflow and timestamps, reorg paths, miner templates and cross-platform consensus vectors must be tested in production C++ before deployment.

### Timestamp attack literature and countermeasures

See Zawy's [LWMA specification](https://github.com/zawy12/difficulty-algorithms/issues/3), [timestamp attack catalog](https://github.com/zawy12/difficulty-algorithms/issues/30), and [later recommendations](https://github.com/zawy12/difficulty-algorithms/issues/76). These document reverse/out-of-order timestamps, timewarp behavior, future-timestamp abuse, and tradeoffs in median-time-past, normalized solve intervals, and future limits.

**Recommended security work, not yet implemented:** preserve locally verified time checks, the existing 11-block median and 540-second future limit as a compatibility baseline; fuzz adversarial timestamp sequences and reorg histories against both growing and full-window LWMA. Evaluate stricter monotonic timestamps and shorter future limits as explicit alternatives **only after** demonstrating miner-template compatibility, acceptable clock-skew behavior, and no new denial-of-service or chain-split risk. Existing normalization alone should not be described as proof against all manipulation.

### Activation and reorganizations: intended invariants

- New network identity and genesis must segregate the proposed mainnet from the current development chain, whose schedule (v17/18/19 at 500/600/700) remains untouched.
- Consensus version activation must be **deterministic by ancestor height and network**, without an operator date or runtime toggle changing validation. Select the correct version from the first mineable block, including startup.
- Expected difficulty must derive only from a candidate block's **own ancestor history**, not cached current-main-chain timestamps/work; use the same function for tip-extension, block-template construction, historical verification, and alternative-chain/reorganization verification.
- Validate each branch from its common ancestor, compare accumulated valid proof-of-work (subject to existing chain-selection rules), reject invalid timestamps/PoW even if the branch advertises greater work, and test reorgs crossing the startup-to-LWMA handoff.
- Avoid consensus dependence on network fetches, pool shares, floating-point arithmetic, machine time beyond explicit timestamp-validity bounds, or platform-dependent integer overflow.
- Keep fresh-mainnet binaries isolated from the current live chain. No deployment, reset, or wallet migration until cross-platform consensus vectors, offline mining, sync-from-genesis, and reorg tests pass.

### Remaining parameters to freeze before a mainnet release

Verify source-of-truth constants and document the actual genesis block, network UUID, addresses, peer seeds, activation versions, reward/maturity and tail emission, block weight, transaction fee and timestamp rules, pool interfaces, checkpoints, hardfork voting thresholds, and recovery/migration behavior. This is a release checklist; it does not authorize changes to these parameters.


## Proposed startup retargeting and chain activation — review required

**Choice to implement and verify:** Height 1 starts with difficulty 500,000. Hold 500,000 for the first **15 mineable blocks** (exact genesis/indexing boundaries must be confirmed). Afterward, compute integer LWMA with a growing interval window `N = min(90, available predecessor intervals)` until the network accumulates 90 intervals. Enforce the **400,000 minimum** on all heights. During bootstrap only, limit each retarget to [previous_difficulty/2, previous_difficulty*2], with defined integer rounding and overflow handling; use the established LWMA 90 calculation once full history exists. The 15-block cutoff, retarget clamp, and progressive-window formula are **provisional consensus proposals**, not deployed rules.

**Preliminary startup simulation:** A 100-seed Python experiment comparing fixed 90-block warm-up with progressive retargeting estimated average block intervals over blocks 16–90:

| Constant network rate | Fixed warm-up | Progressive warm-up |
| --- | ---: | ---: |
| 2,000 H/s | 250 s | 200 s |
| 6,500 H/s | 77 s | 113 s |
| 33,500 H/s | 15 s | 95 s |
| 100,000 H/s | 5 s | 88 s |

This study uses synthetic Poisson solve times and **honest timestamps**, so it does not establish security against timestamp attacks or prove deterministic agreement with compiled consensus code. Sources and CSV are held locally as `consensus-specs/startup_prototype.py` and `startup-prototype-results.csv`.

**Timestamp threat model:** Retain the existing 11-block median-time check, 540-second future timestamp limit, timestamp normalization, and 720-second weighted solve-interval cap as candidate launch rules. Independently test backward timestamps, forward timestamp drift, alternating high/low timestamps, long stalls, invalid past/future timestamps, and chain-switch scenarios before freeze. Stronger monotonic timestamps should be assessed, not silently enabled. Background research: [Zawy's LWMA discussion](https://github.com/zawy12/difficulty-algorithms/issues/3), [Zawy's timestamp attacks](https://github.com/zawy12/difficulty-algorithms/issues/30), [BIP 94](https://github.com/bitcoin/bips/blob/master/bip-0094.mediawiki), [BIP 54](https://github.com/bitcoin/bips/blob/master/bip-0054.md). Bitcoin epoch-boundary patches cannot be copied directly to ForgeCoin's per-block LWMA.

**Activation / reorganization design:** For an explicitly new genesis/network identity, select one protocol version and one deterministic height-based difficulty schedule from the first mineable block. Every validation path—mining templates, full-block acceptance, alternative chains, historical recalculation, and replay from genesis—must compute the next difficulty solely from the candidate branch's ancestors. Use accumulated validated chain work, not block count or local wall-clock timestamps, to determine preferred chain. Never allow an alternative branch to inherit active-chain LWMA history. Reorg and median-timestamp behavior need independent cross-platform test vectors. Existing development-chain heights 500/600/700 remain unchanged and must not be imported. **No source changes, reset, or live activation are authorized by this document.**
