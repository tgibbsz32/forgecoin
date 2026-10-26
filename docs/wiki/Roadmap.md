# ForgeCoin roadmap and acceptance gates

**Plan as of 2026-10-26.** Roadmap entries describe ForgeCoin’s committed development direction and future engineering work.

<small>Proposed future upgrades; implementation and timing are not guaranteed.</small>

 Detailed policy authority remains with [owner decisions](../OWNER_POLICY_DECISIONS_2026-10-24.md), [ROADMAP.md](../../ROADMAP.md) and consensus code validated for a *specific build*.

## Principles and economic decisions

- **Native FRG first:** privacy-focused Monero-derived L1 with CPU-oriented RandomX PoW; no Solana token or bridge at launch.
- **Fair launch target:** no founder/team/ICO premine; native miners receive **100% of block subsidy**.
- **Monetary reference:** **50,000,000 FRG primary-emission reference**, **0.20 FRG per-block perpetual tail**, eight decimal places. **No permanent hard cap** while tail emissions continue.
- **Consensus launch parameters proposed, not activated:** two-minute target, initial difficulty **500,000**, floor **400,000**, with an LWMA90 schedule/bootstrap proposal requiring independent validation. The existing development-chain hardfork schedule is **not** the new network's release authority.
- **Never migrate old development-chain balances by implication.** The old chain and fresh candidate are distinct identities; genesis output must be independently proven unspendable or replaced and retested.

## Milestone A — Freeze and validate native consensus (launch blocker)

1. Resolve genesis spendability and zero-allocation evidence; inspect emission/tail/coinbase maturity integer arithmetic.
2. Produce deterministic cross-platform native tests (Windows x64, Linux x86-64, Linux ARM64), especially blocks around the proposed LWMA transition and bootstrap window (including heights 90–92).
3. Validate timestamps, reorg/fork choice, node connectivity, wallet restore/receive/send and chain identity; publish exact source commits, build flags and reproducible binary digests.
4. Complete independent review and controlled isolated launch rehearsal; explicitly approve genesis and new network activation.

**Done when:** repeatable consensus vectors, reviewed genesis, production-quality release artifacts, independent review, signed-off launch runbook. **State:** not complete.

## Milestone B — Windows wallet and miner V1 (release blocker)

1. Build and digest-pin `forged`, `forge-wallet-rpc` and the Tauri desktop; confirm clean Windows packaging and runtime dependencies.
2. Acquire a **trusted** XMRig or reviewed source-built equivalent; resolve [issue #95](https://github.com/tgibbsz32/forgecoin/issues/95) before any execution or shipping.
3. In a separately enforced offline network, demonstrate **real solo block acceptance, maturity and wallet balance**; test stop/start/cleanup.
4. Demonstrate **actual native FRG shares** accepted and rejected correctly through a compatible *isolated* pool, plus reconnect, telemetry, allocation and authorized payout mechanics.
5. Produce sanitized evidence with exact builds and repeat tests; hold release if either Solo or Pool is unproven.

**Done when:** verified Solo **and** Pool evidence for the packaged software, including failure handling. An **official public pool is not required** for a private-compatible pool acceptance test. **State:** not complete.

## Milestone C — Explorer, website and trustworthy bootstrap

1. Distinguish existing **old-chain** explorer data from any *new* network explorer and ensure correct backend/network identity.
2. Validate lookup, pagination, confirmations, reorganization behavior, rate limits, security, backups and rollback.
3. Publish verified downloads/checksums, bootstrap-node guidance and independent network health measurements—never fabricated hashrate, users or payouts.

**Done when:** externally verified and monitored services correspond to the approved fresh network, with recovery tested. **State:** old explorer exists; fresh-network coverage pending.

## Milestone D — Optional official 1%-fee pool

1. Resolve [#28](https://github.com/tgibbsz32/forgecoin/issues/28), [#29](https://github.com/tgibbsz32/forgecoin/issues/29), [#30](https://github.com/tgibbsz32/forgecoin/issues/30) with canonical candidate work vectors, native RandomX and rejected-share tests.
2. Add authenticated/abuse-resistant Stratum service, independent job/target validation, bounded CPU/concurrency, rate limits, session replay defense and monitored operations.
3. Add *real* chain-aware share and block accounting, reorg/maturity checks, payouts, wallet security, recovery and signed operational procedures.
4. Run controlled private beta, resource tests targeting 100 concurrent workers (capacity is **unproven**), third-party review and guarded public rollout.
5. Publish precise **1% operator fee** calculation, payout thresholds, variance and transaction costs before accepting miners.

**Done when:** a miner can independently verify accepted blocks, allocations and matured payouts from an audited service. **State:** synthetic research only; public pool unavailable.

## Post-launch development direction

First integrate the user-deposit-backed Solana wFRG bridge; follow with the preferred native FCMP++/CARROT hard fork and later native swaps, private finance and L2/L3 applications. Each workstream requires its own engineering and review. Native governance bonds remain a separate governance proposal.

## Intended next-stage technology: wrapper first, FCMP++ later

After the native FRG L1 launch, prioritize a **1:1 reserve-backed Solana wFRG bridge with secure mint/burn and user redemption**. Subsequently, research an **in-place FCMP++/CARROT hard fork** on the existing chain: incrementally updated curve-tree storage, consensus proof verification, legacy wallet/output compatibility, mempool revalidation and a dedicated FCMP++ stressnet. A separate blockchain and voluntary migration mechanism would be a contingency only if an in-place fork cannot be made safe.

Longer-term planned implementations include cross-chain atomic swaps, reserve-backed synthetic stable assets, TSS/MPC-secured private block trading and optional routing fees, L2 payment/settlement, and L3 private-market applications. Their cryptography, financial controls, and execution mechanisms need independent validation; they are **not currently supported**. [Full engineering intentions](../SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md).

See [testing and release verification](Testing-and-Release.md), [current status](Current-Status.md) and [detailed implementation plan](../POOL_EXPLORER_IMPLEMENTATION_PLAN.md).
