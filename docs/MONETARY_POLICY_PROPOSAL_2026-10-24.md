> **Historical archive — superseded for current configuration.** Original evidence and decisions below retain their original dates and network parameters. Do not use old ports, genesis, balances, token proposals or release claims as current instructions. See [current mainnet specification](CURRENT_MAINNET.md) and the current roadmap.

# Withdrawn proposal â€” 55M primary reference / 5M genesis treasury

**WITHDRAWN 2026-10-24. Do not implement or advertise as current policy.** The owner restored the original 50M reference, zero allocated premine, full PoW block subsidy and perpetual 0.20 FRG tail. See [current roadmap](../ROADMAP.md). Historical material follows.

# Proposed FRG monetary policy — 2026-10-24

**Owner decision — design target, not implemented or validated in the current consensus binary.**

- Native primary-emission accounting reference: **55,000,000 FRG**.
- Proposed **5,000,000 FRG** allocation to a transparent, security-reviewed native treasury at **genesis height 0**.
- Intended **50,000,000 FRG** remainder for primary Proof-of-Work miner issuance, subject to emission-schedule design and exact total-accounting verification.
- Retain the perpetual **0.20 FRG per block** tail subsidy to PoW miners after the primary schedule reaches its defined tail threshold.
- **55M is not a hard cap or final total supply.** The tail continues indefinitely, and circulating supply depends on unlock/vesting, lock/burn treatment and actual mining.
- Existing developer candidate binary still has a 50M emission reference and a different genesis transaction. It has **not** been modified by this documentation change; earlier genesis hashes and mining/reorg evidence do not certify the new planned genesis.
- The former zero-premine policy is superseded **for this proposed fresh chain** by a disclosed *treasury premine* of 5M FRG. There is still no proposed ICO or separate personal founder allocation. Statements of “zero premine” in historical material must not be used as descriptions of the new proposed launch.
- Treasury spendability and security are different from the prior requirement for a permanently unspendable genesis output. The spendable treasury requires separately defined multisig or equivalent custody, signing quorum, authorizations, release/lock policy, auditable accounting, and a concrete native treasury destination key.
- The treasury allocation is **not** Solana issuance. Any wrapped SPL token must be independently collateralized and redeemable with provable reserves; Solana precision and mint rights still require design.

## Consensus implementation gates

1. Decide precise 55M primary-emission *accounting and reward formula*. Do not blindly replace a constant and assume exactly 50M will be mined before tail emission, because Monero-derived emission decay, fees, genesis bookkeeping and tail onset interact.
2. Decide custody, public transparency/proofs, and whether the 5M treasury is spendable at genesis, locked by enforceable rules, or unlocks after a specified block height.
3. Create a new genesis transaction and calculate a new genesis hash and network identity; never mutate the existing development chain.
4. Repeat native PoW, emission, difficulty-transition, fork-choice/reorg, wallet/spendability, and cross-platform tests on the redesigned candidate.
5. Update the final audited whitepaper, charter and supply charts using measured release-code behavior before announcing a mainnet.

This supersedes the earlier proposed “50M primary reference plus no allocated premine” for future planning, but no deployed network or existing code has changed.
