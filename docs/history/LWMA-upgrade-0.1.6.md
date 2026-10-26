> **Historical archive.** Original retired-chain results below are preserved for provenance; see [current mainnet specification](../CURRENT_MAINNET.md) for the selected October 26 parameters.

# ForgeCoin Desktop 0.1.6: faster difficulty adjustment

## Scheduled rules

Mainnet version 19 activates at block 700. The existing chain and balances remain valid. The version-17 500,000 floor at block 500 and version-18 1,000,000 floor at block 600 remain unchanged. From block 700, a 90-interval LWMA-style calculation replaces the legacy 720-block calculation. The two-minute target, ongoing eventual 0.2 FORGE base reward, and reward maturity remain unchanged. Every participating node must upgrade before block 700.

## Exact calculation

Use the newest 91 chronological timestamp/cumulative-work samples, including preactivation history. Do not apply the old lag or timestamp sorting. Starting with the oldest sample timestamp, normalize each subsequent timestamp to at least the preceding normalized timestamp plus one second. Cap each normalized solve interval at 720 seconds. Multiply intervals by weights 1 through 90 and sum to L; clamp L to at least 48,600. Let W be cumulative work between the first and last sample. Raw difficulty is floor(W * 120 * 91 * 99 / (200 * L)), with at least 1 before applying the 1,000,000 floor. Intermediate arithmetic is 256-bit; final difficulty is 128-bit. Invalid inputs preserve the zero/error sentinel. Non-mainnet and preactivation calculations retain their prior behavior.

This is an explicitly specified integer adaptation of the LWMA-1 design, not byte-for-byte reference code. It uses the actual first timestamp as the interval anchor, keeps full-precision cumulative work until the final division, and uses complete historical input at activation rather than a guessed fixed difficulty during warmup. Design reference: https://github.com/zawy12/difficulty-algorithms/issues/3

Version-19 mainnet timestamp validation uses the median of the most recent 11 blocks and a 540-second maximum future offset from local node time. The alternative-chain timestamp vector is reversed to chronological order before selecting those 11 blocks. Earlier versions keep their existing validation. These checks are necessary parts of the adjustment upgrade; they do not eliminate every possible timestamp attack.

The normal chain, alternative-chain difficulty, and historical recalculation all call the same height-gated calculation. Existing 735-sample collection remains intact so old history is reproducible; the new calculation selects its newest 91 samples internally.

## Comparison

Simulations compared the legacy algorithm and 60-, 90-, and 120-interval candidates. Twenty reproducible random seeds per scenario used exponential mining intervals, steady hashing, 10x increases/decreases, a 24-hour pause, and alternating hashpower. After 800 warmup blocks, 800 blocks were measured. Baseline hashpower was 100,000 H/s. Results are in LWMA-comparison.json.

| Formula | Steady difficulty coefficient of variation | First 100 block intervals after 10x increase | First 100 intervals after 10x decrease |
| --- | --- | --- | --- |
| Legacy | 0.030 | 12.0 seconds | 1,149.2 seconds |
| LWMA 60 | 0.129 | 69.0 seconds | 320.1 seconds |
| LWMA 90 | 0.103 | 51.7 seconds | 397.3 seconds |
| LWMA 120 | 0.088 | 39.3 seconds | 460.8 seconds |

90 was selected as a response/stability compromise and matches the design author's suggested window for a 120-second target. The numbers describe these synthetic scenarios, not guaranteed live performance. A sudden loss of hashpower can still cause long waits before enough new blocks arrive. A 1,000,000 floor still requires about 8,333 H/s total to achieve a 120-second expected interval.

## Validation

- Windows x64 and Linux ARM64 agree on all 1,231 consensus vectors, including 424 historical blocks, all upgrade boundaries, full-history/suffix equivalence, irregular and extreme timestamps, large work values, and unaffected networks.
- All six desktop tests passed, including wallet creation/reopening/recovery, exact amounts, Solo and XMRig compatibility, logs, pool launcher, and advertised fork heights.
- A disposable offline chain crossed heights 500, 600 and 700, reached height 717, and verified versions 16/17/18/19 and wallet scanning/mature rewards.
- A second offline test rejected old and excessive-future timestamps, rejected an alternative-chain future timestamp, and successfully reorganized onto a version-19 alternative branch.
- Offline integration mining used an explicit fixed difficulty of 1. The real difficulty calculations are exercised by the cross-platform consensus vectors. No public-network mining was performed during validation.
- The public node restarted with the same height 503, tip hash and difficulty. It advertises version 19 at height 700. Server backups: /home/ubuntu/forgecoin-upgrade-0.1.6/backup.
- Desktop 0.1.6 was installed after graceful wallet shutdown; installed sidecar hashes match tested binaries.

This is a behavioral and integration evaluation, not an independent consensus-security audit. Simulations do not model every adversarial mining strategy or propagation topology. No claim of exact two-minute blocks or exact calendar issuance is made.

Reusable core tests are in tests/forgecoin. After activation, do not roll back to software that lacks these consensus rules.

Installer SHA256: 6F07447B7F7FB9457FABFEC6814BB782CB887AA4FB6D2C88617A2B40335DDDA0

Final installed-node verification passed: synchronized to public height 503, preserved block 502 hash, and advertised version 19 at height 700.
