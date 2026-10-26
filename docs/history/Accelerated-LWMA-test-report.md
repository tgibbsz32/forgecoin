> **Historical archive.** Original retired-chain results below are preserved for provenance; see [current mainnet specification](../CURRENT_MAINNET.md) for the selected October 26 parameters.

# Accelerated ForgeCoin adjustment tests

## Outcome

The deployed 90-block LWMA calculation converged toward the two-minute target in steady five- and ten-miner scenarios and after abrupt changes in hashing power. A large loss of miners remains disruptive. The 1,000,000 minimum prevents two-minute blocks if aggregate hashing power falls below about 8,333 H/s.

No live chain, wallet, activation height, difficulty parameter, or reward parameter was changed. No real mining was performed for these simulations.

## Method

Compiled the actual production forgecoin_difficulty.h and difficulty.cpp into an isolated C++ simulation executable. Each case starts with 91 synthetic chronological history entries, then runs 800 warmup blocks followed by 1,000 measured blocks. Heights start at 700 so the deployed LWMA branch is exercised. This deliberately accelerates mathematical history, not proof-of-work validation or the live chain.

Eight scenarios each have one deterministic expected-time run and 100 randomized runs: 808 runs total, 1,454,400 calculated blocks including warmup. Random runs use exponential solve times with mean difficulty / total hashes per second. Seeds 1 through 100 are reused across scenarios for comparison. Honest timestamps are integer simulated elapsed time. Miner rates change once at the measurement boundary. In the pause case the first measured interval includes 24 hours without mining.

The real 1,000,000 floor, timestamp normalization, solve-time cap, integer arithmetic, and 90-block window are all used. Simulations do not validate block hashes, transact, test networking or model adversarial timestamps. Previous offline activation/reorganization tests remain separate. These runs evaluate postactivation behavior with established history, not a proposed fresh-mainnet startup rule.

## Results

These averages combine 100 randomized trials; each miner supplies 8,000 H/s unless otherwise stated.

| Scenario | Average first 100 intervals | Average final 500 intervals |
| --- | --- | --- |
| Five steady miners | 120.1 s | 119.8 s |
| Ten steady miners | 120.1 s | 119.8 s |
| Five miners becomes ten | 91.2 s | 119.8 s |
| Ten miners becomes five | 161.8 s | 119.8 s |
| Five miners becomes 100 | 42.2 s | 119.8 s |
| 100 miners becomes five | 647.1 s (10.8 min) | 119.8 s |
| Only 1,000 H/s total | 995.5 s | 995.7 s |
| Five miners pause 24 hours then return | 978.8 s including pause | 119.8 s |

For steady five miners, the 10th-to-90th percentile range across runs' final-500-block averages was 117.1 to 122.3 seconds. This is a range of run averages, not a range of individual block intervals and not a confidence interval. Individual blocks can be much faster or slower.

## Response timing without mining luck

For a reproducible settling indicator, require the expected interval (difficulty / current hashing power) to stay within 108–132 seconds for 20 consecutive blocks. These are the completion points of that 20-block run, not the first entry into the band or a guarantee of permanent settling:

| Change | Completion block after change | Simulated elapsed time |
| --- | --- | --- |
| Five to ten miners | 109 | 2 h 47 min |
| Ten to five miners | 106 | 4 h 37 min |
| Five to 100 miners | 167 | 3 h 2 min |
| 100 to five miners | 185 | 18 h 25 min |

The earlier estimate of about 90 blocks to first get within 10% after doubling hashpower is consistent with this stricter 20-consecutive-block indicator.

## Practical implication

These tests support keeping the existing test-chain settings while gathering live observations. They do not support a guarantee of two-minute blocks during extreme miner departures. The greatest observed single gap among the 100 randomized 100-to-five trials was approximately 247 minutes; that is an observed simulation result, not a worst-case bound.

No supply increase follows from these results. At stable hashpower the issuance pace returns near its intended block-based rate. Fresh-launch starting difficulty and startup history still need a separate design and test before launch.

## Reproduction

Source: work/accelerated-lwma.cpp. Output: Accelerated-LWMA-runs.csv and Accelerated-LWMA-summary.json. Compile using C++17 and the core source's difficulty.cpp, with include paths for src, contrib/epee/include, and external/easylogging++. Run with the CSV output filename as the only argument. Runtime C++ libraries must be on PATH on Windows. Seed 0 represents deterministic intervals; seeds 1–100 use exponential intervals.
