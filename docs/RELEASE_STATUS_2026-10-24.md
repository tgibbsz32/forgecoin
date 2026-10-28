> **Current mFRG policy (October 28, 2026): Historical archive only.** The October 27 note below has itself been superseded. The current separate mFRG proposal is **500M fixed-supply target, nine treasury allocations, 50M lifetime crypto-denominated fundraising**, and **30M (6%) beneficially owned by founder** (15M immediately unlocked, 15M vesting months 13–36). See [canonical policy](MFRG_LIFETIME_TOKENOMICS_500M.md). This archived evidence must not be read as current sale terms.

> **October 27, 2026 superseding notice:** This is historical research/evidence. The current direction has **no approved fixed ten-seat governance system** and **no planned wFRG bridge**. The separately proposed 50M mFRG SPL token has **5M initial sale**, **5M post-sale liquidity/staking treasury**, and **40M future issuance/development treasury**. Governance is to be selected before the sale concludes. The current active specifications are [ROADMAP.md](../ROADMAP.md) and [miniFORGE allocation](MINIFORGE_SPL_TREASURIES.md). Do not treat earlier planning decisions here as active authorization.

> **Historical archive — superseded for current configuration.** Original evidence and decisions below retain their original dates and network parameters. Do not use old ports, genesis, balances, token proposals or release claims as current instructions. See [current mainnet specification](CURRENT_MAINNET.md) and the current roadmap.

# ForgeCoin release status and document decisions — October 24, 2026

> **Current owner direction (2026-10-24):** Restored native-only fair launch: 50M FRG primary-emission reference, no allocated premine, 100% PoW miner subsidy and perpetual 0.20 FRG/block tail. The 55M/5M genesis treasury proposal is withdrawn. Native trading and user-deposit-backed Solana interoperability are future research. See [roadmap](../ROADMAP.md).


> **Owner policy update (2026-10-24):** Confirmed owner policy: keep the candidate genesis output only if independently proved permanently unspendable; keep PoW-only 100% miner subsidy, zero ICO/founder/team premine, a 50M primary-emission reference and perpetual 0.20-FRG tail (subject to code audit); retain candidate network/difficulty values provisionally; revisit a **10-seat native FRG governance chamber** with seat allocations still unratified; keep existing development and new mainnet distinct with **no automatic balance migration**. See OWNER_POLICY_DECISIONS_2026-10-24.md.


**Status: public development-chain source plus an isolated fresh-mainnet candidate. NO RELEASE APPROVAL.**

This document records observed test evidence, distinguishes existing public-source rules from the new candidate, and identifies decisions awaiting project-owner approval. It neither activates a new chain nor alters consensus.

## Public development source vs isolated candidate

| Parameter | Existing public development-chain source | Isolated fresh candidate (not launched) |
| --- | --- | --- |
| Address prefixes | 90 / 91 / 92 | 190 / 191 / 192 |
| P2P / RPC / ZMQ ports | 19480 / 19481 / 19482 | 39480 / 39481 / 39482 (test bind ports varied) |
| Genesis nonce | 10000 | 20261020 |
| Difficulty upgrades | v17 at 500, v18 at 600, v19 LWMA90 at 700 | initial 500,000 through height 15, progressive LWMA from 16, 400,000 floor |
| Genesis transaction | Original | Same 78-byte transaction; different block nonce |

The network UUID also differs. These are not interchangeable protocols or balances. Candidate settings are proposals pending code review and approval.

## Confirmed isolated candidate test observations

- Windows x64 native RandomX candidate mined and accepted blocks through RPC height 17, including the first block after the proposed difficulty transition. Next difficulty reached the 400,000 floor.
- A second full offline two-branch native-PoW reorganization run produced `passed: true`, `source_preserved: true`, no cleanup errors. The higher-cumulative-work branch became canonical, displaced blocks remained alternatives, and restart persistence checks passed.
- 105 independently generated C++ difficulty boundary calculations at heights 90, 91 and 92 matched Python on Windows x64 and Linux x86-64. This is **not** native acceptance of mined blocks at those heights and **not** an ARM64 execution result.
- Candidate genesis has **one indexed output of 11.92092895 FRG** (1,192,092,895 atomic units), unlock time 60. No independent evidence yet proves the output permanently unspendable. A separately proposed burn-key transaction was **not** in the tested candidate.
- Mining rewards are intended for PoW miners; proposed governance bonds are **not** operational proof-of-stake, and existing election/practice services have no binding authority.

Sources: locally saved `2026-10-24/.../outputs/reorg-height17-repeat/evidence.json`, `REPRODUCE.md`, `boundary-comparison.json`, and `GENESIS_FINDINGS.md` and the height-17 isolated mining record in GitHub PR #15. GitHub PR #16 holds the isolated reorganization runner and tests. Results are not an independent code/security audit.

## Decisions required before finalizing the documents

1. **Genesis and fair launch:** Must the candidate use a demonstrably unspendable genesis output with zero allocated FRG? Or retain the current indexed output only if its permanent unspendability can be proven? Should the existing public development chain remain explicitly separate from a new mainnet?
2. **Native monetary policy:** Confirm 100% of native block subsidy to PoW miners, no ICO/premine/founder allocation, 50-million primary-emission reference (not a hard cap), and a perpetual 0.20-FRG tail reward, subject to reproducible source verification.
3. **Difficulty/network identity:** Approve or revise the candidate's address prefixes/ports/UUID/nonce, 500,000 initial difficulty, 400,000 floor, LWMA start at height 16 and 90-interval window.
4. **Governance:** Determine constituency seat counts, founder participation if any, thresholds, term lengths, election authority, conflicts and independent review. Native FRG miner bonds remain unimplemented; no quorum or binding election can be advertised.
5. **Launch treatment:** How should existing development-chain holders be told about a separate new genesis, including any lack of balance portability? No migration is implied.
6. **Deferred integrations:** A fully FRG-backed optional future Solana representation is research only; no launch or issuance commitment.

## Release gates still open

Native full-daemon acceptance through heights 90–92; ARM64 consensus equivalence; genesis output spendability/burn proof; adversarial timestamp/fork tests; reproducible final Windows and ARM64 binaries; independent security and economic review; explicit public launch plan. None can be inferred from prior x86 test vectors.

No documentation in this branch ratifies unconfirmed governance, creates treasury privileges, changes emissions, deploys Solana assets, or resets any running chain.
